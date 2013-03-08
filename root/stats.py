'''
Basic statistics on classification.

@author: Rafa
'''

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
    tc = TagsetConverter() # assumes the pwds are pos-tagged using Brown tags
    
    pos_dist    = dict() 
    wn_pos_dist = dict()
    
    fragments_total = 0  # number of words
    pos_total       = 0  # number of pos-tagged words
    wn_verbs_total  = 0  # number of verbs that are found in wordnet
    wn_nouns_total  = 0  # number of verbs that are found in wordnet
        
    while (db.hasNext()):
        words = db.nextPwd() # list of Words
        fragments_total += len(words)
        
        for w in words:
            if w.pos is None :
                continue
            pos_total += 1
            
            if w.pos in pos_dist :
                pos_dist[w.pos] += 1
            else : 
                pos_dist[w.pos] = 1
            
            wn_pos = tc.brownToWordNet(w.pos)
            
            if wn_pos in wn_pos_dist :
                wn_pos_dist[wn_pos] += 1
            else : 
                wn_pos_dist[wn_pos] = 1
                
            if w.synsets is not None:
                if wn_pos == 'v' :
                    wn_verbs_total += 1
                elif wn_pos == 'n' :
                    wn_nouns_total += 1
        
    db.finish()
    
    print "Total number of fragments: {}".format(fragments_total)
    print 'of which {} are POS tagged words ({}%)'.format(pos_total, float(pos_total)/fragments_total)
    print '\nPOS distribution:\n', pos_dist
    print '\nPOS distribution (WordNet tagset):\n', wn_pos_dist     
    print '\n{} verbs found in WordNet ({}% of verbs)'.format(wn_verbs_total, float(wn_verbs_total)/wn_pos_dist['v'])
    print '\n{} nouns found in WordNet ({}% of nouns)'.format(wn_nouns_total, float(wn_nouns_total)/wn_pos_dist['n'])
    
    return 0
    
if __name__ == "__main__":
    main()

