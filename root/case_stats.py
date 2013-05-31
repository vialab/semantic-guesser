from database import PwdDb
import re
from timer import Timer
from nltk.probability import FreqDist

def main(db):
    
    dist = FreqDist()
    
    total = 0

#     regex_word_capitalized = r'^[A-Z][a-z]*'
    regex_pwd_capitalized = r'^[A-Z][^A-Z]*$'
    
    while db.hasNext():
        fragments = db.nextPwd()
        pwd = fragments[0].password
        
#         if pwd == '*FENix915':
#             print 'stop'
        
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
                
                if   raw_word.istitle():  bag.add('captlzd')
                elif raw_word.islower():  bag.add('lower')
                elif raw_word.isupper():  bag.add('upper')
                else:                     bag.add('mangled')

            pattern = ', '.join(sorted(bag))

        dist.inc(pattern)    
#         print "{}\t{}".format(pattern, pwd)
    
    for k, v in dist.items():
        print "{}\t{}".format(k, v)

    
if __name__ == '__main__':
#     test()
    with Timer('Loading passwords'):
#         db = PwdDb(sample=100, random=True)
        db = PwdDb()
     
    with Timer('Processing'):
        main(db)