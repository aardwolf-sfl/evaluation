import sys
import os

USAGE = 'usage: python scalability_data.py <timem | binary | plugins> <filenames...>'

assert len(sys.argv) >= 3, USAGE

COMMAND = sys.argv[1]
FILES = sys.argv[2:]

assert COMMAND in ['timem', 'binary', 'plugins'], f'invalid command; {USAGE}'
for file in FILES:
    assert os.path.isfile(file), f'file "{file}" does not exist; {USAGE}'


def _read(file):
    with open(file) as fh:
        return fh.read()


def _mean(arrays):
    return [sum(row) / len(row) for row in zip(*arrays)]


def timem(data):
    times, memories = [], []

    for item in data:
        times.append([])
        memories.append([])

        for line in item.splitlines():
            pair = line.split(' ; ')
            times[-1].append(float(pair[0].replace(' s', '')))
            memories[-1].append(int(pair[1].replace(' kB', '')))

    times = _mean(times)
    memories = _mean(memories)

    csv = 'Time [s],Peak memory usage [kB]\n'

    for time, memory in zip(times, memories):
        csv += f'{time},{memory}\n'

    return csv


def binary(data):
    names, sizes = [], []

    for item in data:
        names.clear()
        sizes.append([])

        for line in item.splitlines():
            pair = line.split('\t')
            names.append(pair[1])
            sizes[-1].append(int(pair[0]))

    sizes = _mean(sizes)

    csv = 'File,Binary size [B]\n'

    for name, size in zip(names, sizes):
        csv += f'{name},{size}\n'

    return csv


def plugins(data):
    names, times = [], []

    for item in data:
        names.clear()
        times.append([])

        for line in item.splitlines():
            pair = line.split('\t')
            if len(pair) != 2:
                continue

            names.append(pair[0])
            times[-1].append(float(pair[1]))

    times = _mean(times)

    csv = 'Plugin,Time [s]\n'

    for name, time in zip(names, times):
        csv += f'{name},{time}\n'

    return csv


commands = ({'timem': timem, 'binary': binary, 'plugins': plugins})
output = commands[COMMAND]([_read(file) for file in FILES])
print(output)
