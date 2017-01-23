#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Proper way to run this script:
# python -m root.test.estimation
# from semantic-guesser/

"""
Tests the accuracy of the Laplace estimator for probabilities of words in passwords.
Uses the framework from Manning and Schütze (1999), section 6.2.2 (see Table 6.4),
for comparison of accuracy of estimators.

Divides the data into training and test. Trains the Laplace estimator using the
training data. Then compares the predicted frequencies of frequencies with the
empirical frequencies of frequencies in the test data.

"""

from root.database   import PwdDb
import root.util as util
from collections     import defaultdict
from root.pos_tagger import BackoffTagger
from root.estimator  import LaplaceEstimator, MleEstimator, FreqDist, noun_vocab, verb_vocab

def main():
    tagger = BackoffTagger()
    vocabulary = noun_vocab(tagger)
    vocabulary.update(verb_vocab(tagger))

    # word probability estimators, to be trained with training data
    lap = LaplaceEstimator(vocabulary)
    mle = MleEstimator(vocabulary)

    # frequency of each word found in the test set
    test_dist = FreqDist([])

    # if password is in the training set, use it to train estimators
    # if it's from the test set, store count of each word
    db = PwdDb(1)
    n  = 100
    interval = round(float(db.pwset_size)/n)
    i = 1
    k = 1
    while db.hasNext():
        segments = db.nextPwd()
        for s in segments:
            if s.dictset_id < 100:  # if it's a dictionary word
                if not s.test:
                    lap.inc((s.word, s.pos))
                    mle.inc((s.word, s.pos))
                else:
                   test_dist.inc((s.word, s.pos))
        i += 1
        if i == interval:
            i = 0
    	    k += 1
            util.printprogress(k, n)

    util.printprogress(k, n)
    db.finish()

    # Now we want to see how well the estimators predict the frequencies
    # in the test data.
    # We compare the frequency of frequencies.
    # For example, if we saw 10 words that have frequency 2 in the training data,
    # what's the avg, freq. of these words in the test data? (This is a comparison
    # of MLE and f_empirical).
    # In the same way, how do these compare with the avg. freq. predicted by the
    # Laplace estimator (f_lap).

	
    mle_binned  = mle.group_by_freq() # estimated frequency of frequencies in test data
    freqs       = mle_binned.keys()
    f_empirical = FreqDist(freqs) # empirical avg. frequency of frequencies in test data
    lap_binned  = lap.group_by_freq() # estimated avg. frequency of frequencies in test data (Laplace method)
    
    f_lap = defaultdict(lambda:0)
    # Iterate over vocabulary
    # 1. tally observed word counts aggregated by count in training data (f_empirical)
    # 2. tally Laplacian probabilities aggregated by count in training data (f_lap)
    # 3. transform measures above into avg. frequencies
    for f, lemma_list in mle_binned.items():
        for lemma in lemma_list: # lemmas is a tuple (word, pos)
            if lemma in test_dist:
                f_empirical.inc(f, test_dist[lemma])
            if lemma in lap:
                f_lap[f] += lap.probability(lemma)
        f_lap[f] *= float(test_dist.total) / len(lemma_list)
        f_empirical[f] = float(f_empirical[f])/len(lemma_list)

    print "r\tf_empirical\tf_lap\n"
    for r, f_emp in f_empirical.items():
        print "{}\t{}\t{}".format(r, f_emp, f_lap[r])

        

	

	# ---------- test data ------------------
#	test_dist = FreqDist([])
#	db = PwdDb(1, test=1)
#	while db.hasNext():
#		segments = db.nextPwd()
#		for s in segments:
#			if s.dictset_id
    


if __name__ == "__main__":
    main()

# TODO:
# build avg. frequencies of frequencies for training data
# build avg. frequencies of frequencies for test data
