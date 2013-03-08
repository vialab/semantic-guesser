'''
This script outputs a tree in JSON format representing the
hypernym paths of all verbs tagged in the db.

@author: Rafa
'''

from database import PwdDb
from tagset_conversion import TagsetConverter
from nltk.corpus import wordnet as wn
from time import time
from tree import Tree, TreeNode

def main():
    
    db = PwdDb()
    tg = TagsetConverter() # assumes the pwds are pos-tagged using Brown tags
    
    offset = 0
    size   = 1000000
    
    # TODO: make this a command line program with options --all or --size and --offset
    
    tree = Tree()
#    treeFile = open('../results/semantic/verbs-{0}-{1}.json'.format(offset, size), 'wb')
    treeFile = open('../results/semantic/verbs-all.json', 'wb')

    
    while (db.hasNext()):
#    for i in range(offset,offset+size):
        words = db.nextPwd() # list of Words
        for w in words:
            if w.pos is None :
                continue
            wn_pos = tg.brownToWordNet(w.pos)
            if w.synsets is not None and wn_pos == 'v':
                synset = wn._synset_from_pos_and_offset(wn_pos, w.synsets)
                paths = synset.hypernym_paths()
                for path in paths :
                    path = [synset.name for synset in path]
                    path.append(w.word)
                    tree.insert(path);
                
    db.finish()
    
    treeFile.write(tree.toJSON())
    
    return 0
    
if __name__ == "__main__":
    main()
