''' This script outputs all the nouns found in a given range of
password ids in a format that be inputted in docuburst for visualization
of the categories.

Created on 2012-11-23

@author: Rafa
'''

from database import PwdDb
from root.tagset_conversion import TagsetConverter

def main():
    db = PwdDb()
    tg = TagsetConverter() # assumes the pwds are pos-tagged using Brown tags
    
    offset = 0
    size   = 1000000
    
    docuburstFile = open('../results/semantic/nouns/{0}_{1}.txt'.format(offset, size), 'wb')
    
    for i in range(offset,offset+size):
        words = db.nextPwd() # list of Words
        for w in words:
            wn_pos = tg.brownToWordNet(w.pos)
            if wn_pos == 'n':
                docuburstFile.write(str(w.word) + ' ')
    
    db.finish(False)
    
    return 0

if __name__ == "__main__":
    main()