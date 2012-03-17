'''
Created on Mar 8, 2012

@author: Rafa
'''

from database import PwdDb
from taggers import SemanticTagger
from root.tagset_conversion import TagsetConverter
from time import time

def main():
    """ Tags the dataset by semantic categories,
        assuming it's already pos and sentiment-tagged. """
    
    db = PwdDb()
    tagger = SemanticTagger()
    
    print "tagging process initialized..."
    start = time()
    
    while (db.hasNext()):
#    for i in range(30000):
        words = db.nextPwd() # list of Words
        for w in words:
#            if w.word=="you":
#                print "bitch!" 
            t = None
            if w.synsets is not None:
                pos = TagsetConverter().brownToWordNet(w.pos)
                if pos is not None: # pos is in wordnet tagset
                    t = tagger.tag(pos, w.synsets)
                else:
                    t = tagger.tag(w.word)
            
            if w.pos[:2]=='PP' and w.pos[2]!='$': # no wordnet pos correspondent but personal pronoun
                    t = 'person'
                     
            if t is not None:
                w.category = t
#                print w.word, " ", w.category
                db.saveCategory(w)
    db.finish() 
    
    print "tagging process took " + str(time()-start) + " seconds."      
    return 0;
    
if __name__ == "__main__":
    main()