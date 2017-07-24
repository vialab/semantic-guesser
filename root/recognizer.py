'''
Created on 2013-06-28

@author: rafa
'''

import argparse
import guesser
from parsing import wordminer as parser
import grammar
import database
from pos_tagger import BackoffTagger
import os
import sys
import util
import cPickle as pickle

base_structures = dict()
tag_dicts = dict()
probabilities = dict() # key -> (tag, word)
noun_treecut = None
verb_treecut = None

def options():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=argparse.FileType('r'),
        help='a list of clear text passwords.')
    parser.add_argument('-g', '--grammar', default='grammar',
        help="grammar path.")

    return parser.parse_args()


def segment(password, dictionary, db):
    permutations = parser.permuteString(password.lower())
    words = list()
    for x in permutations:
        if x[0] in dictionary:
            words.append(x)

    candidates = parser.generateCandidates(words, password)
    # candidates comes pretty raw. we need a representation that
    # stores dictset_id, pos, etc... for semantic classification
    candidates = transform(candidates, dictionary)

    for c in candidates:
        processGaps(db, c, password)

    if candidates == []:
        candidates = [processGaps(db, [], password)]

    return [ [s[0] for s in c] for c in candidates]


def processGaps(db, segmentation, password):
    if (segmentation == []):
        dynDictionaryID = parser.tagChunk(password)
        segment = database.Fragment(0, dynDictionaryID, password)
        segmentation.append((segment, 0, len(password)))
        return segmentation

    lastEndIndex = 0
    nextStartIndex = 0
    i = 0
    try:
        for x in segmentation:
            (xw, xs, xe) = x
            nextStartIndex = xs
            if (nextStartIndex > lastEndIndex):
                # find the gap, see if it is a #/sc chunk
                segmentation = addInTheGapsHelper(db, segmentation, i,
                        password, lastEndIndex, nextStartIndex)
            lastEndIndex = xe
            i = i + 1
        if (len(password) > lastEndIndex):
                segmentation = addInTheGapsHelper(db, segmentation,
                        i, password, lastEndIndex, len(password))
    except :
        print ("Warning: caught unknown error in addTheGaps -- resultSet=",
                resultSet, "password", password)

    return segmentation


def addInTheGapsHelper(db, segmentation, i, password, lastEndIndex, nextStartIndex):
    # attention for the strip() call! space info is lost! who cares?!
    gap = password[lastEndIndex:nextStartIndex].strip()

    dynDictionaryID = parser.tagChunk(gap)

    if ((len(gap) > 0) and (dynDictionaryID > 0)):
        segment = database.Fragment(0, dynDictionaryID, gap)
        segmentation.insert(i, (segment, lastEndIndex, nextStartIndex))

    return segmentation


def transform(seg_candidates, dictionary):
    """ Takes a segmentation candidate from testWordMiner.generateCandidates and
    transforms into simple list of list of tuples like (segment, sindex, eindex)"""

    result = []

    for (segmentations, coverage) in seg_candidates:
        for s in segmentations:
            tmp = []
            for (segment, s_index, e_index) in s:
                tmp.append((database.Fragment(0, dictionary[segment][0], segment),
                    s_index, e_index))
            result.append(tmp)

    return result


def probability(base_struct, tags, segments):
    p = base_structures[base_struct]

    for i, tag in enumerate(tags):
        p_t = None  # terminal probability
        # finds the terminal probability
        for terminal in tag_dicts[tag]:
            if terminal == segments[i].word:
                p_t = probabilities[(tag, terminal)]
                break

        p *= p_t

    return p


def is_guessable(pattern, pattern_label, segments):
    """ Check if a password is guessable under the current grammar.
    @params
    pattern - list - the password's pattern, a list of tags, one for each
        of its segments
    pattern_label - str - a string representation of the pattern
    segments - list - a list of the segments the password consists of
    """
    answer = True

    if pattern_label in base_structures:
        for i, segment in enumerate(segments):
            tag = pattern[i]
            if segment.word not in tag_dicts[tag]:
                answer = False
                break
    else:
        answer = False

    return answer


def load_grammar(grammar_path, base_structures, tag_dicts):

    grammar_dir = util.abspath(grammar_path)

    with open(os.path.join(grammar_dir, 'rules.txt')) as f:
        for line in f:
            fields = line.split()
            tags = fields[0]
            base_structures[tags] = float(fields[1])  # maps grammar rule (tags) to probability

    tagdicts_dir = os.path.join(grammar_dir, 'nonterminals')

#     with Timer('Loading tag dictionaries'):
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
                    probabilities[(tag, word)] = float(prob)
                except:
                    sys.stderr.write("error inserting {} in the tag dictionary {}\n"
                            .format(fields, tag))
            tag_dicts[tag] = words

    global noun_treecut, verb_treecut


    with open(os.path.join(grammar_dir, 'verb-treecut.pickle'), 'rb') as f:
        verb_treecut = pickle.load(f)
    with open(os.path.join(grammar_dir, 'noun-treecut.pickle'), 'rb') as f:
        noun_treecut = pickle.load(f)


def main(base_structures, tag_dicts, file, grammar_params):
    db = parser.connectToDb()
    dictionary = parser.getDictionary(db, parser.dict_sets)
    pos_tagger = BackoffTagger()

    guessable_count = 0

    i = 0
    for l in file:
        password = l.rstrip()

        if not password : continue

        segmentations = segment(password, dictionary, db)

        guessable = False

        for s in segmentations:

            postags = pos_tagger.tag([ f.word for f in s if f.dictset_id <= 90])
            for j in range(len(s)):
                if s[j].dictset_id > 90:
                    s[j].pos = None
                else:
                    s[j].pos = postags.pop(0)[1]

            # a pattern is a tag list e.g., ['nn1', 'n.love.01']
            patterns = grammar.patterns(s, grammar_params.tags,
                noun_treecut, verb_treecut, grammar_params.lowres)

            for pattern in patterns:
                pattern_label = grammar.stringify_pattern(pattern)
                if is_guessable(pattern, pattern_label, s):
                    guessable = True
                    print "{}\t{}\t{}".format(password, pattern_label,
                        probability(pattern_label, pattern, s))


        guessable_count += int(guessable)
#         print "{}\t{}".format(password, guessable)

        i += 1
#        if i >= 1000: break

    # print # of guessable passwords
    print "{} guessable passwords out of {} ({:.2%})" \
        .format(guessable_count, i, float(guessable_count)/i)

if __name__ == '__main__':
    opt = options()
    load_grammar(opt.grammar, base_structures, tag_dicts)

    with open(os.path.join(opt.grammar, 'params.pickle'), 'rb') as f:
        grammar_params = pickle.load(f)

    main(base_structures, tag_dicts, opt.file, grammar_params)
