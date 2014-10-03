if __name__ == '__main__' and __package__ is None:
    import os
    from os import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wordminer import *
import sys
import time

PWDS = ['weeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee']

def minePwds(pwds):
    db = connectToDb()
    dictionary = getDictionary(db, dict_sets)
    freqInfo = freqReadCache(db)
    
    for p in pwds:
        print mineLine(db, p, dictionary, freqInfo)
  
if __name__ == '__main__':
    minePwds(PWDS)
