'''
This script outputs a tree in JSON format representing the
hypernym paths of all verbs/nouns/etc. tagged in the db.

@author: Rafa
'''

from database import PwdDb
from tagset_conversion import TagsetConverter
from nltk.corpus import wordnet as wn
from tree.default_tree import DefaultTree 
import argparse

def main(pos, size):
    
    db = PwdDb(size=size)
    tg = TagsetConverter() # assumes the pwds are pos-tagged using Brown tags
    
    tree = DefaultTree()
#    treeFile = open('../results/semantic/verbs-{0}-{1}.json'.format(offset, size), 'wb')
#    treeFile = open('../results/semantic/verbs-all.json', 'wb')
    treeFile = open('/home/rafa/Desktop/test.json', 'wb')

    posTotal     = 0  # number of pos-tagged words
    verbsTotal   = 0  # number of verbs 
    wnVerbsTotal = 0  # number of verbs that are found in wordnet

    count = 0        
    
    if size is None: size = float('inf')
    
    while (db.hasNext()):
        count += 1
        if count >= size:
            break
        
        words = db.nextPwd() # list of Words
        
        for w in words:
            if w.pos is None :
                continue
            posTotal += 1
            wn_pos = tg.brownToWordNet(w.pos)
            if wn_pos == pos :
                verbsTotal += 1
                if w.synsets is not None :
                    wnVerbsTotal += 1
                    synset = wn._synset_from_pos_and_offset(wn_pos, w.synsets)
                    paths  = synset.hypernym_paths()
                    for path in paths :
                        path = [synset.name for synset in path]
                        path.append(w.word)
                        tree.insert(path);
                
    tree.updateEntropy()
    treeFile.write(tree.toJSON())

    db.finish()
    
    print '{} POS tagged words'.format(posTotal)
    print 'of which {} are verbs ({}%)'.format(verbsTotal, float(verbsTotal)*100/posTotal)
    print 'of which {} are found in WordNet ({}%)'.format(wnVerbsTotal, float(wnVerbsTotal)*100/verbsTotal)
    
    return 0
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('pos', help='part-of-speech of the semantic tree. n (noun) or v (verb)')
    parser.add_argument('-s', '--size', type=int, default=None,
                        help='size of the sample from which the words should be gotten.')
    args = parser.parse_args()
    
    main(args.pos, args.size)
