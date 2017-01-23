#!/usr/bin/env python

import database
from nltk.tag.sequential import DefaultTagger, BigramTagger, TrigramTagger,\
SequentialBackoffTagger
from nltk.probability import FreqDist
from taggers import COCATagger, NamesTagger, WordNetTagger
import cPickle as pickle
import sys
import traceback
from timer import Timer
import argparse
import util


class BackoffTagger(SequentialBackoffTagger):

    def __init__(self, *args, **kwargs):
        SequentialBackoffTagger.__init__(self, *args, **kwargs)
        self.dist = FreqDist()

#       train_sents = brown.tagged_sents()
        try:
            train_sents = pickle.load(open("pickles/brown_clawstags.pickle"))
        except:
            train_sents = pickle.load(open("root/pickles/brown_clawstags.pickle"))
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
                #self.dist.inc(tagger.__class__.__name__)
                self.dist[tagger.__class__.__name__] += 1
#                  print tokens[index], history, tagger.__class__.__name__, tag
                break
        return tag


#TODO: Isolate the POS tagging code in this function
def POStag(password, tagger):
    """ Part-of-speech tag a single password.
    Sets the POS attribute of the Fragments.
    password: a list of Fragment objects
    """
    pass


def main(db, dryrun, stats, verbose):
    """ Tags the dataset by POS and sentiment at
        the same time """

    with Timer("Backoff tagger load"):
        pos_tagger = BackoffTagger()

    counter = 0
    output_interval = round(db.savebuffer_size/5)

    with Timer("POS tagging"):
        total = db.pwset_size

        print "Connected to database, tagging..."

        lastpw = None

        while db.hasNext():
            pwd = db.nextPwd()  # list of Fragment
            pwd_str = pwd[0].password

            counter += 1

            # filters segments that are not dictionary words
            pwd = [f for f in pwd if f.dictset_id <= 90]

            # only recalculate POS if this password is diff than previous
            if pwd_str != lastpw:

                # extracts to a list of strings and tags them
                pos_tagged = pos_tagger.tag([f.word for f in pwd])


            for i, f in enumerate(pwd):
                pos = pos_tagged[i][1]  # Brown pos tag
                f.pos = pos
                if not dryrun:
                    db.save(f, True)
                if verbose:
                    print "{}\t{}\t{}".format(f.password, f.word, f.pos)

            lastpw = pwd_str

            if counter % output_interval == 0:
                # util.printprogress(counter/output_interval, total/output_interval)
                print "{} passwords processed. {:.2f}% completed..."\
                .format(counter, (float(counter)/total)*100)
                # print "{} passwords processed.".format(counter)

        db.finish()

        if stats:
            print "\nFrequency distribution of results by tagger\n"
            for k, v in pos_tagger.dist.items():
                print "{}\t{}".format(k, v)


def options():
    parser = argparse.ArgumentParser()
    parser.add_argument('password_set', default=1, type=int, \
        help='the id of the collection of passwords to be processed')
    parser.add_argument('-s', '--sample', default=None, type=int, \
        help="sample size")
    parser.add_argument('-d', '--dryrun', action='store_true', \
        help="no commits to the database")
    parser.add_argument('-t', '--stats', action='store_true', \
        help="output stats in the end")
    parser.add_argument('-v', '--verbose', action='store_true', \
        help="output the pos tags of each password")

    return parser.parse_args()


if __name__ == "__main__":
    opts = options()

    try:
        db = database.PwdDb(opts.password_set, samplesize=opts.sample, save_cachesize=500000)
        main(db, opts.dryrun, opts.stats, opts.verbose)
    except:
        e = sys.exc_info()[0]
        traceback.print_exc()
        sys.exit(1)

    # tests
#     t = getTagger()
#     print t.tag(['fat','boy','1'])
#     print t.tag(['fat','boy'])
#     print nltk.pos_tag(['all', 'yours'])
#     print nltk.pos_tag(['screw','you', 'all'])
#     print nltk.pos_tag(['all','that', 'counts'])
#     print nltk.pos_tag(['all','day'])
#     print nltk.pos_tag(['all','the', 'cake'])
#     print nltk.pos_tag(['all', 'alone'])
#     print nltk.pos_tag(['to', 'lose', "one's", 'all'])
