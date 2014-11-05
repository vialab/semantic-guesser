from parsing.wordminer import *
from argparse import ArgumentParser  

def check(p):
    """ Check the probability of password p.
    """
    db = connectToDb()
    dictionary = getDictionary(db, dict_sets)
    freqInfo = freqReadCache(db)
   
    # 1. Segmentation
    segmentations =  mineLine(db, p, dictionary, freqInfo)
    # 2. POS-tagging
    for fragments in segmentations[0]:
        for f in fragments:
            
            print "{}\t{}".format(f[0], dictionary[f[0]][0])
         

def options():
    parser = ArgumentParser()
    parser.add_argument('password', type=str)
    return parser.parse_args()


if __name__ == "__main__":
    opts = options()
    check(opts.password)



