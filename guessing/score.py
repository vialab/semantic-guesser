# %cd semantic-guesser-lite/

from nltk.corpus    import wordnet as wn
from learning.train import getchunks, pos_tag, synset
from learning       import model
from learning.pos   import ExhaustiveTagger, BackoffTagger
from learning.tagset_conversion import TagsetConverter
from functools      import reduce
from itertools      import chain

import pickle
import time
import functools
import itertools
import argparse

from wordsegment import Segmenter
from collections import deque
from pathlib     import Path

import sys
import re

import pandas as pd

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
        self.tag_prob_cache = dict()

    @functools.lru_cache(maxsize=None)
    def get_pos(self, string):
        tags = self.postagger.get_tags(string)
        tags.append((string, None))
        return tags

    @functools.lru_cache(maxsize=None)
    def get_synsets(self, string, pos):
        if self.grammar.tagtype == 'pos' or pos is None:
            return {None}

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

    def prob(self, tag, string):
        tag_prob_cache = self.tag_prob_cache
        grammar = self.grammar

        if tag not in tag_prob_cache:
            tag_prob_cache[tag] = dict()
            samplesize          = sum(grammar.tag_dicts[tag].values())
            vocabsize           = len(grammar.tag_dicts[tag])

            if grammar.estimator == 'laplace':
                estimator = model.LaplaceEstimator(samplesize, vocabsize, 1)
            else:
                estimator = model.MleEstimator(samplesize)

            entries = map(lambda x, e=estimator: (x[0], e.probability(x[1])), grammar.tag_dicts[tag].items())

            tag_prob_cache[tag].update(entries)

        try:
            return tag_prob_cache[tag][string]
        except KeyError:
            return 0

    @functools.lru_cache(maxsize=None)
    def get_tags(self, word):
        tagset = set()
        for _, pos in self.get_pos(word):
            syns = self.get_synsets(word, pos)
            syns.add(None)
            for syn in syns:
                segment_tag = self.get_segment_tag(word, pos, syn)
                if segment_tag in self.grammar.tag_dicts:
                    p = self.prob(segment_tag, word)
                    tagset.add((segment_tag, p))
        return tagset





#%% -----------------------------------------------------------------

class GrammarTable():
    def __init__(self, grammar):
        records = []

        for i, struct in enumerate(grammar.base_structures.keys()):
            tags = re.findall("[\w\.]+", struct)
            for j, tag in enumerate(tags):
                records.append((i, tag, j))

        self.table = pd.DataFrame.from_records(records,
            columns=['base_struct_id', 'tag', 'position'],
            index=['tag', 'position'])
        self.table.sort_index(inplace=True)

    def exists(self, conditions):
        v = self.table.loc[conditions]
        return any(v.groupby('base_struct_id').size() == len(conditions))

class BaseStructChecker():
    def __init__(self, grammar):
        self.cache = set()

        for i, struct in enumerate(grammar.base_structures.keys()):
            tags = re.findall("[\w\-\'\.]+", struct)
            acc = ''
            for tag in tags:
                acc += '('+tag+')'
                self.cache.add(acc)

    def exists(self, tags):
        if type(tags) == str:
            return tags in self.cache
        else:
            return '('+')('.join(tags)+')' in self.cache


class GraphNode():
    def __init__(self, tag, id):
        self.tag = tag
        self.id  = id


class GrammarGraph():
    def __init__(self, grammar):
        self.nodes = dict() # self.nodes['tag'] = GraphNode(id, tag)
        self.edges = set()  # self.edges.add((id1, id2, position))
        self._next_node_id = 0

        for struct in grammar.base_structures.keys():
            tags = re.findall("[\w\.]+", struct)
            tags.insert(0, '^')
            tags.append('$')
            for i, (tag1, tag2) in enumerate(zip(tags[:-1], tags[1:])):
                self.add_link(tag1, tag2, i)

    def add_link(self, tag1, tag2, position):
        if tag1 not in self.nodes:
            self.nodes[tag1] = GraphNode(tag1, self._gen_id())
        if tag2 not in self.nodes:
            self.nodes[tag2] = GraphNode(tag2, self._gen_id())

        self.edges.add((
            self.nodes[tag1].id,
            self.nodes[tag2].id,
            position
        ))

    def exists(self, tag1, tag2, position):
        if tag1 not in self.nodes or tag2 not in self.nodes:
            return False
        id1 = self.nodes[tag1].id
        id2 = self.nodes[tag2].id
        return (id1, id2, position) in self.edges

    def _gen_id(self):
        self._next_node_id += 1
        return self._next_node_id - 1


#%% -----------------------------------------------------------------


class PrefixTreeNode():
    def __init__(self, word, p=0, tag=None, parent=None):
        self.word = word
        self.p = p
        self.parent = parent
        self.children = []
        self.depth = 0
        self.sequence_p = p
        self.base_struct = '('+tag+')' if tag is not None else ''
        self.tag = tag

    def append_child(self, node):
        self.children.append(node)
        node.parent = self
        node.depth = self.depth + 1
        node.sequence_p = node.p*self.sequence_p
        node.base_struct = self.base_struct + node.base_struct

    def dfs(self):
        stack = deque([self])
        while len(stack) > 0:
            node = stack.pop()
            for child in node.children:
                stack.append(child)
            yield node

    def prefix_path(self):
        p = self
        while p is not None:
            yield p
            p = p.parent

    def leaves(self):
        for node in self.dfs():
            if len(node.children) == 0:
                yield node


def score(passwords, grammar, tc_nouns,
    tc_verbs, postagger=None, vocab=None):
    """
    For each password finds the most probable rule that outputs
    it, if any. The test is done with a lowercased version of the
    password.
    """

    if postagger is None:
        postagger = ExhaustiveTagger.from_pickle()
    if vocab is None:
        vocab = grammar.get_vocab()

    memotagger = MemoTagger(postagger, tc_nouns, tc_verbs, grammar)
    base_struct_dist = dict(grammar.base_structure_probabilities())
    checker = BaseStructChecker(grammar)

    # Build a prefix tree of the segmentations, but do not include
    # in this tree sequences that don't occur in the grammar.

    for password in passwords:
        if password.isdigit():
            base_struct = 'number'+str(len(password))
            try:
                yield (password, base_struct, base_struct_dist[base_struct])
                continue
            except:
                pass


        segs = deque()
        root = PrefixTreeNode('', tag=None, p=1)
        segs.append((root, password))

        # leaves = []

        max_p = 0
        max_base_struct  = None
        max_segmentation = None

        while len(segs) > 0:
            head, tail = segs.popleft() # head is a node, tail is a string

            for newsplit in segmenter.divide(tail):
                if newsplit[0].lower() not in vocab: continue

                # check if a number sequence was split
                if newsplit[0][-1].isdigit() and \
                    newsplit[1] and newsplit[1][0].isdigit(): continue

                for tag, p in memotagger.get_tags(newsplit[0].lower()):
                    # if this tag never occurs after the head tag in the grammar
                    # then ignore this split
                    bs = head.base_struct + '(' + tag + ')'

                    if not checker.exists(bs):
                        continue

                    newhead = PrefixTreeNode(newsplit[0], tag=tag, p=p)
                    head.append_child(newhead)

                    if newsplit[1] == '': # success!
                        if newhead.base_struct in base_struct_dist:
                            p = newhead.sequence_p * base_struct_dist[newhead.base_struct]
                            if p > max_p:
                                max_p = p
                                max_base_struct  = newhead.base_struct
                                max_segmentation = [node.word for node in newhead.prefix_path()]
                                max_segmentation.reverse()
                        # leaves.append(newhead)
                    else:
                        if newhead.sequence_p > max_p:
                            segs.append((newhead, newsplit[1]))

        yield (password, max_base_struct, max_segmentation, max_p)
        # leaves = filter(lambda leaf, dist=base_struct_dist: leaf.base_struct in dist, leaves)
        # leaves = map(lambda leaf, dist=base_struct_dist: (leaf.base_struct, leaf.sequence_p * dist[leaf.base_struct]), leaves)
        # try:
        #     max_base_struct, max_p = max(leaves, key=lambda x: x[1])
        #     yield (password, max_base_struct, max_p)
        # except ValueError:
        #     yield (password, None, 0)

#%%------------------------------------------------------------------


def options():
    parser = argparse.ArgumentParser(description=('Find if passwords '
        'can be produced (guessed) by the grammar. By default, accepts only '
        'exact matches (lowercase passwords). Optionally, it can accept uppercase, '
        'camel case, and capitalized strings. These '
        'options can be used when case modification strategies are '
        'used in guess generation. '
        'This code assumes the grammar has only lowercase terminals.'))
    parser.add_argument('grammar_dir')
    parser.add_argument('passwords',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin)
    parser.add_argument('--uppercase',
        action='store_true',
        help='produce a match even when a password is uppercase')
    parser.add_argument('--camelcase',
        action='store_true',
        help=('produce a match if camel casing the segments produces '
              'the password'))
    parser.add_argument('--capitalized',
        action='store_true',
        help='produce a match even when a password is capitalized')

    return parser.parse_args()


if __name__ == '__main__':
    opts           = options()
    grammar_dir    = Path(opts.grammar_dir)
    passwords_file = opts.passwords

    accept_upper   = opts.uppercase
    accept_camel   = opts.camelcase
    accept_capital = opts.capitalized


    postagger = ExhaustiveTagger.from_pickle()
    tc_nouns  = pickle.load(open(grammar_dir / 'noun_treecut.pickle', 'rb'))
    tc_verbs  = pickle.load(open(grammar_dir / 'verb_treecut.pickle', 'rb'))
    grammar   = model.Grammar.from_files(opts.grammar_dir)

    passwords = (line.rstrip() for line in passwords_file)

    for password, struct, split, prob in score(passwords, grammar,
        tc_nouns, tc_verbs, postagger, grammar.get_vocab()):
        if password.islower() or \
           accept_upper and password.isupper() or \
           accept_camel and ''.join(map(str.capitalize, split)) == password or \
           accept_capital and password[0].isupper() and password[1:].islower():

           print(password, struct, prob)

# tagger = ExhaustiveTagger().from_pickle()
# # tagger.pickle(ExhaustiveTagger.pickle_path)
#
# tc_nouns = pickle.load(open('/Users/rafa/Data/grammar/yahoo-voices-laplace/noun_treecut.pickle', 'rb'))
# tc_verbs = pickle.load(open('/Users/rafa/Data/grammar/yahoo-voices-laplace/verb_treecut.pickle', 'rb'))
# grammar   = model.Grammar.from_files('/Users/rafa/Data/grammar/yahoo-voices-laplace')
# postagger = ExhaustiveTagger()
#
# nodes = list(score(['upsidedown'], grammar, tc_nouns, tc_verbs, postagger=postagger))
#
# for node in nodes[0]:
#     print(node.base_struct, node.sequence_p)
#
#
# vocab = grammar.get_vocab()
# memotagger = MemoTagger(postagger, tc_nouns, tc_verbs, grammar)
# base_struct_dist = dict(grammar.base_structure_probabilities())
# checker = BaseStructChecker(grammar)
#
# postagger.get_tags('down')
# memotagger.get_synsets('fell', 'vvi')

# import learning
# from importlib import reload
#
# reload(learning)
#
# vocab = learning.train.verb_vocab(tc_verbs, min_length=2)
#
# vocab = list(vocab)
#
# # [v for v in vocab if v[0] == 'grinded']
#
# keys = [leaf.key for leaf in list(tc_verbs.treecut.leaf2cut['s.attach.v.01'])[0].leaves()]
# print(sorted(keys))


# # postagger = ExhaustiveTagger.from_pickle()
# # # postagger2 = BackoffTagger.from_pickle()
# # # graph = GrammarGraph(grammar)
# # # table = GrammarTable(grammar)
# # # checker = BaseStructChecker(grammar)
# memotagger = MemoTagger(tagger, tc_nouns, tc_verbs, grammar)
#
# memotagger.get_pos('rubricking')
# memotagger.get_synsets('pick', 'vvi')
