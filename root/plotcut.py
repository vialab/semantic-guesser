#!/usr/bin/env python
from argparse import ArgumentParser
from grammar  import Grammar
from tree.abstract import DepthFirstIterator

import seaborn as sns
import pandas  as pd
import numpy   as np
import matplotlib.pyplot as plt

import math

def options():
    parser = ArgumentParser()
    parser.add_argument('grammars', nargs='+', help="the grammar path")
    parser.add_argument('--aggregate', action='store_true',
        help="plot mean depth curve and a band representing min/max")
    return parser.parse_args()


def smooth(x,window_len=11,window='hanning'):
    """smooth the data using a window with requested size.
    see http://scipy-cookbook.readthedocs.io/items/SignalSmooth.html
    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."

    if window_len < 3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', \
        'bartlett', 'blackman'"

    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]

    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    return y


def depth_curve(grammar):
    tree = grammar.noun_treecut.tree

    # update depth attribute (for backwards compatibility)
    for depth, node in DepthFirstIterator(tree.root):
        node.depth = depth

    depth = []
    for node in grammar.noun_treecut:
        nLeaves = node.leafCount()
        d = node.depth
        depth.extend([d] * max(nLeaves, 1))

    return depth


def plot_many(grammars, fig=None, ax=None, show=False):

    depths = []

    for grammar in grammars:
        depth = depth_curve(grammar)
        depths.append(depth)

    depths = np.array(depths).transpose()
    max_depth  = smooth(np.amax(depths, 1), 1000)
    min_depth  = smooth(np.amin(depths, 1), 1000)
    mean_depth = smooth(np.mean(depths, 1), 1000)

    fig, ax = plt.subplots()
    plt.gca().invert_yaxis()

    ax.plot(mean_depth, '-', lw=1)
    ax.fill_between(range(len(mean_depth)), min_depth, max_depth)

    plt.show()


def plot(grammar, fig=None, ax=None, show=False):
    depth = depth_curve(grammar)

    smooth_depth = smooth(np.array(depth), 1000)

    if not ax:
        fig, ax = plt.subplots()
        plt.gca().invert_yaxis()

    ax.plot(smooth_depth, '-', lw=1)

    if show: plt.show()

    return fig, ax


if __name__ == '__main__':
    opts = options()

    n = len(opts.grammars)

    if opts.aggregate:
        grammars = []
        for i in range(0, n):
            g = Grammar.from_files(opts.grammars[i])
            grammars.append(g)

        plot_many(grammars)
    else:
        g0 = Grammar.from_files(opts.grammars[0])
        fig, ax = plot(g0, show=n==1)

        for i in range(1, n):
            g_i = Grammar.from_files(opts.grammars[i])
            fig, ax = plot(g_i, fig, ax, show=i==n-1)
