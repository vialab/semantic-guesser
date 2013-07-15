#from multiprocessing import Pool, freeze_support
#import itertools
#
#def aFunction(q,x):
#  return [ [len(z),z,q] for z in x]
#
#def a_star(x):
#  return aFunction(*x)
#
#if __name__ == '__main__':
#  pool = Pool(processes=4)
#  basedir = '/home/Till/passwordStuff/'
#  fdict = basedir+'dictionaries/words100'
#  passin = basedir+'rockyou/lim1m'
#  output = basedir+'wordmined'
#  d = list()
#  with open(passin, encoding='WINDOWS-1252', mode='r') as f:
#    for line in f:
#      d.append(line.strip())
#  
#  hi = 'hi'
#  result = pool.map_async(a_star, zip(itertools.repeat(hi), [d]), 1000)
#  
#  #print(result)
#  #print(dir(result))
#  print(result.get())


from testWordMiner import *
from testMinerCache import *
from testMinerQueries import *

if __name__ == '__main__':
    db = connectToDb()
    freqInfo = freqReadCache(db)
    resetDynamicDictionary(db)
    dictionary = getDictionary(db, [10, 20, 30, 40, 50, 60, 80, 90])
    mineLine('" freakin idiot"', dictionary, freqInfo, transforms=None)