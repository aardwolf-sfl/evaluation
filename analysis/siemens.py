import os
import json
import pandas as pd

from config import params


class Version:
    def __init__(self, program, version):
        self.program_ = program
        self.version_ = version
        self.dir_ = os.path.realpath(os.path.join(
            params['results.effectiveness'], program, version))
        assert os.path.isdir(self.dir_), 'version not found'

    def config(self):
        with self._file('.aardwolf.yml') as fh:
            return fh.read()

    def log(self):
        with self._file('aard.log') as fh:
            return fh.read()

    def tests(self):
        with self._file('aard.result') as fh:
            results = []
            for line in fh.readlines():
                if line != '':
                    split = line.split(': ')
                    results.append((split[1].strip(), split[0] == 'PASS'))

            return results

    def results(self):
        return pd.read_csv(os.path.join(self.dir_, 'results.csv'))

    def n_statements(self):
        return int(self._json()['statements_count'])

    def _file(self, filename):
        return open(os.path.join(self.dir_, filename))

    def _json(self):
        with self._file('results.json') as fh:
            return json.load(fh)

    def __str__(self):
        return f'{self.program_}[{self.version_}]'

    def __repr__(self):
        return str(self)


def all_versions():
    data = dict()

    data['printtokens_2.0'] = ['v1', 'v2', 'v3', 'v5', 'v7']

    data['printtokens2_2.0'] = ['v1', 'v2', 'v3', 'v4', 'v5',
                                'v6', 'v7', 'v8', 'v9']

    data['replace_2.1'] = ['v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v9',
                           'v10', 'v11', 'v12', 'v13', 'v14', 'v15', 'v17',
                           'v18', 'v19', 'v20', 'v21', 'v22', 'v23', 'v24',
                           'v25', 'v26', 'v27', 'v28', 'v29', 'v30', 'v31']

    data['schedule_2.0'] = ['v2', 'v3', 'v4', 'v5', 'v7', 'v8']

    data['schedule2_2.0'] = ['v1', 'v2', 'v3', 'v4', 'v5',
                             'v6', 'v7', 'v8', 'v10']

    data['tcas_2.0'] = ['v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10',
                        'v11', 'v12', 'v13', 'v14', 'v15', 'v16', 'v17', 'v18', 'v19',
                        'v20', 'v21', 'v22', 'v23', 'v24', 'v25', 'v26', 'v27', 'v28',
                        'v29', 'v30', 'v31', 'v32', 'v33', 'v34', 'v35', 'v36', 'v37',
                        'v39', 'v40', 'v41']

    data['totinfo_2.0'] = ['v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10',
                           'v11', 'v12', 'v13', 'v14', 'v15', 'v16', 'v17', 'v18',
                           'v19', 'v20', 'v21', 'v22', 'v23']

    for program, versions in data.items():
        for version in versions:
            yield Version(program, version)
