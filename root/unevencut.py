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
    tree.trim(threshold)

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

    # forming the cut file name
    filename = "{}-{}".format(args.pos, args.algorithm)
    if args.algorithm == 'wagner':
        filename += '-{}'.format(args.weighting)
    if args.samplesize:
        filename += '-{}'.format(args.samplesize)
    if args.commit:
        filename += '-{}'.format(args.commit)

    cut_file_path = "{}cut-{}.txt".format(args.file, filename)
    tree_file_path = "{}tree-{}.json".format(args.tree, filename) if args.tree else None

    main(args.pos, cutter, cut_file_path, args.samplesize, tree_file_path, args.threshold)