''' This script outputs all the nouns/verbs, etc. found in a given range of
password ids.

Created on 2012-11-23

@author: Rafa
'''

from database import PwdDb
from tagset_conversion import TagsetConverter

def main():
    db = PwdDb()
    tg = TagsetConverter() # assumes the pwds are pos-tagged using Brown tags
    
    offset = 0
    size   = 1000000
    
    #output_file = open('../results/semantic/nouns/{0}_{1}.txt'.format(offset, size), 'wb')
    output_file = open('../results/pos/verbs/all.txt'.format(offset, size), 'wb')


    while (db.hasNext()):    
#    for i in range(offset,offset+size):
        words = db.nextPwd() # list of Words
        
        for w in words:
            if w.pos is None :
                continue
            wn_pos = tg.brownToWordNet(w.pos)
            if wn_pos == 'v':
                output_file.write(str(w.word) + '\n')
    
    db.finish()
    
    return 0

if __name__ == "__main__":
    main()