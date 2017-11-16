import pickle
import sys
import traceback
import csv
import os
from nltk.corpus import wordnet

from nltk.tag.sequential import DefaultTagger, \
                                BigramTagger,  \
                                TrigramTagger, \
                                SequentialBackoffTagger
from nltk.probability import FreqDist

class BackoffTagger(SequentialBackoffTagger):

    pickle_path = os.path.join(os.path.dirname(__file__),
        '../data/backoff_tagger.pickle')

    def __init__(self, *args, **kwargs):
        SequentialBackoffTagger.__init__(self, *args, **kwargs)

        self.dist = FreqDist()

        tagged_brown_path = os.path.join(os.path.dirname(__file__),
            '../data/brown_clawstags.pickle')
        train_sents = pickle.load(open(tagged_brown_path, 'rb'))

        # make sure all tuples are in the required format: (TAG, word)
        train_sents = [[t for t in sentence
            if len(t) == 2] for sentence in train_sents]

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
                self.dist[tagger.__class__.__name__] += 1
                break
        return tag

    def choose_tag(self, tokens, index, history):
        # this tagger is a wrapper for taggers
        return None

    def pickle(self, path=None):
        if not path:
            path = BackoffTagger.pickle_path

        pickle.dump(self, open(path, 'wb'))

    @classmethod
    def from_pickle(cls, path=None):
        if not path:
            path = cls.pickle_path

        return pickle.load(open(path, 'rb'))

class WordNetTagger(SequentialBackoffTagger):
    '''
    >>> wt = WordNetTagger()
    >>> wt.tag(['food', 'is', 'great'])
    [('food', 'nn'), ('is', 'vv0'), ('great', 'jj')]
    '''
    def __init__(self, *args, **kwargs):
        SequentialBackoffTagger.__init__(self, *args, **kwargs)

        # maps wordnet tags to claws7 tags
        self.wordnet_tag_map = {
            'n': 'nn',
            's': 'jj',
            'a': 'jj',
            'r': 'rr',
            'v': 'vv0'
        }

    def choose_tag(self, tokens, index, history):
        word = tokens[index]
        if word is None:
            return None
        fd = FreqDist()

        for synset in wordnet.synsets(word):
            fd[synset.pos] += 1
        try:
            return self.wordnet_tag_map.get(fd.max())
        except:  # in case fd is empty
            return None


class NamesTagger(SequentialBackoffTagger):
    """
        >>> nt = NamesTagger()
        >>> nt.tag(['Jacob'])
        [('Jacob', 'np')]
    """
    def __init__(self, *args, **kwargs):
        SequentialBackoffTagger.__init__(self, *args, **kwargs)
        self.name_set = []
        for line in open(os.path.join(os.path.dirname(__file__),
            '../data/names.txt')):
            self.name_set.append(line.strip())

    def choose_tag(self, tokens, index, history):

        word = tokens[index]

        if word is None:
            return None

        if word.lower() in self.name_set:
            return 'np'
        else:
            return None


class COCATagger(SequentialBackoffTagger):
    def __init__(self, *args, **kwargs):
        SequentialBackoffTagger.__init__(self, *args, **kwargs)
        coca_path = os.path.join(os.path.dirname(__file__),'../data/coca_500k.csv')
        coca_list = csv.reader(open(coca_path), delimiter='\t')
        self.tag_map = dict()
        for row in coca_list:
            freq = int(row[0])
            word = row[1].strip()
            pos  = row[2].strip()
            self.insertPair(word, pos, freq)

    def insertPair(self, word, pos, freq):
        """ Appends a (pos,freq) tuple in the end of the list
        corresponding to a word. Since they're ranked in coca file
        it should result in an ordered list by frequency """
        map_ = self.tag_map
        if (word not in map_):
            map_[word] = [(pos, freq)]
        else:
            map_[word].append((pos,freq))

    def choose_tag(self, tokens, index, history):
        word = tokens[index]
        if word in self.tag_map:
            posfreq = self.tag_map[word][0]
            #return self.tag_converter.claws7ToBrown(posfreq[0])
            return posfreq[0]
        else:
            return None
