import pickle
import sys
import traceback
import csv
import os
from nltk.corpus import wordnet

from nltk.tag.sequential import DefaultTagger, \
                                BigramTagger,  \
                                UnigramTagger,  \
                                TrigramTagger, \
                                SequentialBackoffTagger
from nltk.probability import FreqDist

class ExhaustiveTagger():
    """
    Returns a comprehensive list of tags for a word. Does not tag
    numbers.
    """
    pickle_path = os.path.join(os.path.dirname(__file__),
        '../data/exhaustive_tagger.pickle')

    def __init__(self):
        tagged_brown_path = os.path.join(os.path.dirname(__file__),
            '../data/brown_clawstags.pickle')
        train_sents = pickle.load(open(tagged_brown_path, 'rb'))

        # make sure all tuples are in the required format: (TAG, word)
        train_sents = [[t for t in sentence
            if len(t) == 2] for sentence in train_sents]

        self.taggers = [
            WordNetTagger(),
            NamesTagger(),
            COCATagger(),
            MyUnigramTagger(train_sents)
        ]

    def tag(self, tokens):
        taglists = []
        for index, token in enumerate(tokens):
            taglists.append(self.tag_one(tokens, index, taglists))
        return taglists

    def tag_one(self, tokens, index, history):
        token = tokens[index]
        if token.isdigit(): return [(token,None)]

        tags = set()

        for tagger in self.taggers:
            tags.update(tagger.get_tags(token))

        return [(token, tag) for tag in tags] if len(tags) else [(token, None)]

    def get_tags(self, token):
        return self.tag_one([token], 0, [])

    def pickle(self, path=None):
        if not path:
            path = ExhaustiveTagger.pickle_path

        pickle.dump(self, open(path, 'wb'))

    @classmethod
    def from_pickle(cls, path=None):
        if not path:
            path = cls.pickle_path

        return pickle.load(open(path, 'rb'))


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

        # default_tagger = DefaultTagger('nn')
        wn_tagger      = WordNetTagger()
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

    def set_wordnet_instance(self, wordnet):
        """
        Set an instance of WordNetCorpusReader. If not set, then WordNetTagger
        will use the one imported globally. It's advisable to create an instance
        per Process when running tasks in parallel.
        """
        for tagger in self._taggers:
            if isinstance(tagger, WordNetTagger):
                tagger.set_wordnet_instance(wordnet)

    @classmethod
    def proper_noun_tags(cls):
        return ['np', 'np1', 'np2']

    @classmethod
    def from_pickle(cls, path=None):
        if not path:
            path = cls.pickle_path

        return pickle.load(open(path, 'rb'))


class MyUnigramTagger(UnigramTagger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_tags(self, token):
        return [self.choose_tag([token], 0, [])]


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

        self.wordnet = wordnet

    def get_tags(self, token):
        synsets = self.wordnet.synsets(token)
        tagset  = set()
        taglist = []
        for syn in synsets:
            pos = self.wordnet_tag_map[syn.pos()]
            if pos not in tagset:
                tagset.add(pos)
                taglist.append(pos)
        return taglist

    def choose_tag(self, tokens, index, history):
        word = tokens[index]
        if word is None:
            return None
        if len(word) < 3:
            return None
        fd = FreqDist()

        for synset in self.wordnet.synsets(word):
            fd[synset.pos] += 1
        try:
            return self.wordnet_tag_map.get(fd.max())
        except:  # in case fd is empty
            return None

    def __getstate__(self):
        state = dict(self.__dict__)
        del state['wordnet']
        return state

    def __setstate__(self, d):
        self.wordnet_tag_map = d['wordnet_tag_map']
        self.wordnet = wordnet

    def set_wordnet_instance(self, wordnet):
        """
        Set an instance of WordNetCorpusReader. If not set, then this object
        will use the one imported globally. It's advisable to create an instance
        per Process when running tasks in parallel.
        """
        self.wordnet = wordnet

def _datafile(name):
    return open(os.path.join(os.path.dirname(__file__), '../data/'+name),
        encoding='utf-8')

class NamesTagger(SequentialBackoffTagger):
    """
        >>> nt = NamesTagger()
        >>> nt.tag(['Jacob'])
        [('Jacob', 'np')]
    """

    MaleNames   = set([name.strip() for name in _datafile('mnames.txt')])
    FemaleNames = set([name.strip() for name in _datafile('fnames.txt')])
    Countries   = set([country.strip() for country in _datafile('countries.txt')])
    # Months      = set([month.strip() for month in _datafile('months.txt')])
    Surnames    = set([surname.strip() for surname in _datafile('surnames.txt')])
    Cities      = set([city.strip() for city in _datafile('cities.txt')])

    def __init__(self, *args, **kwargs):
        SequentialBackoffTagger.__init__(self, *args, **kwargs)
        # self.name_set = []
        # for line in open(os.path.join(os.path.dirname(__file__),
        #     '../data/names.txt')):
        #     self.name_set.append(line.strip())

    def choose_tag(self, tokens, index, history):
        word = tokens[index]

        if word is None:
            return None

        if self.is_propername(word.lower()):
            return 'np'
        else:
            return None

    def get_tags(self, token):
        if self.is_propername(token): return ['np']
        else: return []

    def is_propername(self, string):
        return string in NamesTagger.MaleNames or \
               string in NamesTagger.FemaleNames or \
               string in NamesTagger.Cities or \
               string in NamesTagger.Surnames or \
               string in NamesTagger.Countries


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
            pos, freq = self.tag_map[word][0]
            #return self.tag_converter.claws7ToBrown(posfreq[0])
            
            if (pos == 'np1' or pos == 'nn1') and len(word) < 3: # notably noisy classes
                pos = None
            elif (pos == 'np1' or pos == 'nn1') and len(word) == 3 and freq < 10000:
                pos = None

            return pos
        else:
            return None

    def get_tags(self, token):
        # return the 3 most frequent POS tags if len(token) > 1
        # if it's a letter, then return only the most frequent
        if token in self.tag_map:
            return [tag for tag, freq in self.tag_map[token][:4]]
        # elif len(token) == 1 and token in self.tag_map:
        #     return self.tag_map[token][0][0]
        else:
            return []


class SpacyTagger():
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm', disable=["parser", "ner"])
        coca_path = os.path.join(os.path.dirname(__file__),'../data/coca_500k.csv')
        with open(coca_path) as f:
            self.coca = dict()
            for line in f:
                freq, word, pos, _ = line.rstrip().split('\t')
                freq = int(freq)
                if word in coca and coca[word] > freq: continue
                coca[word] = freq

    def tag(self, tokens):
        doc = self.nlp(' '.join(tokens))
        tags = []
        for token in doc:
            if token in coca and coca[token] > 1000:
                tags.append([token.text, token.tag_ ])
            else:
                tags.append([token.text, None])
        return tags
