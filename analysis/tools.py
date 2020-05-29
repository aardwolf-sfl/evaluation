import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from export import save


# Creates function which maps input array to density representing what fraction
# of given values is less than or equal to element from the array.
def make_density(values):
    values = np.array(values)
    return np.vectorize(lambda x: np.count_nonzero(values <= x) / len(values))


# Makes given array a smooth line.
def smooth(y, sigma=None):
    if sigma is None:
        sigma = np.ceil(np.log10(len(y)))

    first, last = y[0], y[-1]
    y = gaussian_filter1d(y, sigma=sigma)
    y[0], y[-1] = first, last

    return y


def to_percent(ax, axis):
    assert axis in ['x', 'y']
    labels_attr = f'set_{axis}ticklabels'
    ticks_attr = f'get_{axis}ticks'

    ticks = getattr(ax, ticks_attr)()
    percent_ticks = [f'{int(tick * 100)}\\%' for tick in ticks]
    getattr(ax, labels_attr)(percent_ticks)


def fake_handle(color='black', linestyle=None, marker=None):
    kwargs = {'color': color}
    if linestyle is not None:
        kwargs['linewidth'] = 4
        kwargs['linestyle'] = linestyle
        kwargs['fillstyle'] = 'left'
    else:
        kwargs['linewidth'] = 0

    if marker is not None:
        kwargs['markersize'] = 4
        kwargs['marker'] = marker

    if linestyle is None and marker is None:
        return Patch(color=color)

    return Line2D([0], [0], **kwargs)


class Figure:
    def _render(self):
        raise Exception('not implemented')

    def show(self):
        fig = self._render()
        plt.show(fig)
        return self

    def save(self, name):
        fig = self._render()
        save(fig, name)
        return self


class Table:
    def _build(self):
        raise Exception('not implemented')

    def show(self):
        tab = self._build()
        display(tab)
        return self

    def to_latex(self):
        latex_params = {'index': False}
        if hasattr(self, 'latex_params'):
            latex_params.update(self.latex_params)

        tab = self._build()
        print(tab.to_latex(**latex_params))
        return self
