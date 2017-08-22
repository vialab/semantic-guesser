#!/usr/bin/env python

"""
This script generates a context-free grammar
that captures the semantic patterns of a list of
passwords.

It's based on Weir (2009)*.

*http://dl.acm.org/citation.cfm?id=1608146

Created on Apr 18, 2013

"""
from database import Fragment

__author__ = 'rafa'

import database
import semantics
from cut import wagner
import sys
import traceback
#from nltk.probability import FreqDist, ConditionalFreqDist
from pos_tagger import BackoffTagger
from estimator import prior_group_fdist, LaplaceEstimator, MleEstimator
from timer import Timer
from collections import defaultdict, Counter
from tree.default_tree import TreeCut
import re
import argparse
import shutil
import util
import os
import cPickle as pickle
from parsing import wordminer, queries


#-----------------------------------------
# Initializing module variables
#-----------------------------------------

# nouns_tree = None
# verbs_tree = None
# node_index = None

class Grammar(object):
    def __init__(self):
        self.base_structures = dict()
        self.probabilities   = dict()
        self.tag_dicts       = dict()
        self.verb_treecut = None
        self.noun_treecut = None

        # booleans
        self.lowres = None
        self.tagtype = None

    def read(self, path):
        grammar_dir = util.abspath(path)

        with open(os.path.join(grammar_dir, 'rules.txt')) as f:
            for line in f:
                fields = line.split()
                tags = fields[0]
                # map grammar rule (tags) to probability
                self.base_structures[tags] = float(fields[1])

        tagdicts_dir = os.path.join(grammar_dir, 'nonterminals')

        for fname in os.listdir(tagdicts_dir):
            if not fname.endswith('.txt'): continue

            with open(os.path.join(tagdicts_dir, fname)) as f:
                tag = fname.replace('.txt', '')
                words = []
                for line in f:
                    fields = line.split('\t')
                    try:
                        word, prob = fields
                        words.append(word)
                        self.probabilities[(tag, word)] = float(prob)
                    except:
                        sys.stderr.write("error inserting {} in the tag dictionary {}\n"
                                .format(fields, tag))
                self.tag_dicts[tag] = words

        with open(os.path.join(grammar_dir, 'verb-treecut.pickle'), 'rb') as f:
            self.verb_treecut = pickle.load(f)
        with open(os.path.join(grammar_dir, 'noun-treecut.pickle'), 'rb') as f:
            self.noun_treecut = pickle.load(f)
        with open(os.path.join(grammar_dir, 'params.pickle'), 'rb') as f:
            opts = pickle.load(f)
            self.lowres = opts.lowres
            self.tagtype = opts.tags


def select_treecut(pwset_id, abstraction_level):
    """ Load the noun and verb trees and calculates their respective tree
    cuts.  Stores  them in the module  variables, nouns_tree, verbs_tree  and
    node_index.  node_index points to the nodes in the tree.
    """

    global nouns_tree, verbs_tree, node_index

    nouns_tree, verbs_tree = semantics.load_semantictrees(pwset_id)

    cut = wagner.findcut(nouns_tree, abstraction_level)
    for c in cut: c.cut = True

    cut = wagner.findcut(verbs_tree, abstraction_level)
    for c in cut: c.cut = True

    flat = nouns_tree.flat() + verbs_tree.flat()

    node_index = dict()
    for node in flat:
        if node.key not in node_index:
            node_index[node.key] = node

#-------------------------------------------

class DictionaryTag:
    map = {10: 'month',
           20: 'fname',
           30: 'mname',
           40: 'surname',
           50: 'country',
           60: 'city',
           200: 'number',
           201: 'num+special',
           202: 'special',
           203: 'char',
           204: 'all_mixed'}

    _gaps = None

    @classmethod
    def get(cls, id):
        return DictionaryTag.map[id] if id in DictionaryTag.map else None

    @classmethod
    def gaps(cls):
        if not DictionaryTag._gaps:
            DictionaryTag._gaps = [ v for k, v in DictionaryTag.map.items() if DictionaryTag.is_gap(k)]

        return DictionaryTag._gaps

    @classmethod
    def is_gap(cls, id):
        return id > 90


def generalize(synset, noun_treecut, verb_treecut):
    """ Generalizes a synset based on a tree cut.
    @params:
        synset  - Required : a wordnet synset
        treecut - Required : instance of TreeCut

    Return a list of tags (str), each of which corresponds to
    synset key. Multiple tags are returned when synset has
    multiple parents.
    """

    if synset.pos() == 'v':
        treecut = verb_treecut
    elif synset.pos() == 'n':
        treecut = noun_treecut
    else:
        return None

    # an internal node is split into a node representing the class and other
    # representing the sense. The former's name starts with 's.'
    key = synset.name() if is_leaf(synset) else 's.' + synset.name()

    try:
        abstracts = treecut.abstract(key)
        # some subtrees are disconnected in wordnet (not accessible through
        # hyponyms()), but they are still included in WordNetTree
        # for instance, the subtree of atoll.n.01
        # in this case, treecut lookup will fail, cause the node won't be leaf,
        # as is_leaf suggests. the correct key is the one prefixed with 's.'
        if not abstracts:
            abstracts = treecut.abstract('s.'+key)
        tags = [node.key for node in abstracts]
    except:
        print key
        raise

    return tags


def is_leaf(synset):
    return not bool(synset.hyponyms())


def classify_gap(segment, lowres = False):
    if lowres:
        return DictionaryTag.map[segment.dictset_id]
    else:
        return DictionaryTag.map[segment.dictset_id] + str(len(segment.word))


def classify_by_pos(segment, lowres = False):
    """ Classifies  the  segment into number, word, character  sequence or
    special  character sequence.  Includes a POS tag if possible. Does not
    include a semantic symbol/tag.
    If segment is a word, the tag consists of its POS tag. For numbers and
    character sequences, a tag of the form categoryN is  retrieved where N
    is  the length  of the segment.  Words with unknown pos  are tagged as
    'unkwn'.
    Examples:
        love    -> vb
        123     -> number3
        audh    -> char4
        kripton -> unkwn
        !!!     -> special3
    Returns:
        str -- tag
    """

    if DictionaryTag.is_gap(segment.dictset_id):
        tag = classify_gap(segment, lowres)
    else:
        tag = segment.pos if segment.pos else 'unkwn'

    return tag


def classify_pos_semantic(segment, noun_treecut, verb_treecut, lowres = False):
    """ Fully classify the segment. Returns a list of tags possibly  containing
    semantic AND syntactic (part-of-speech) symbols. If the segment is a proper
    noun,  returns either month, fname,  mname,  surname,  city  or country, as
    suitable.
    For other  words, returns  tags of  the  form  pos_synset, where pos is  a
    part-of-speech tag and  synset is the corresponding  WordNet synset.  If no
    synset exists,  the symbol 'unkwn' is used. Aside from these classes, there
    is also numberN, charN, and specialN, for numbers, character sequences  and
    sequences of  special characters,  respectively, where N denotes the length
    of the segment.
    Examples:
        loved -> vvd_s.love.v.01
        paris -> city
        jonas -> mname
        cindy -> fname
        aaaaa -> char5

    Returns:
        list of str -- tags
    """
    if DictionaryTag.is_gap(segment.dictset_id):
        tags = [classify_gap(segment, lowres)]
    elif segment.pos in ['np', 'np1', 'np2', None] and segment.dictset_id in DictionaryTag.map:
        tags = [DictionaryTag.map[segment.dictset_id]]
    else:
        synset = semantics.synset(segment.word, segment.pos)
        # only tries to generalize verbs and nouns
        if synset is not None and synset.pos() in ['v', 'n']:
            tags = generalize(synset, noun_treecut, verb_treecut)
            tags = ['{}_{}'.format(segment.pos, tag ) for tag in tags]
        else:
            tags = [segment.pos]

    return tags


def classify_semantic_backoff_pos(segment, noun_treecut, verb_treecut, lowres = False):
    """  Returns a  list of  tags  containing  EITHER  semantic  OR syntactic
    (part-of-speech) symbols. If the segment is a proper noun, returns either
    month, fname, mname, surname, city or country, as suitable.
    For other words, returns  semantic tags if the  word is found in Wordnet;
    otherwise, falls  back to A POS tag. Aside from  these classes, there is
    also numberN, charN, and specialN, for numbers,  character sequences  and
    sequences of special characters, respectively, where N denotes the length
    of the segment.
    Examples:
        loved -> s.love.v.01
        paris -> city
        jonas -> mname
        cindy -> fname
        aaaaa -> char5
    Returns:
        list of str -- tags
    """
    if DictionaryTag.is_gap(segment.dictset_id):
        tags = [classify_gap(segment, lowres)]
    elif segment.pos in ['np', 'np1', 'np2', None] and segment.dictset_id in DictionaryTag.map:
        tags = [DictionaryTag.map[segment.dictset_id]]
    else:
        synset = semantics.synset(segment.word, segment.pos)
        # only tries to generalize verbs and nouns
        if synset is not None and synset.pos() in ['v', 'n']:
            tags = generalize(synset, noun_treecut, verb_treecut)
            tags = ['{}_{}'.format(segment.pos, tag) for tag in tags]
        else:
            tags = [segment.pos]

    return tags

def classify_word(segment, lowres = False):
    """ Most basic form of classification. Groups strings with respect to their
    length and nature (number, word, alphabetic characters, special characters).
    Examples:
        loved -> word5
        lovedparisxoxo -> word5word5char4
        12345 -> number5
        %$^$% -> special5
    Returns:
        str -- tag
    """
    word   = segment.word
    length = len(word)

    if DictionaryTag.is_gap(segment.dictset_id):
        return classify_gap(segment, lowres)

    # if re.match(r'\d+', word):
    #     return 'number' + str(length)
    # elif re.match(r'[^a-zA-Z0-9]+', word):
    #     return 'special' + str(length)
    else:
        return 'word' + str(length)

def classify(s, tagtype, noun_treecut, verb_treecut, lowres = False):
    if tagtype == 'pos':
        tag  = [classify_by_pos(s, lowres)]
    elif tagtype == 'backoff':
        tags = classify_semantic_backoff_pos(s, noun_treecut, verb_treecut, lowres)
    elif tagtype == 'word':
        tags = [classify_word(s, lowres)]
    else:
        tags = classify_pos_semantic(s, noun_treecut, verb_treecut,lowres)

    return tags


def stringify_pattern(tags):
    return ''.join(['({})'.format(tag) for tag in tags])


def patterns(segments, tagtype, noun_treecut, verb_treecut, lowres=False):
    segments = expand_gaps(segments)

    tag_lists = [[]]  # each tag list is a pattern (e.g., ['pp', 'love', 'ppy'])
    for s in segments:  # semantic tags
        tags = classify(s, tagtype, noun_treecut, verb_treecut, lowres)
        # remove duplicates (in case repeated nodes generalize to the same abstract)
        tags = set(tags)
        # do a full join of tag_lists with tags
        tag_lists = [tag_list + [tag] for tag in tags for tag_list in tag_lists]

    return tag_lists

def sample(db, noun_treecut, verb_treecut):
    """ I wrote this function to output data for a table
    that shows words, the corresponding synsets, and their generalizations."""

    while db.hasNext():
        segments = db.nextPwd()
        for s in segments:
            tag = classify(s, noun_treecut, verb_treecut)
            if re.findall(r'.+\..+\..+', tag): # test if it's a synset
                synset = semantics.synset(s.word, s.pos)
            else:
                synset = None
            print "{}\t{}\t{}\t{}".format(s.password, s.word, tag, synset)


def expand_gaps(segments):
    """
    If the password has segments of the type "MIXED_ALL" or "MIXED_NUM_SC",
    break them into "alpha", "digit" and "symbol" segments.
    This function provides more resolution in the treatment of non-word segments.
    This should be done in the parsing phase, so this is more of a quick fix.
    """
    temp = []

    for s in segments:
        if s.dictset_id == 204 or s.dictset_id == 201:
            temp += segment_gaps(s.word)
        else:
            temp.append(s)

    return temp


def segment_gaps(pwd):
    """
    Segments a string into alpha, digit and "symbol" fragments.
    """
    regex = r'\d+|[a-zA-Z]+|[^a-zA-Z0-9]+'
    segments = re.findall(regex, pwd)
    segmented = []
    for s in segments:
        if s[0].isalpha():
            f = Fragment(0, 203, s)
        elif s[0].isdigit():
            f = Fragment(0, 200, s)
        else:
            f = Fragment(0, 202, s)

        segmented.append(f)

    return segmented


def print_result(password, segments, tags, pattern):
    for i in range(len(segments)):
        print "{}\t{}\t{}\t{}".format(password, segments[i].word, tags[i], pattern)


def get_treecuts(pwset_id, estimator, abslevel, sample=None):
    """
    Assign counts to nodes of noun and verb WordNet trees based on occurrence
    in a password list, then calculate an abstract tree cut using MDL.
    If estimator is 'laplace', then all leaves will have a prior count of 1.
    Return a tuple like (noun_treecut, verb_treecut).
    """
    noun_tree, verb_tree = semantics.load_semantictrees(pwset_id, sample)

    if estimator == 'laplace':
        # increase the count of each leaf by one and propagate values to the top
        # this is equivalent to having a uniform prior (Laplace smoothing)
        for leaf in noun_tree.leaves(): leaf.value += 1
        for leaf in verb_tree.leaves(): leaf.value += 1

        noun_tree.updateValue()
        verb_tree.updateValue()

    verb_treecut = TreeCut(verb_tree, wagner.findcut(verb_tree, abslevel))
    noun_treecut = TreeCut(noun_tree, wagner.findcut(noun_tree, abslevel))

    return noun_treecut, verb_treecut


def main(db, pwset_id, dryrun, verbose,
    basepath, tagtype, lowres, abslevel, estimator):
    """
    There are 2 levels of ambiguity resolution:
        1. _sense_: the most frequent sense is selected.
        2. _subtree_: if a sense belongs to multiple subtrees, the count is split.
    """
#    tags_file = open('grammar/debug.txt', 'w+')

    patterns_dist  = Counter()  # distribution of patterns
    segments_dist  = defaultdict(lambda : Counter())

    # get tree and treecut
    print "Loading WordNet trees and calculating tree cuts..."

    noun_treecut, verb_treecut = get_treecuts(pwset_id, estimator,
        abslevel, db.sample_ids())

    print "Tree cut for tree of nouns has {} nodes".format(len(noun_treecut.cut))
    print "Tree cut for tree of verbs has {} nodes".format(len(verb_treecut.cut))

    if estimator == 'laplace':
        # initialize frequency distributions by including all possible symbols.
        # with MLE, this isn't necessary, as unseen words and tags do not appear
        # in the grammar
        postagger = BackoffTagger()
        segments_dist.update(prior_group_fdist(noun_treecut, 'n', tagtype, postagger))
        segments_dist.update(prior_group_fdist(verb_treecut, 'v', tagtype, postagger))


        parsingdb = wordminer.connectToDb()
        for dictset_id, dict_name in DictionaryTag.map.items():
            if dictset_id > 90: continue
            dictset = queries.getDictionary(parsingdb, [dictset_id])
            for word in dictset.keys():
                segments_dist[dict_name][word] = 1


    counter = 0
    total   = db.pwset_size if not db.is_sample() else len(db.sample_ids())

    while db.hasNext():
        segments = db.nextPwd()
        password = ''.join([s.word for s in segments])
        tag_lists = [[]]  # each tag list is a pattern (e.g., ['pp', 'love', 'ppy'])

        segments = expand_gaps(segments)

        for s in segments:  # semantic tags
            tags = classify(s, tagtype, noun_treecut, verb_treecut, lowres)
            # remove duplicates (in case repeated nodes generalize to the same abstract)
            tags = set(tags)
            # do a full join of tag_lists with tags
            tag_lists = [tag_list + [tag] for tag in tags for tag_list in tag_lists]

            for tag in tags:
                try:
                    segments_dist[tag][s.word] += 1.0/len(tags)
                except:
                    print tag, s.word
                    raise

        for tag_list in tag_lists:
            pattern = stringify_pattern(tag_list)
            patterns_dist[pattern] += 1

            # outputs the classification results for debugging purposes
            if verbose:
                print_result(password, segments, tag_list, pattern)

        counter += 1
        if counter % 100000 == 0:
            print "{} passwords processed so far ({:.2%})... ".format(counter, float(counter)/total)

    pwset_id = str(pwset_id)

    if dryrun:
        return

    # remove previous grammar
    try:
        shutil.rmtree(basepath)
    except OSError: # in case the above folder does not exist
        pass

    # recreate the folders empty
    os.makedirs(os.path.join(basepath, 'nonterminals'))

    with open(os.path.join(basepath, 'rules.txt'), 'w+') as f:
        samplesize = sum(patterns_dist.values())
        vocabsize = len(patterns_dist.keys())

        if estimator == 'laplace':
            est = LaplaceEstimator(samplesize, vocabsize, 1)
        else:
            est = MleEstimator(samplesize)

        for pattern, freq in patterns_dist.most_common():
            f.write('{}\t{}\n'.format(pattern, est.probability(freq)))

    for tag in segments_dist.keys():
        samplesize = sum(segments_dist[tag].values())
        vocabsize = len(segments_dist[tag].keys())

        if estimator == 'laplace':
            est = LaplaceEstimator(samplesize, vocabsize, 1)
        else:
            est = MleEstimator(samplesize)

        with open(os.path.join(basepath, 'nonterminals', str(tag) + '.txt'), 'w+') as f:
            for lemma, freq in segments_dist[tag].most_common():
                f.write("{}\t{}\n".format(lemma.encode('utf-8'), est.probability(freq)))

    # if we're sampling, dump list of password ids in the sample
    if db.is_sample():
        with open(os.path.join(basepath, "sample-ids.txt"), 'w+') as f:
            for id_ in db.sample_ids():
                f.write(str(id)+'\n')

    # pickle the tree cuts
    with open(os.path.join(basepath, "noun-treecut.pickle"), 'wb') as f:
        pickle.dump(noun_treecut, f, -1)

    with open(os.path.join(basepath, "verb-treecut.pickle"), 'wb') as f:
        pickle.dump(verb_treecut, f, -1)

    with open(os.path.join(basepath, "params.pickle"), 'wb') as f:
        pickle.dump(options(), f, -1)


def options():
    parser = argparse.ArgumentParser()

    parser.add_argument('password_set', default=1, type=int,
        help='The id of the collection of passwords to be processed')
    parser.add_argument('-s', '--sample', default=None, type=int,
        help="Sample size")
    parser.add_argument('--estimator', default='mle', choices=['mle', 'laplace'])
    parser.add_argument('-r', '--random', action='store_true',
        help="To be used with -s. Enables random sampling.")
    parser.add_argument('-d', '--dryrun', action='store_true',
        help="Does not override the grammar folder. ")
    parser.add_argument('-v', '--verbose', action='store_true',
        help="Verbose mode")
    parser.add_argument('-l', '--lowres', action='store_true',
        help="Toggles low resolution treatment of non-word segments. For "\
            "example: instead of (number5) tags it as (number)")
    parser.add_argument('-e', '--exceptions', type=argparse.FileType('r'),
        help="A file containing a list of password ids " \
        "to be ignored. One id per line. Depending on the size of this file " \
        "you might need to increase MySQL's variable max_allowed_packet.")
    # parser.add_argument('--onlypos', action='store_true', \
    #     help="Turn this switch if you want the grammar to have only "\
    #     "POS symbols, no semantic tags (synsets)")
    parser.add_argument('-a', '--abstraction', type=int, default=5000,
        help='Abstraction Level. An integer > 0, correspoding to the '\
             'weighting factor in Wagner\'s formula')
    parser.add_argument('-p', '--path', default='grammar',
        help="Path where the grammar files will be output")
    parser.add_argument('--tags', default='pos_semantic',
        choices=['pos_semantic', 'pos', 'backoff', 'word'])

    return parser.parse_args()


# TODO: Option for online version (calculation of everything on the fly) and from db
if __name__ == '__main__':

    opts = options()

    exceptions = []

    if opts.exceptions:
        for l in opts.exceptions:
            exceptions.append(int(l.strip()))
        opts.exceptions.close()

    # if not opts.tags == 'pos':
    #     select_treecut(opts.password_set, opts.abstraction)

    try:
        with Timer('grammar generation'):
            #db = PwdDb(sample=10000, random=True)
            print 'Instantiating database...'
            db = database.PwdDb(opts.password_set, samplesize=opts.sample,
                random=opts.random, exceptions=exceptions)
            try:
                main(db, opts.password_set, opts.dryrun,
                    opts.verbose, opts.path, opts.tags, opts.lowres,
                    opts.abstraction, opts.estimator)
            except KeyboardInterrupt:
                db.finish()
                raise
    except:
        e = sys.exc_info()[0]
        traceback.print_exc()
        sys.exit(1)
