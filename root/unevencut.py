#!/usr/bin/env python

"""This script finds the WordNet uneven cut appropriate for
the frequencies computed from the passwords. 

Created on 2013-03-29

@author: rafa
"""

import cut
import semantics
from argparse import ArgumentParser


DEFAULT_FILE = '../results/cut/cut.txt'


def main(pwsetid, pos, cutter, cut_file, samplesize, tree_file, threshold):
    
    tree = semantics.load_semantictree(pos, pwsetid, samplesize)
    cut_ = cutter.findcut(tree)
    tree.trim(threshold)  # trimming the 0 frequency nodes by default!!!

    if cut_file:    
        output = open(cut_file, 'wb')
        output.write(str([node.id for node in cut_]))
        output.close()
    else:
        print str(cut_)
        
    if tree_file:
        output = open(tree_file, 'wb')
        output.write(tree.toJSON())
        output.close()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('pos', help='part-of-speech')
    parser.add_argument('pwsetid', help='ID of the password set')
    parser.add_argument('file', help='directory path for the output file')
    parser.add_argument('-s', '--samplesize', type=int, help='if this argument is not '
                                                             'passed, runs over the entire database')
    parser.add_argument('-t', '--tree', help='if a directory path is provided,'
                                             ' the populated tree will be ouput to the informed file')
    parser.add_argument('-o', '--threshold', default=0, type=int, help='nodes with value <= threshold are removed')
    parser.add_argument('-a', '--algorithm', default='li_abe', choices=['li_abe', 'wagner'])
    parser.add_argument('-w', '--weighting', default=50, type=int, help="weighting factor for Wagner's algorithm")
    parser.add_argument('-c', '--commit', default=None, help="if the commit key is informed, the output"
                                                             " file will feature it")

    args = parser.parse_args()

    algorithm = args.algorithm

    if algorithm == 'li_abe':
        cutter = cut.li_abe
    else:
        cut.wagner.default_c = args.weighting
        cutter = cut.wagner

    # forming the cut and tree file names
    cut_filepath = "cut-{}-{}-{}".format(args.pwsetid, args.pos, args.algorithm)
    tree_filepath = "tree-{}-{}".format(args.pwsetid, args.pos)

    if args.algorithm == 'wagner':
        cut_filepath += '-{}'.format(args.weighting)

    cut_filepath += '-{}'.format(args.threshold)
    tree_filepath += '-{}'.format(args.threshold)

    if args.samplesize:
        cut_filepath += '-{}'.format(args.samplesize)
        tree_filepath += '-{}'.format(args.samplesize)

    if args.commit:
        cut_filepath += '-{}'.format(args.commit)
        tree_filepath += '-{}'.format(args.commit)

    cut_filepath = args.file + cut_filepath + '.txt'
    tree_filepath = args.tree + tree_filepath + '.json' if args.tree else None

    main(args.pwsetid, args.pos, cutter, cut_filepath, args.samplesize, tree_filepath, args.threshold)
