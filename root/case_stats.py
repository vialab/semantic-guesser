from database import PwdDb
import re
from timer import Timer
from nltk.probability import FreqDist

def bysegment(db):
    dist = FreqDist()
    
    total = 0

    while db.hasNext():
        fragments = db.nextPwd()
        pwd = fragments[0].password
        
        for f in fragments: # iterate through fragments
            total += 1
            if total % 100000 == 0:
                print "{} segments processed...".format(total)
                
            if f.is_gap(): 
                dist.inc("gap")
            else:
                raw_word = pwd[f.s_index:f.e_index]

                if     raw_word.isupper():  dist.inc('upper')
                elif   raw_word.istitle():  dist.inc('capitalized')
                elif   raw_word.islower():  dist.inc('lower')
                else:                       dist.inc('mangled')
            
    for k, v in dist.items():
        print "{}\t{}".format(k, v)


def bypassword(db):
    
    dist = FreqDist()
    
    total = 0

#     regex_word_capitalized = r'^[A-Z][a-z]*'
    regex_pwd_capitalized = r'^[A-Z][^A-Z]*$'
    
    while db.hasNext():
        fragments = db.nextPwd()
        pwd = fragments[0].password
        
        total += 1
        
        if total % 100000 == 0:
            print "{} passwords processed...".format(total)
        
        pattern = None
        
        if all([f.is_gap() for f in fragments]): 
            pattern = 'gap'
        elif re.match(regex_pwd_capitalized, pwd):
            pattern = 'title'
        else:
            bag = set()
        
            for f in fragments:
                if f.is_gap(): continue
                
                raw_word = pwd[f.s_index:f.e_index]
                
                if     raw_word.isupper():  bag.add('upper')
                elif   raw_word.istitle():  bag.add('captlzd')
                elif   raw_word.islower():  bag.add('lower')
                else:                     bag.add('mangled')
                
            pattern = ', '.join(sorted(bag))
            if pattern == 'captlzd, upper': print pwd

        dist.inc(pattern)    
    
    for k, v in dist.items():
        print "{}\t{}".format(k, v)

    
if __name__ == '__main__':
    with Timer('Loading passwords'):
#         db = PwdDb(sample=100, random=True)
        db = PwdDb()
     
    with Timer('Processing'):
        bysegment(db)