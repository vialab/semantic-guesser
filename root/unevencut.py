"""This script finds the WordNet uneven cut appropiate for
the frequencies computed from the passwords. 

Created on 2013-03-29

@author: rafa
"""

from tree.wordnet import WordNetTree
import cut
from argparse import ArgumentParser
from database import PwdDb
import semantics

DEFAULT_FILE = '../results/cut/cut.txt'


def populate(tree, pos, samplesize):
    
    db = PwdDb(size=samplesize)
    
    while db.hasNext():
        words = db.nextPwd()  # list of Fragment
        
        for w in words:
            # we don't want dynamic dict. entries
            if w.is_gap():
                continue

            # best effort to get a synset matching the fragment's pos
            synset = semantics.synset(w)    
            
            # check if the synset returned has the pos we want
            if synset is not None and synset.pos == pos:
                tree.insert_synset(synset)
                
    return tree


def main(pos, cutter, cut_file, samplesize, tree_file, threshold):
    
    tree = WordNetTree(pos)
    tree = populate(tree, pos, samplesize)
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
    parser.add_argument('-f', '--file', help='directory path for the output file')
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
    cut_filepath = "cut-{}-{}".format(args.pos, args.algorithm)
    tree_filepath = "tree-{}".format(args.pos)

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

    main(args.pos, cutter, cut_filepath, args.samplesize, tree_filepath, args.threshold)