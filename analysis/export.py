import os
from math import sqrt

import matplotlib as mpl
import matplotlib.pyplot as plt

from config import params


def update_mpl():
    plt.style.use('bmh')
    params = {
        # fonts
        'font.family': 'lmodern',
        'text.usetex': True,
        'text.latex.preamble': [r'\usepackage{lmodern}'],
        'font.size': 10,
        'axes.labelsize': 10,
        'legend.fontsize': 7,
        'xtick.labelsize': 7,
        'ytick.labelsize': 7,
        # sizes
        'lines.linewidth': 1,
        'lines.markersize': 2,
        'axes.linewidth': 0.6,
        # colors
        'axes.facecolor': '#ffffff',
        'figure.facecolor': '#ffffff'
    }
    mpl.rcParams.update(params)


# http://scipy-cookbook.readthedocs.io/items/Matplotlib_LaTeX_Examples.html
# https://python4astronomers.github.io/plotting/advanced.html
TEXT_WIDTH_PT = 369
WIDTH = 1 / 72.27 * TEXT_WIDTH_PT
DEFAULT_HEIGHT = (sqrt(5) - 1) / 2

DPI = 300


def figsize(width, height=DEFAULT_HEIGHT):
    fig_width = width * WIDTH
    fig_height = height * fig_width

    return (fig_width, fig_height)


def save(fig, name):
    # If an extension is specified, we ignore it.
    name, _ = os.path.splitext(name)
    name += '.' + params['figures.ext']

    fig.savefig(os.path.join(params['figures.root'], name),
                facecolor=fig.get_facecolor(), bbox_inches='tight', dpi=DPI)
    plt.close(fig)
