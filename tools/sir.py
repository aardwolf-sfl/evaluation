import sys
import os
import io
import shutil
import distutils.dir_util as dir_util
import glob
import time
import subprocess
import difflib
import json
import csv

STARTED = time.time()
DATA_DIR = os.path.realpath('data')

# Enables parallel evaluation.
if 'DATA_DIR_ID' in os.environ:
    DATA_DIR = os.path.join(DATA_DIR, os.environ['DATA_DIR_ID'])


def _elapsed():
    return '{:06.3f}'.format(time.time() - STARTED)


def _info(message):
    print(f'[{_elapsed()}] info: {message}')


# python sir.py prepare path/to/program/archive.tar.gz [test_count_limit]
def prepare(args, user=False):
    _info(f'clean "{DATA_DIR}"')
    _make_fresh_dir(DATA_DIR)

    archive_path = os.path.realpath(args[0])
    assert os.path.isfile(archive_path), f'archive "{archive_path}" not found'
    _info(f'extract "{archive_path}" into "{DATA_DIR}"')
    shutil.unpack_archive(archive_path, DATA_DIR)

    program_name = os.listdir(DATA_DIR)[0]
    assert program_name is not None, 'extracting the archive failed'

    sources_dir = os.path.join(
        DATA_DIR, program_name, 'source.alt', 'source.orig')
    assert os.path.isdir(sources_dir), 'sources directory not found'
    playground_dir = os.path.join(DATA_DIR, program_name, 'source')
    assert os.path.isdir(playground_dir), 'playground directory not found'

    _info(f'copy sources from {sources_dir} to {playground_dir}')
    dir_util.copy_tree(sources_dir, playground_dir)

    healthy_file = os.path.join(playground_dir, 'healthy.c')
    source_filename = os.path.basename(
        glob.glob(os.path.join(sources_dir, '*.c'))[0])
    source_file = os.path.join(playground_dir, source_filename)
    assert os.path.isfile(source_file), 'source file not found'

    _info(f'rename {source_file} to {healthy_file}')
    os.rename(source_file, healthy_file)

    _info('compile healthy file')
    compile(['exe', healthy_file, '-o', 'healthy', '-lm'], cwd=playground_dir)

    inputs_path = os.path.join(DATA_DIR, program_name, 'inputs')
    assert os.path.isdir(inputs_path), 'inputs directory not found'

    _info(f'copy inputs from {inputs_path} to {playground_dir}')
    dir_util.copy_tree(inputs_path, playground_dir)

    universe_file = os.path.join(
        DATA_DIR, program_name, 'testplans.alt', 'universe')
    assert os.path.isfile(universe_file), 'universe file not found'

    if len(args) > 1:
        limit = int(args[1])
        _info(f'generate test runner from {universe_file} with limit {limit}')
        test_runner = generate_test_runner(universe_file, limit=limit)
    else:
        _info(f'generate test runner from {universe_file}')
        test_runner = generate_test_runner(universe_file)

    test_runner_file = os.path.join(playground_dir, 'test_runner.c')

    _info(f'write test runner to {test_runner_file}')
    _write(test_runner_file, test_runner)

    _info('getting healthy outputs')
    for test, args in enumerate(filter(lambda line: line != '', _read(universe_file).split('\n'))):
        command = f'./healthy {args} > healthy.{test + 1}.out'
        subprocess.run(command, cwd=playground_dir, shell=True)

    existing_labels_file = archive_path.replace('.tar.gz', '.json')
    if os.path.isfile(existing_labels_file):
        labels_file = os.path.join(
            DATA_DIR, program_name, 'info', 'labels.json')
        _info(f'copy labels from {existing_labels_file} to {labels_file}')
        shutil.copy(existing_labels_file, labels_file)
    else:
        _info(f'labels file {existing_labels_file} does not exist')

    sir_file = os.path.join(playground_dir, 'sir.py')

    _info(f'copy itself to {sir_file}')
    shutil.copy(sys.argv[0], sir_file)


# python sir.py run version_id
def run(args, user=False):
    assert os.path.isdir(DATA_DIR), 'run sir.py prepare before sir.py run'

    program_name = os.listdir(DATA_DIR)[0]
    assert program_name is not None, 'sir.py prepare probably failed'

    playground_dir = os.path.join(DATA_DIR, program_name, 'source')
    assert os.path.isdir(playground_dir), 'playground directory not found'

    healthy_file = os.path.join(playground_dir, 'healthy.c')
    assert os.path.isfile(healthy_file), 'healthy source file not found'

    version = args[0]

    version_dir = os.path.join(
        DATA_DIR, program_name, 'versions.alt', 'versions.orig', version)
    assert os.path.isdir(version_dir), 'invalid version'

    _info(f'copy sources from {version_dir} to {playground_dir}')
    dir_util.copy_tree(version_dir, playground_dir)

    buggy_file = os.path.join(playground_dir, 'buggy.c')
    source_filename = os.path.basename(
        glob.glob(os.path.join(version_dir, '*.c'))[0])
    source_file = os.path.join(playground_dir, source_filename)
    assert os.path.isfile(source_file), 'source file not found'

    _info(f'rename {source_file} to {buggy_file}')
    os.rename(source_file, buggy_file)

    labels_file = os.path.join(DATA_DIR, program_name, 'info', 'labels.json')

    if os.path.isfile(labels_file):
        _info('labels file exists and will be used')
        machine_friendly = json.loads(_read(labels_file))

        _, human_friendly = get_buggy_lines(healthy_file, buggy_file, version)

        _info('display human friendly diff')
        print(human_friendly)
    else:
        _info('labels file does not exist so it will be determined automatically')

        _info('determine buggy lines')
        machine_friendly, human_friendly = get_buggy_lines(
            healthy_file, buggy_file, version)

        _info(f'write results in json into {labels_file}')
        _write(labels_file, json.dumps(machine_friendly))

        _info('display human friendly diff')
        print(human_friendly)

    bin_dir = os.path.join('/mnt', 'aardwolf')
    assert os.path.isdir(bin_dir), 'directory with Aardwolf binaries not found'

    aardwolf_file = os.path.join(playground_dir, '.aardwolf.yml')
    aardwolf_config = ''.join([_read('sir.yml'), _read('plugins.yml')])

    _info(f'copy .aardwolf.yml with specified plugins.yml to {aardwolf_file}')
    _write(aardwolf_file, aardwolf_config)

    def _prepend_bin(filename):
        return os.path.join(bin_dir, filename)

    stdout_file = os.path.join(playground_dir, 'stdout.txt')
    stderr_file = os.path.join(playground_dir, 'stderr.txt')

    stdout_fd = open(stdout_file, 'w')
    stderr_fd = open(stderr_file, 'w')


    command = os.path.join(bin_dir, 'aardwolf --ui json')
    _info(f'run Aardwolf using: `{command}`')
    subprocess.run(command, cwd=playground_dir, shell=True,
                   check=True, stdout=stdout_fd, stderr=stderr_fd)

    stdout_fd.close()
    stderr_fd.close()

    results_json = _read(stdout_file)
    results = json.loads(results_json)

    _info('evaluate')
    evaluated = evaluate(results, machine_friendly[version])

    if user:
        _output(_format_scores(evaluated))

    _output_raw(version, _format_scores(evaluated), results_json, playground_dir)

    return evaluated


# python sir.py runall [ignored_versions...]
def runall(args, user=False):
    assert os.path.isdir(DATA_DIR), 'run sir.py prepare before sir.py run'

    program_name = os.listdir(DATA_DIR)[0]
    assert program_name is not None, 'sir.py prepare probably failed'

    versions_dir = os.path.join(
        DATA_DIR, program_name, 'versions.alt', 'versions.orig')
    assert os.path.isdir(versions_dir), 'versions directory not found'

    metrics = ['EXAM best', 'EXAM worst', 'hit@5 best',
               'hit@5 worst', 'hit@10 best', 'hit@10 worst']
    plugins = {}

    for version in os.listdir(versions_dir):
        # Ignore specified version
        if version in args:
            continue

        if os.path.isdir(os.path.join(versions_dir, version)):
            for plugin, result in run([version]).items():
                if plugin not in plugins:
                    plugins[plugin] = []

                version_result = {'version': version}
                for metric in metrics:
                    version_result[metric] = result[metric]

                plugins[plugin].append(version_result)

    for plugin in plugins:
        total_result = dict([('version', 'avg')] + [(metric, 0)
                                                    for metric in metrics])

        for result in plugins[plugin]:
            for metric in metrics:
                total_result[metric] += result[metric]

        for metric in metrics:
            total_result[metric] /= len(plugins[plugin])

        plugins[plugin].append(total_result)

    if user:
        stream = io.StringIO()
        writer = csv.DictWriter(stream, ['plugin', 'version'] + metrics)

        writer.writeheader()

        for plugin in plugins:
            for result in plugins[plugin]:
                row = dict([('plugin', plugin)] + list(result.items()))
                writer.writerow(row)

        formatted = stream.getvalue()
        stream.close()

        _output(formatted)

    return plugins


# python sir.py out_dir
def label(args, user=False):
    assert os.path.isdir(DATA_DIR), 'run sir.py prepare before sir.py run'

    program_name = os.listdir(DATA_DIR)[0]
    assert program_name is not None, 'sir.py prepare probably failed'

    sources_dir = os.path.join(
        DATA_DIR, program_name, 'source.alt', 'source.orig')
    assert os.path.isdir(sources_dir), 'sources directory not found'

    healthy_file = glob.glob(os.path.join(sources_dir, '*.c'))[0]
    assert os.path.isfile(healthy_file), 'source file not found'

    versions_dir = os.path.join(
        DATA_DIR, program_name, 'versions.alt', 'versions.orig')
    assert os.path.isdir(versions_dir), 'versions directory not found'

    def _is_version(dir_item):
        return os.path.isdir(os.path.join(versions_dir, dir_item))

    labels = {}
    for version in sorted(filter(_is_version, os.listdir(versions_dir)), key=lambda x: int(x[1:])):
        version_dir = os.path.join(versions_dir, version)

        _info(f'label version {version}')

        buggy_file = glob.glob(os.path.join(version_dir, '*.c'))[0]
        assert os.path.isfile(buggy_file), 'buggy file not found'

        _, human_friendly = get_buggy_lines(healthy_file, buggy_file, version)
        print(human_friendly)

        version_labels = []

        raw = input('buggy lines: ')

        if raw == 'q':
            break

        for lines in [x.split('-') for x in raw.split(',')]:
            if len(lines) == 1:
                if lines[0] == "":
                    break

                line_begin = int(lines[0])
                line_end = int(lines[0])
            elif len(lines) == 2:
                line_begin = int(lines[0])
                line_end = int(lines[1])
            else:
                raise Exception('invalid input')

            version_labels.append(
                {'line_begin': line_begin, 'line_end': line_end})

        labels[version] = version_labels

    labels_file = os.path.realpath(args[0])

    _info(f'write results to {labels_file}')
    _write(labels_file, json.dumps(labels))

    return labels


# python sir.py compile unit_type [compiler_args...]
def compile(args, cwd=None, user=False):
    unit_type = args[0]
    compiler_args = args[1:]

    unit_types = ['ir', 'obj', 'exe']
    assert unit_type in unit_types, f'invalid unit type "{unit_type}", use one of: {", ".join(unit_types)}'

    unit_flags = ''

    if unit_type == 'ir':
        unit_flags = '-c -emit-llvm'
    elif unit_type == 'obj':
        unit_flags = '-c -emit-llvm'
    elif unit_type == 'exe':
        unit_flags = ''

    command = f'clang -g -O0 {unit_flags} -Wno-return-type -std=c89 {" ".join(compiler_args)}'

    _info(f'compile using: `{command}`')
    subprocess.run(command, cwd=cwd, shell=True, check=True)


# python sir.py diff version
def diff(args, user=False):
    assert os.path.isdir(DATA_DIR), 'run sir.py prepare before sir.py run'

    program_name = os.listdir(DATA_DIR)[0]
    assert program_name is not None, 'sir.py prepare probably failed'

    playground_dir = os.path.join(DATA_DIR, program_name, 'source')
    assert os.path.isdir(playground_dir), 'playground directory not found'

    healthy_file = os.path.join(playground_dir, 'healthy.c')
    assert os.path.isfile(healthy_file), 'healthy source file not found'

    version = args[0]

    version_dir = os.path.join(
        DATA_DIR, program_name, 'versions.alt', 'versions.orig', version)
    assert os.path.isdir(version_dir), 'invalid version'

    _info(f'copy sources from {version_dir} to {playground_dir}')
    dir_util.copy_tree(version_dir, playground_dir)

    buggy_file = os.path.join(playground_dir, 'buggy.c')
    source_filename = os.path.basename(
        glob.glob(os.path.join(version_dir, '*.c'))[0])
    source_file = os.path.join(playground_dir, source_filename)
    assert os.path.isfile(source_file), 'source file not found'

    _info(f'rename {source_file} to {buggy_file}')
    os.rename(source_file, buggy_file)

    _, human_friendly = get_buggy_lines(healthy_file, buggy_file, version)
    print(human_friendly)


def generate_test_runner(universe, limit=None):
    prolog = '''
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <sys/wait.h>

int run(const char* command)
{
    int status = system(command);
    if (WIFSIGNALED(status) && (WTERMSIG(status) == SIGINT || WTERMSIG(status) == SIGQUIT)) {
        exit(1);
    }
    return status / 256;
}

int diff(const char *first, const char *second)
{
    #define BUFFER_SIZE 64

    FILE *first_fd = fopen(first, "rb");
    FILE *second_fd = fopen(second, "rb");

    #define RETURN(result) fclose(first_fd); fclose(second_fd); return result

    char first_out[BUFFER_SIZE];
    char second_out[BUFFER_SIZE];

    while (!feof(first_fd) && !feof(second_fd)) {
        size_t first_bytes = fread(&first_out, 1, BUFFER_SIZE, first_fd);
        size_t second_bytes = fread(&second_out, 1, BUFFER_SIZE, second_fd);

        if (first_bytes != second_bytes) {
            RETURN(1);
            return 1;
        }

        if (memcmp(first_out, second_out, first_bytes) != 0) {
            RETURN(1);
            return 1;
        }
    }

    if (feof(first_fd) == feof(second_fd)) {
        RETURN(0);
    } else {
        RETURN(1);
    }
}

int main()
{
    int result;
'''

    epilog = '''
    return 0;
}

'''

    tests = []

    with open(universe) as f:
        for test, line in enumerate(f):
            args = line.strip().replace('\\', '\\\\').replace('"', '\\"')
            tests.append(f'''
    aardwolf_write_external("Test #{test + 1}");
    run("./buggy {args} > buggy.out");
    result = diff("healthy.{test + 1}.out", "buggy.out");
    if (result == 0) {{ printf("PASS: Test #{test + 1}\\n"); }} else {{ printf("FAIL: Test #{test + 1}\\n"); }}
''')
            if limit is not None and test >= limit:
                break

    code = prolog + os.linesep.join(tests) + epilog
    return code


def get_buggy_lines(healthy, buggy, version):
    # TODO: Remove whitespace character in all lines (to suppress indentation changes).

    with open(healthy, errors='ignore') as fd:
        healthy_lines = fd.readlines()

    with open(buggy, errors='ignore') as fd:
        buggy_lines = fd.readlines()

    matcher = difflib.SequenceMatcher(None, buggy_lines, healthy_lines)
    labels = []

    for tag, i1, i2, _, _ in matcher.get_opcodes():
        if tag != 'equal':
            labels.append({'type': tag, 'line_begin': i1, 'line_end': i2})

    machine_friendly = {version: labels}

    diff = difflib.unified_diff(
        buggy_lines, healthy_lines, fromfile='buggy.c', tofile='healthy.c')
    human_friendly = ''.join(diff)

    return machine_friendly, human_friendly


def evaluate(results, buggy_lines):
    evaluated = {}
    # n_total = results['statements_count']
    n_executed = results['executed_statements_count']

    for plugin in results['plugins']:
        name = plugin['name']

        n_best = -1
        n_worst = -1

        idx = 0
        while idx < len(plugin['results']):
            item = plugin['results'][idx]

            # Best-case strategy: Any one defective statement needs to be localized to understand and repair the defect.
            found = False
            for buggy in buggy_lines:
                # Is located statement inside a buggy region?
                begin = buggy['line_begin'] >= item['location']['line_begin']
                end = buggy['line_end'] <= item['location']['line_end']
                if begin and end:
                    found = True
                    break

            if found:
                score = item['suspiciousness']

                # Find lower bound
                idx -= 1
                while idx > 0 and plugin['results'][idx]['suspiciousness'] == score:
                    idx -= 1

                n_best = idx + 1

                # Find upper bound
                idx += 2
                while idx < len(plugin['results']) and plugin['results'][idx]['suspiciousness'] == score:
                    idx += 1

                n_worst = idx - 1
                break

            idx += 1

        n_best += 1
        n_worst += 1

        if n_best == 0:
            # If the technique failed, set the worst possible results
            n_best = n_executed
            n_worst = n_executed

        evaluated[name] = {
            'best': n_best,
            'worst': n_worst,
            'EXAM best': n_best / n_executed,
            'EXAM worst': n_worst / n_executed,
            'hit@5 best': 1 if n_best <= 5 else 0,
            'hit@5 worst': 1 if n_worst <= 5 else 0,
            'hit@10 best': 1 if n_best <= 10 else 0,
            'hit@10 worst': 1 if n_worst <= 10 else 0,
        }

    return evaluated


def _make_fresh_dir(path):
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path)


def _write(path, content):
    with open(path, 'w') as fd:
        print(content, file=fd)


def _read(path):
    with open(path) as fd:
        return fd.read()


def _format_scores(items, ignore=[]):
    metrics = list(filter(lambda metric: metric not in ignore,
                          next(iter(items.values()), {}).keys()))

    output = 'plugin,' + ','.join(metrics) + os.linesep

    for plugin, results in items.items():
        output += plugin + ',' + \
            ','.join(map(lambda metric: str(
                results[metric]), metrics)) + os.linesep

    return output


def _output(content):
    dest = os.environ.get('RESULTS_FILE')
    if dest is None:
        print(content)
    else:
        _write(dest, content)


def _output_raw(version, results, results_json, playground_dir):
    dest = os.environ.get('RAW_RESULTS_DIR')
    if dest is not None:
        dest = os.path.join(dest, version)
        _make_fresh_dir(dest)

        _write(os.path.join(dest, 'results.csv'), results)
        _write(os.path.join(dest, 'results.json'), results_json)
        dir_util.copy_tree(os.path.join(playground_dir, '.aardwolf'), dest)
        shutil.copy(os.path.join(playground_dir, '.aardwolf.yml'), dest)


def main():
    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        'prepare': prepare,
        'run': run,
        'runall': runall,
        'label': label,
        'compile': compile,
        'diff': diff,
    }

    if command in commands:
        commands[command](args, user=True)
    else:
        print(
            f'Unknown command "{command}". Use one of: {", ".join(commands.keys())}.')
        sys.exit(1)


main()
