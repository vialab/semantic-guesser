#!/usr/bin/env python

'''
Created on 2013-06-28

@author: rafa
'''
from __future__ import print_function
import argparse
import guesser
from parsing import wordminer as parser
from grammar import Grammar, patterns, stringify_pattern
import database
from pos_tagger import BackoffTagger
import os
import sys
import util
import cPickle as pickle

# Global variables
db = parser.connectToDb()
dictionary = parser.getDictionary(db, parser.dict_sets)
pos_tagger = BackoffTagger()


def options():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='?', type=argparse.FileType('r'),
        help='a list of clear text passwords.', default=sys.stdin)
    parser.add_argument('-g', '--grammar', default='grammar',
        help="grammar path.")
    parser.add_argument('-s', '--summary', action='store_true',
        help="output stats line with percentage guessable")
    parser.add_argument('-b', '--print_base_struct', action='store_true',
        help="include base_struct field in the output")
    parser.add_argument('-m', '--print_segmentation', action='store_true',
        help="include segmentation field in the output")

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
    except:
        print("Warning: caught unknown error in addTheGaps -- resultSet=",
                resultSet, "password", password, file=sys.stderr)

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


def probability(grammar, base_struct, base_struct_str, segments):
    p = grammar.base_structures[base_struct_str]

    for i, tag in enumerate(base_struct):
        p_t = None  # terminal probability
        # finds the terminal probability
        for terminal in grammar.tag_dicts[tag]:
            if terminal == segments[i].word:
                p_t = grammar.probabilities[(tag, terminal)]
                break

        p *= p_t

    return p


def is_guessable(grammar, base_struct, base_struct_str, segments):
    """ Check if a password is guessable under the current grammar.
    @params
    base_struct - list - the password's pattern, a list of tags, one for each
        of its segments
    base_struct_str - str - a string representation of the pattern
    segments - list - a list of the segments the password consists of
    """
    answer = True

    if base_struct_str in grammar.base_structures:
        for i, segment in enumerate(segments):
            tag = base_struct[i]
            if segment.word not in grammar.tag_dicts[tag]:
                answer = False
                break
    else:
        answer = False

    return answer


def argmax_probability(password, grammar):
    """Return the segmentation and the base structure that generate _password_ with
    the highest probability. Retun None if the grammar isn't capable of generating
    _password_.

    @params
    password - str
    grammar  - Grammar

    @return tuple (password, segmentation, str(base_struct), p) or None
    segmentation -> list of Fragment
    """
    segmentations = segment(password, dictionary, db)

    guessable = False

    # of all base structures that generate password, the one that generates it first.
    max_base_struct = None  # a tuple (password, segmentation, base_struct_str, probability)

    for s in segmentations:

        postags = pos_tagger.tag([ f.word for f in s if f.dictset_id <= 90])
        for j in range(len(s)):
            if s[j].dictset_id > 90:
                s[j].pos = None
            else:
                s[j].pos = postags.pop(0)[1]

        # a base_struct is a tag list e.g., ['nn1', 'n.love.01']
        base_structs = patterns(s, grammar.tagtype,
            grammar.noun_treecut, grammar.verb_treecut, grammar.lowres)


        for base_struct in base_structs:
            base_struct_str = stringify_pattern(base_struct)

            if is_guessable(grammar, base_struct, base_struct_str, s):
                p = probability(grammar, base_struct, base_struct_str, s)
                guessable = True

                if max_base_struct is None \
                    or p > max_base_struct[3]:
                    max_base_struct = (password, s, base_struct_str, p)

    return None if not guessable else max_base_struct


def main(grammar, file, print_summary, print_basestruct, print_segmentation):
    guessable_count = 0

    i = 0
    for l in file:
        password = l.rstrip()

        if not password: continue

        argmax = argmax_probability(password, grammar)

        if argmax:
            password, seg, base_struct, p = argmax
            print(password + '\t', end='')
            if print_segmentation:
                print(str(seg) + '\t', end='')
            if print_basestruct:
                print(base_struct + '\t', end='')
            print(p)
            # print "{}\t{}\t{}\t{}".format(*)
            guessable_count += 1

        i += 1

    # print # of guessable passwords
    if print_summary:
        print("{} guessable passwords out of {} ({:.2%})"
            .format(guessable_count, i, float(guessable_count) / i))


if __name__ == '__main__':
    opts = options()

    g = Grammar()
    g.read(opts.grammar)

    main(g, opts.file, opts.summary, opts.print_base_struct, opts.print_segmentation)
