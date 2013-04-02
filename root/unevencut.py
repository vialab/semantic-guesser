'''This script finds the WordNet uneven cut appropiate for
the frequencies computed from the passwords. 

Created on 2013-03-29

@author: rafa
'''

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
            if synset is not None and synset.pos==pos:
                tree.insert_synset(synset)
                
    return tree

def main(pos, cut_file, samplesize, tree_file, threshold):
    
    tree = WordNetTree(pos)
    tree = populate(tree, pos, samplesize)
    tree.trim(threshold)
    cut_ = cut.findcut(tree)
    
    if cut_file:    
        output = open(cut_file, 'wb')
        output.write(str(cut_))
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
    parser.add_argument('-f','--file', help='complete path of the output file')
    parser.add_argument('-s', '--samplesize', type=int, help='if this argument is not passed, runs over the entire database')
    parser.add_argument('-t', '--tree', help='if a path is provided, the populated tree will be ouput to the informed file')
    parser.add_argument('-o', '--threshold', default=0, type=int, help='nodes with value <= threshold are removed')
    
    args = parser.parse_args()
    
    main(args.pos, args.file, args.samplesize, args.tree, args.threshold)

# this is populate for a frequency distribution of words,
# suitable for reading from a file
# def populate(tree, dist, pos):
#     for word, freq in dist.items():
#         synset = semantics.synset(word)
#         
#         # check if the synset returned has the pos we want
#         if synset is not None and synset.pos==pos:
#             insert(tree, synset, freq)
#             
#     return tree


# def freq_dist_from_file(f):
#     dist = dict()
# 
#     LIMIT = 100000
#     
#     word = f.readline()[:-2]
#     counter = 0
#     while word is not None:
#         counter += 1
#         if counter>=LIMIT:
#             break
#         if word in dist:
#             dist[word] += 1
#         else:
#             dist[word] = 1
#         word = f.readline()[:-2]
#         
#     return dist