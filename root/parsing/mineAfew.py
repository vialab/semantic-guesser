from testWordMiner import *
import sys
import time

PWDS = ['crazy23duck91']

def minePwds(pwds):
    db = connectToDb()
    dictionary = getDictionary(db, dict_sets)
    freqInfo = freqReadCache(db)
    
    for p in pwds:
        print mineLine(db, p, dictionary, freqInfo)
  
if __name__ == '__main__':
    minePwds(PWDS)
