#!/usr/bin/env python

from database import PwdDb
from nltk.tag.sequential import DefaultTagger, BigramTagger, TrigramTagger, SequentialBackoffTagger
from nltk.probability import FreqDist
from taggers import COCATagger, NamesTagger, WordNetTagger
import cPickle as pickle
import sys
import traceback
from timer import Timer
import argparse


class BackoffTagger(SequentialBackoffTagger):
    
    def __init__(self, *args, **kwargs):
        SequentialBackoffTagger.__init__(self, *args, **kwargs)
        self.dist = FreqDist()
        
#       train_sents = brown.tagged_sents()
        train_sents = pickle.load(open("pickles/brown_clawstags.pickle"))
        # make sure all tuples are in the required format: (TAG, word)
        train_sents = [[t for t in sentence if len(t) == 2] for sentence in train_sents]

        default_tagger = DefaultTagger('nn')
        wn_tagger      = WordNetTagger(default_tagger)
        names_tagger   = NamesTagger(wn_tagger)
        coca_tagger    = COCATagger(names_tagger)
        bigram_tagger  = BigramTagger(train_sents, backoff=coca_tagger)
        trigram_tagger = TrigramTagger(train_sents, backoff=bigram_tagger)
        
        # doesn't include self cause it's a dumb tagger (would always return None)
        self._taggers = trigram_tagger._taggers 

    def tag_one(self, tokens, index, history):
        tag = None
        for tagger in self._taggers:
            tag = tagger.choose_tag(tokens, index, history)
            if tag is not None:  
                self.dist.inc(tagger.__class__.__name__)
#                  print tokens[index], history, tagger.__class__.__name__, tag
                break
        return tag 


def main(sample, dryrun, stats, verbose):
    """ Tags the dataset by POS and sentiment at
        the same time """    
    
    with Timer("Backoff tagger load"):    
        pos_tagger = BackoffTagger()
    
    counter = 0
    
    with Timer("POS tagging"):
        db = PwdDb(sample=sample)
        total = db.sets_size
        
        print "Connected to database, tagging..."
        
        while db.hasNext():
            pwd = db.nextPwd()  # list of segments
            counter += 1
            # filters segments that are not dictionary words
            pwd = [f for f in pwd if f.dictset_id <= 90]
            
            # extracts to a list of strings and tags them
            pos_tagged = pos_tagger.tag([f.word for f in pwd])
            
            for i, f in enumerate(pwd):
                pos = pos_tagged[i][1]  # Brown pos tag
                f.pos = pos
                if not dryrun:
                    db.save(f, True)
                if verbose:
                    print "{}\t{}\t{}".format(f.password, f.word, f.pos)

            if counter % 100000 == 0:
                print "{} passwords processed. {}% completed...".format(counter, (float(counter)/total)*100)
        
        db.finish()
        
        if stats:
            print "\nFrequency distribution of results by tagger\n"
            for k, v in pos_tagger.dist.items():
                print "{}\t{}".format(k, v)
    

def options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--sample', default=None, type=int, help="sample size")
    parser.add_argument('-d', '--dryrun', action='store_true', help="no commits to the database")
    parser.add_argument('-t', '--stats', action='store_true', help="output stats in the end")
    parser.add_argument('-v', '--verbose', action='store_true', help="output the pos tags of each password")
    
    return parser.parse_args()
 
 
if __name__ == "__main__":
    opts = options()
    try:
        main(opts.sample, opts.dryrun, opts.stats, opts.verbose)
    except:
        e = sys.exc_info()[0]
        traceback.print_exc()
        sys.exit(1)





    
    # tests
#     t = getTagger()
#     print t.tag(['fat','boy','1'])
#     print t.tag(['fat','boy'])
#     print nltk.pos_tag(['all', 'yours'])
#     print nltk.pos_tag(['fuck','you', 'all'])
#     print nltk.pos_tag(['all','that', 'counts'])
#     print nltk.pos_tag(['all','day'])
#     print nltk.pos_tag(['all','day'])
#     print nltk.pos_tag(['all','the', 'cake'])
#     print nltk.pos_tag(['all', 'alone'])
#     print nltk.pos_tag(['to', 'lose', "one's", 'all'])




