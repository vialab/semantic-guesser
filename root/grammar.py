"""
This script generates a context-free grammar
that captures the semantic patterns of a list of
passwords.

It's based on Weir (2009)*.

*http://dl.acm.org/citation.cfm?id=1608146

Created on Apr 18, 2013

"""

__author__ = 'rafa'

from database import PwdDb
import semantics
from cut import wagner
import sys
import traceback

nouns_tree = None
verbs_tree = None


def generalize(synset):
    """ Generalizes a synset based on a tree cut. """

    if synset.pos == 'n':
        tree = nouns_tree
    elif synset.pos == 'v':
        tree = verbs_tree
    else:
        return None

    # an internal node is split into a node representing the class and other
    # representing the sense. The former's name starts with 's.'
    key = synset.name if is_leaf(synset) else 's.' + synset.name

    # given the hypernym path of a synset, selects the node that belongs to the cut
    for node in tree.path(key):
        if node.cut:
            return node.key

    return None


def is_leaf(synset):
    return not bool(synset.hyponyms())


def classify(fragment):
    synset = semantics.synset(fragment.word, fragment.pos)

    if synset is not None:
        g = generalize(synset)
        print "{}\t{}".format(synset, g)


def main():
    global verbs_tree
    global nouns_tree

    nouns_tree = semantics.load_semantictree('n')
    cut = wagner.findcut(nouns_tree, 5000)
    for c in cut:
        c.cut = True

    verbs_tree = semantics.load_semantictree('v')
    cut = wagner.findcut(verbs_tree, 5000)
    for c in cut:
        c.cut = True

    db = PwdDb(size=200)
    while db.hasNext():
        password = db.nextPwd()
        for fragment in password:
            classify(fragment)


# TODO: Option for online version (calculation of everything on the fly) and from db
if __name__ == '__main__':
    try:
        main()
    except:
        e = sys.exc_info()[0]
        traceback.print_exc()
        sys.exit(1)