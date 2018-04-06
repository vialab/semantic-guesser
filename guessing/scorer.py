# %cd semantic-guesser-lite/

from nltk.corpus    import wordnet as wn
from learning.train import getchunks, pos_tag, synset
from learning       import model
from learning.pos   import BackoffTagger
from learning.tagset_conversion import TagsetConverter
from functools      import reduce
from itertools      import chain

import pickle
import time
import functools
import itertools

from wordsegment import Segmenter
from collections import deque

segmenter = Segmenter()
segmenter.load()

def product(list_a, list_b):
    for a in list_a:
        for b in list_b:
            try:
                yield a + [b]
            except TypeError:
                yield [a, b]

def segment_all(word, segmenter, vocab=None):
    # an optional filter for word splits:
    def isgood(seg):
       good = True
       if seg[0] not in vocab: good = False
       # check if it a number sequence was split
       if seg[0][-1].isdigit() and seg[1] and seg[1][0].isdigit(): good = False

       return good

    # disable filtering with identity filter
    # isgood = lambda x: x

    segs = deque(filter(isgood, segmenter.divide(word)))

    results = [(word,)]

    while len(segs) > 0:
        seg = segs.popleft()
        tail = seg[-1]
        newsplits = filter(isgood, segmenter.divide(tail))

        for newsplit in newsplits:
            if newsplit[1] == '': # success!
                results.append(seg)
            else:
                segs.append(tuple(chain(seg[:-1], newsplit)))
    return results


def score_segmentation(result):
    prob = 1
    for curr, prev in zip(range(len(result)), range(-1,len(result)-1)):
        if curr == 0:
            prob *= segmenter.score(result[curr])
        else:
            prob *= segmenter.score(result[curr], result[prev])
    return prob



class MemoTagger():
    def __init__(self, postagger, tc_nouns, tc_verbs, grammar):
        self.postagger = postagger
        self.tc_nouns  = tc_nouns
        self.tc_verbs  = tc_verbs
        self.grammar   = grammar
        self.tagconv   = TagsetConverter()

    @functools.lru_cache(maxsize=None)
    def get_pos(self, string):
        tags = self.postagger.get_tags(string)
        tags.append((string, None))
        return tags

    @functools.lru_cache(maxsize=None)
    def get_synsets(self, string, pos):
        if pos is None: return {None}
        wnpos = self.tagconv.clawsToWordNet(pos)
        if wnpos not in ('n', 'v') or \
            (wnpos == 'v' and len(string) < 2) or \
            (wnpos == 'n' and len(string) < 3): return {None}

        tc_model = self.tc_nouns if wnpos == 'n' else self.tc_verbs
        syns = [None]
        for syn in wn.synsets(string, wnpos):
            syns.extend(tc_model.predict(syn))

        return set(syns)

    @functools.lru_cache(maxsize=None)
    def get_segment_tag(self, string, pos, synset):
        return self.grammar.tagger._get_tag(string, pos, synset, self.grammar.tagtype)



#%% -----------------------------------------------------------------

def score(passwords, grammar, tc_nouns, tc_verbs, postagger=None):
    tag_prob_cache = dict()

    def prob(tag, string):
        if tag not in tag_prob_cache:
            tag_prob_cache[tag] = dict()
            samplesize          = sum(grammar.tag_dicts[tag].values())
            vocabsize           = len(grammar.tag_dicts[tag].keys())

            if grammar.estimator == 'laplace':
                estimator = model.LaplaceEstimator(samplesize, vocabsize, 1)
            else:
                estimator = model.MleEstimator(samplesize)

            for k, count in grammar.tag_dicts[tag].items():
                tag_prob_cache[tag][k] = estimator.probability(count)

        try:
            return tag_prob_cache[tag][string]
        except KeyError:
            return 0


    word2tags  = dict()
    tagconv    = TagsetConverter()
    memotagger = MemoTagger(postagger, tc_nouns, tc_verbs, grammar)
    vocab      = grammar.get_vocab()

    N = 0


    for password in passwords:
        segmentations = segment_all(password, segmenter, vocab)

        for segmentation in segmentations:
            for word in segmentation:
                if word in word2tags: continue
                word2tags[word] = set()
                for _, pos in memotagger.get_pos(word):
                    syns = memotagger.get_synsets(word, pos)
                    syns.add(None)
                    for syn in memotagger.get_synsets(word, pos):
                        segment_tag = memotagger.get_segment_tag(word, pos, syn)
                        if segment_tag in grammar.tag_dicts:
                            p = prob(segment_tag, word)
                            if p > 0:
                                word2tags[word].add((segment_tag, p))

        maxprob = 0
        maxbase = ''
        for segmentation in segmentations:
            if len(segmentation) == 1:
                parsings = [[w] for w in word2tags[segmentation[0]]]
            else:
                parsings = list(itertools.product(*[word2tags[word] for word in segmentation]))

            N += 1

            for parsing in parsings:
                aborted = False
                base_structure = ''
                p = 1
                for i, (tag, tag_p) in enumerate(parsing):
                    string = segmentation[i]
                    base_structure += '({})'.format(tag)

                    p *= tag_p
                    if p < maxprob:
                        aborted = True
                        break

                if aborted:
                    continue
                else:
                    p *= grammar.base_structures[base_structure]/grammar.counter

                if p > maxprob:
                    maxprob = p
                    maxbase = base_structure

        yield (maxprob, maxbase)




#%% -----------------------------------------------------------------


from functools import partial
import learning.pos

from learning.train import getchunks, pos_tag, synset

tagger = learning.pos.ExhaustiveTagger()
tc_nouns = pickle.load(open('/Users/rafa/Data/grammar/yahoo-voices-laplace/noun_treecut.pickle', 'rb'))
tc_verbs = pickle.load(open('/Users/rafa/Data/grammar/yahoo-voices-laplace/verb_treecut.pickle', 'rb'))
gramma   = model.Grammar.from_files('/Users/rafa/Data/grammar/yahoo-voices-laplace')

sample = sorted(gramma.sample(1000), key=lambda x: x[1])

predicted_p = list(score((pwd[0] for pwd in sample), gramma, tc_nouns, tc_verbs, tagger))

num_wrong = 0
for i, (pwd, base_struct, p) in enumerate(sample):
    if (p - predicted_p[i][0]) > 1e-5:
        num_wrong += 1
        print(pwd, p, predicted_p[i][0], base_struct, predicted_p[i][1])
print(num_wrong)


# import importlib
# importlib.reload(learning.pos)
