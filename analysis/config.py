import os

params = {
    'figures.root': os.path.dirname(os.path.realpath(__file__)),
    'figures.ext': 'pgf',
    'results.effectiveness': os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'results_effectiveness'),
    'results.scalability': os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'results_scalability')
}
