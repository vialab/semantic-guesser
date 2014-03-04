"""
Script to retrieve information from the grammar.
"""

__author__ = 'rafa'

import argparse
from nltk.corpus import wordnet as wn
from Queue import Queue
import rank_rules
import re


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

    return result[1:]


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
    regex = r'^[a-zA-Z-]+\_(?:s\.)*([a-z_-]+\.[a-z]\.\d+)'

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

    print "{}\n{}\t{}".format('-'*40, s, total_prob)


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

    return parser.parse_args()


if __name__ == "__main__":
    opts = options()
    if opts.function == "descendants":
        cli_descendants(opts.synset)
    elif opts.function == "group":
        cli_group(opts.synset, opts.nocache)
        # TODO: Continue writing the cli_group function.