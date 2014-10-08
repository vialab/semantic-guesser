#!/usr/bin/env python

"""
Script to retrieve information from the grammar.
"""
import multiprocessing

__author__ = 'rafa'

import argparse
from nltk.corpus import wordnet as wn
from Queue import Queue
import rank_rules
import re
import os
import math

RULES_FILE = os.path.join(".", "grammar", "rules.txt")
CATEGORIES_FILE = os.path.join(".", "grammar", "categories.txt")
GRAMMAR_FOLDER = os.path.join(".", "grammar")
TERMINALS_FOLDER = os.path.join(GRAMMAR_FOLDER, "seg_dist")

# captures synsets inside grammar categories that also have POS tag
# e.g., nn1_s.ball.n.01
GRAMMAR_SYNSET_REGEX = r'^[a-zA-Z0-9-]+\_(?:s\.)*([a-z_-]+\.[a-z]\.\d+)'
# matches a synset name, e.g. animal.n.01
SYNSET_REGEX = r'[a-z_-]+\.[a-z]\.\d+'


# class SemanticTag:
#     def __init__(self, synset_name):
#         self.synset_name = synset_name

class Tag:
    def __init__(self, tag):
        self.tag = tag

    def __str__(self):
        return self.tag

    def __repr__(self):
        return self.tag

    def __eq__(self, other):
        return self.tag == other.tag


class WildCardTag:
    def __init__(self):
        self.tag = '*'

    @staticmethod
    def check(s):
        return s == '*'

    def __eq__(self, other):
        return True


class SynsetTag(Tag):
    regex = r'[a-z_-]+\.[a-z]\.\d+'

    def __init__(self, tag):
        self.tag = tag
        self.synset_name = re.findall(SynsetTag.regex, tag)[0]

    @staticmethod
    def check(s):
        return bool(re.match(SynsetTag.regex, s))


class POSSynsetTag(SynsetTag):
    regex = r'^([a-zA-Z0-9-]+)_(?:s\.)*([a-z_-]+\.[a-z]\.\d+)'

    def __init__(self, tag):
        matches = re.findall(POSSynsetTag.regex, tag)
        self.tag = tag
        self.pos = matches[0][0]
        self.synset_name = matches[0][1]

    @staticmethod
    def check(s):
        return bool(re.match(POSSynsetTag.regex, s))


class POSTag(Tag):
    def __init__(self, tag):
        self.tag = tag


class CustomSemanticTag(Tag):

    regexes = [r'^number\d+$', r'^char\d+$', r'^special\d+$', r'^surname$', r'^[fm]name$', r'^country$', r'^city$']

    def __init__(self, tag):
        self.tag = tag

    @staticmethod
    def check(s):
        for r in CustomSemanticTag.regexes:
            if re.findall(r, s):
                return True

        return False


def parse_rule(rule):
    regex = r'\(([^()]+)\)'

    segments = re.findall(regex, rule)
    tags = []
    for s in segments:
        if POSSynsetTag.check(s):
            tags.append(POSSynsetTag(s))
        elif SynsetTag.check(s):
            tags.append(SynsetTag(s))
        elif CustomSemanticTag.check(s):
            tags.append(CustomSemanticTag(s))
        elif WildCardTag.check(s):
            tags.append(WildCardTag())
        else:
            tags.append(POSTag(s))

    return tags


def descendants(s):
    """Retrieves all the synsets that descend from s.
    s - synset
    """
    result = []
    q = Queue()
    q.put(s)

    while not q.empty():
        t = q.get()
        result.append(t)
        for c in t.hyponyms():
            q.put(c)

    return result[1:] if len(result) > 0 else []


def extract_synset(s):
    """Given a category with other symbols in addition to synset names,
    return the synset names if they exist, otherwise None.
    s - a category like nn1 or nn1_s.ball.n.01
    return the synset name, like ball.n.01
    """
    matches = re.findall(GRAMMAR_SYNSET_REGEX, s)
    return None if not matches else matches[0]


def is_synset(s):
    return bool(re.match(SYNSET_REGEX, s))


def descend(p):
    """Given a pattern p, expands the synsets into all their descendants.
    p - a list of categories, like [nn1, nn1_animal.n.01, pp]
    return a 2d list of categories like [nn1, [butterfly.n.01, monkey.n.01...], pp]
    """
    result = []
    for c in p:
        if is_synset(c):
            result.append(descendants(wn.synset(c)))
        else:
            # if c does not match a synset, it might have a synset in it (e.g., nn1_animal.n.01)
            matches = re.findall(GRAMMAR_SYNSET_REGEX, c)
            if matches:
                result.append(descendants(c))
            else:
                # there is not synset in c (e.g., POS tag), then just preserve it
                result.append(c)

    return result


#TODO: Update the documentation
def descend_tags(p):
    """Given a pattern p, expands the synsets into all their descendants.
    p - a list of categories, like [nn1, nn1_animal.n.01, pp]
    return a 2d list of categories like [nn1, [butterfly.n.01, monkey.n.01...], pp]
    """
    result = []
    for c in p:
        if isinstance(c, SynsetTag) or isinstance(c, POSSynsetTag):
            result.append([d.name for d in descendants(wn.synset(c.synset_name))])
        else:
            result.append(c.tag)

    return result


def load_categories():
    categories = []
    with open('grammar/categories.txt') as f:
        for line in f:
            fields = line.split()
            cat = fields[0]
            prob = float(fields[1])
            categories.append((cat, prob))

    return categories


def group(s, categories):
    """Aggregates all the occurrences of or under the synset s present in a list of categories.
    s - the name of the synset (e.g., animal.n.01)
    categories - list of tuples of the form [('nn1_s.larva.n.01', 9.2249e-08), ...]
    """
    targets = [d.name for d in descendants(wn.synset(s))]  # the names of all synsets descending from s
    targets += [s]  # add s itself to the list of targets

    # matches synsets names, like NN_s.ball.n.01
    regex = GRAMMAR_SYNSET_REGEX

    # stores all occurrences of s or descendants of s and their probs, for aggregation later.
    matches_table = []

    # finds occurrences of s or its descendants in the list of categories
    for cat, prob in categories:
        matches = re.findall(regex, cat)
        if not matches:
            continue
        else:
            synset_name = matches[0]
            if synset_name in targets:
                matches_table.append((cat, prob))

    return matches_table


def cli_match(p):
    """ Prints matches of a pattern in the grammar.
    p - string of the form (pp1)(love.n.01)(pp2)
    """
    matches = match_pattern(p)
    for rule, prob in matches:
        print "{}\t{}".format(rule, prob)


def match_pattern(p):
    """ Finds matches of a pattern in the grammar.
    p - string of the form (pp1)(love.n.01)(pp2)
    return a list of tuples of the form (pattern, probability)
    """

    def worker(rows, out_queue):
        output = []

        for r in rows:
            fields = r.rstrip().split()
            p2 = fields[0]
            p2 = parse_rule(p2)  # p2 is a list of tags

            if len(p2) != len(p1):
                continue

            # compares reference with test category by category
            match = True
            for i in range(len(p1)):
                a = p1[i]
                a_desc = p1_descendants[i]
                b = p2[i]

                if a == b:
                    continue
                elif isinstance(a, SynsetTag) and isinstance(b, SynsetTag):
                    if b.synset_name == a.synset_name or b.synset_name in a_desc:
                        continue

                match = False
                break

            if match:
                output.append(tuple(fields))

        out_queue.put(output)
        return

    p1 = parse_rule(p)  # p1 is a list of tags
    p1_descendants = descend_tags(p1)

    lines = []

    # p1 is the input pattern (reference), p2 is the pattern read from file (test)
    # each iteration looks for a match
    with open(RULES_FILE) as f:
        for line in f:
            lines.append(line)

    output_queue = multiprocessing.Queue()
    n_processes = 8

    chunksize = int(math.ceil(len(lines)/float(n_processes)))

    procs = []
    for k in range(n_processes):
        p = multiprocessing.Process(target=worker, args=(lines[k*chunksize:(k+1)*chunksize], output_queue))
        procs.append(p)
        p.start()

    result_array = []
    for k in range(n_processes):
        result_array += output_queue.get()

    for p in procs:
        p.join()

    return result_array


def cli_descendants(s):
    for s in descendants(wn.synset(s)):
        print s.name


def cli_group(s, nocache):
    """ Prints all the occurrences of or under the synset s, and their consolidated probability.
    s - the name of the synset (e.g., animal.n.01)
    """
    # loads the pre-computed category probabilities or computes them now
    categories = rank_rules.rank() if nocache else load_categories()

    total_prob = 0

    g = group(s, categories)
    for synset, prob in g:
        print "{}\t{}".format(synset, prob)
        total_prob += prob

    print "{}\n{}\t{}".format('-' * 40, s, total_prob)


def cli_terminals(c):
    terminal_files = [f for f in os.listdir(GRAMMAR_FOLDER) if os.path.isfile(os.path.join(GRAMMAR_FOLDER, f))]


def options():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="function")

    # parser for the command descendants
    parser_desc = subparsers.add_parser("descendants", help="Prints all descendants of a synset")
    parser_desc.add_argument("synset", type=str, help="Full name of the synset, like ball.n.01")

    # parser for the command group
    parser_group = subparsers.add_parser("group", help="Prints the probability of a synset, aggregating the descendants"
                                                       " if necessary")
    parser_group.add_argument("synset", type=str, help="Full name of the synset, like ball.n.01")
    parser_group.add_argument("-n", "--nocache", action="store_true", help="Computes the probabilities of categories"
                                                                           " from scratch (takes time); otherwise, "
                                                                           " reads from the file categories.txt")

    # parser for the command pattern
    parser_match = subparsers.add_parser("match", help="Print matches of a pattern in the grammar.")
    parser_match.add_argument("pattern", type=str, help="Patterns should follow the format '(tag1)(tag2)...'"
                                                        "For example: (pp1)(love.n.01)(*)")

    # parser for the command pattern
    parser_terminals = subparsers.add_parser("terminals", help="Prints all terminal strings deriving from the category"
                                                               " informed.")
    parser_terminals.add_argument("category", type=str, help="A semantic or POS tag present in the grammar.")

    return parser.parse_args()


def test():
    pass
    # print parse_rule("(mname)(nn1_s.team.n.01)(char1)")
    # print cli_match("(nn1_s.rock.n.01)(ppy)")
    #print extract_synset("nn1_password.n.01")


if __name__ == "__main__":
    # test()
    try:
        opts = options()
        if opts.function == "descendants":
            cli_descendants(opts.synset)
        elif opts.function == "group":
            cli_group(opts.synset, opts.nocache)
        elif opts.function == "match":
            cli_match(opts.pattern)
        elif opts.function == "terminals":
            cli_terminals(opts.category)
    except IOError:
        pass
