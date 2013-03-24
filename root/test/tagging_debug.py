'''
I wrote this just to verify what tags in the Brown corpus have no correspondent
in wordnet. In addition I wanted to see the impact on the pos-tagging of the
passwords and review my mapping brown -> wordnet.

Created on 2013-03-12

@author: rafa
'''

from database import PwdDb
from tagset_conversion import TagsetConverter

if __name__ == '__main__':
    db = PwdDb()
    tagconverter = TagsetConverter()
    
    # tags not convered by wordnet 
    notcovered = dict()
    
    while db.hasNext() :
        p = db.nextPwd()
        
        for w in p :
            
            if w.pos is not None and tagconverter.brownToWordNet(w.pos) is None :
                freq = notcovered[w.pos] if w.pos in notcovered else 0 
                notcovered[w.pos] = freq + 1
    
    db.finish()
    
    print notcovered
    