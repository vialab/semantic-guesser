'''This script finds the WordNet uneven cut appropiate for
the frequencies computed from the passwords. 

Created on 2013-03-29

@author: rafa
'''

from tree.wordnet import load
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
                insert(tree, synset)
                
    return tree


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


def insert(tree, synset, freq=1):
    paths = synset.hypernym_paths()
    for path in paths:
        path = [s.name for s in path]
        if len(synset.hyponyms())>0:  # internal node
            path.append('s.'+path[-1])
        tree.insert(path, freq)

                    
def freq_dist_from_file(f):
    dist = dict()

    LIMIT = 100000
    
    word = f.readline()[:-2]
    counter = 0
    while word is not None:
        counter += 1
        if counter>=LIMIT:
            break
        if word in dist:
            dist[word] += 1
        else:
            dist[word] = 1
        word = f.readline()[:-2]
        
    return dist


def main(pos, f, samplesize):
    output = open(f, 'wb')
    
    tree = load(pos)
    tree = populate(tree, pos, samplesize)
    
    output.write(str(cut.findcut(tree)))
    
    output.close()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('pos', help='part-of-speech')
    parser.add_argument('-f','--file', default=DEFAULT_FILE, help='complete path of the output file')
    parser.add_argument('-s', '--samplesize', type=int, help='if this argument is not passed, runs over the entire database')
    
    args = parser.parse_args()
    
    main(args.pos, args.file, args.samplesize)
    