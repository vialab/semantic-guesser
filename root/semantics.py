"""
This module contains functions for semantic classification of password fragments.
The main function classifies a sample and outputs the WordNet hierarchy with the nodes
containing the frequency in the sample, in JSON format.

@author: Rafa
"""

import database
from tagset_conversion import TagsetConverter
from nltk.corpus import wordnet as wn
from tree.default_tree import DefaultTree 
from tree.wordnet import WordNetTree
from timer import Timer
import cPickle as pickle
import argparse
import os
import sys

tag_converter = TagsetConverter()


def synset(word, pos):
    """Given a POS-tagged word, determines its synset by
    converting the CLAWS tag to WordNet tag and querying
    the associated synset from WordNet.

    If more than one synset is retrieved, return the first,
    which is, presumably, the most frequent.
    More on this at: http://wordnet.princeton.edu/wordnet/man/cntlist.5WN.html
    
    If the fragment has no POS tag or no synset is found in
    WordNet for the POS tag, None is returned.

    - pos: a part-of-speech tag from the CLAWS7 tagset

    """
    if pos is None:
        return None

    wn_pos = tag_converter.clawsToWordNet(pos)

    if wn_pos is None:
        return None

    synsets = wn.synsets(word, wn_pos)

    return synsets[0] if len(synsets) > 0 else None


def populate(tree, samplesize, pwset_id):
    """ Given a POS-specific tree representation
    of WordNet (an instance of WordNetTree), updates the
    frequency of each node according to its occurrence
    in a sample of the passwords.

    samplesize - if None, reads the entire database

    """

    with Timer("Loading records from db"):
        db = database.PwdDb(pwset_id, sample=samplesize)

    tree_hashtable = tree.hashtable()
    synset_dist    = {}

    i = 0;
    while db.hasNext():
        i += 1
        if i % 1000000 == 0:
            print "{} passwords have been read...".format(i)
        fragments = db.nextPwd()  # list of Fragment
#
        for f in fragments:
            # we don't want dynamic dict. entries
            if f.is_gap():
                continue

            # best effort to get a synset matching the fragment's pos
            synset_ = synset(f.word, f.pos)

            # check if the synset returned has the pos we want
            if synset_ is not None and synset_.pos == tree.pos:
                if synset_ not in synset_dist:
                    synset_dist[synset_] = 1
                else:
                    synset_dist[synset_] += 1
    
    print "All passwords read."

    with Timer("Updating tree"):
        #tree.increment_synset(synset_)
        for syn, count in synset_dist.items():
            increment_synset_count(tree, syn, tree_hashtable, count)

    return tree

def increment_synset_count(tree, synset, hashtable, count=1):
    """ Given  a  WordNetTree, increases the  count  (frequency)
    of a  synset  and propagate  it  through its ancestors. This
    method is more efficient than WordNetTree.increment_synset()
    as it uses WordNetTree.hashtable() to avoid searching.
    
    It's different  from increment_node() in that it  increments
    the counts of ALL nodes  matching a key. In fact, it divides 
    the count by the number of nodes matching the key.
    
    increment_node() resolves  ambiguity using the ancestor path
    received as argument.
    """
    # unfortunately, WordNetTree.load() is not guaranteed to build
    # the entire WordNet tree. The reason is that it starts at root
    # adding the descendants retrieved from synset.hyponyms(). For some
    # odd reason that method not always returns all hyponyms. For
    # example, portugal.n.01 is not retrieved as a hyponym of 
    # european_country.n.01, but if we call
    #   wn.synsets('portugal')[0].hypernym_paths()
    # european-country.n.01 appears as its ancestor.
    # so what we do is check if the number of hypernym paths
    # of a node is the same as the # of nodes in the tree, if
    # it's higher, than we use tree.increment_synset, which is slow
    # but takes care of adding the missing nodes.

    paths = synset.hypernym_paths()
    
    key = synset.name if not synset.hyponyms() else 's.' + synset.name

    if key in hashtable and len(hashtable[key]) == len(paths):
        count = float(count) / len(paths)
        nodes = hashtable[key]
        for n in nodes:
            n.increment_value(count, True)
    else:
        tree.increment_synset(synset, count)    


def load_semantictree(pos, pwset_id, samplesize=None):
    """ Returns a tree representation of WordNet (an
    instance of WordNetTree) for a certain part-of-speech
    with the frequency of the nodes conforming to their
    occurrence in the passwords.

    samplesize - if None, reads the entire database

    """

    sys.setrecursionlimit(10000)

    dir = os.path.dirname(os.path.abspath(__file__))
    fname = "pickles/tree-{}-{}-{}.pickle".format(pos, pwset_id, samplesize)
    path = os.path.join(dir, fname)

    try:
        f = open(path)
        tree = pickle.load(f)
        print 'successfuly pickled tree'
        return tree
    except:
        with Timer("WordNetTree loading"):
            tree = WordNetTree(pos)
        with Timer("WordNetTree population"):
            populate(tree, samplesize, pwset_id)
        print 'no pickling. loaded tree from scratch'
        f = open(path, 'w+')
        pickle.dump(tree, f)  # dumps tree to make the job faster next time
    return tree


def increment_node(hashtable, key, ancestors):
    """ Efficiently increments the count of a node in a tree.
    Args:
        - key: key of the node whose count must be incremented.
        - hashtable: dictionary mapping  keys to all nodes of a 
        tree. See DefaultTree.hashtable()
        - ancestors: a list of the keys of the ancestors of the 
        node, for  disambiguation, in case the tree has several 
        nodes associated with a single key. Root is first.
    """

    nodes = hashtable[key]
    if not nodes:
        return False

    for n in nodes:
        n_ancestors = []
        # check if every ancestor matches
        # every a should be equals to b
        fullmatch = True
        b = n
        for a in reversed(ancestors):
            b = b.parent            
            if not b or a.key != b.key:
                fullmatch = False
                break
            n_ancestors.append(b)                

        if fullmatch:
            n.value += 1
            for b in n_ancestors: b.value += 1
            return True

    return False



def main(db, pos, file_):
    
    tree = DefaultTree()
    treeFile = open(file_, 'wb')

    pos_tagged_total = 0  # number of pos-tagged words
    target_total     = 0  # number of words tagged as pos 
    in_wordnet_total = 0  # number of verbs that are found in wordnet

    while db.hasNext():
        words = db.nextPwd()  # list of Words
        
        for w in words:
            if w.pos is None:
                continue
            pos_tagged_total += 1

            wn_pos = tag_converter.clawsToWordNet(w.pos)  # assumes the pwds are pos-tagged using CLAWS tags
            if wn_pos == pos:
                target_total += 1
            else:
                continue
                
            synset_ = synset(w.word, w.pos)  # best effort to get a synset matching the fragment's pos
            
            # if we were able to find a synset, append it to the tree
            if synset_ is not None:
                in_wordnet_total += 1
                paths = synset_.hypernym_paths()
                for path in paths:
                    path = [s.name for s in path]
                    path.append(w.word)
                    tree.insert(path)
                
    tree.updateEntropy()
    treeFile.write(tree.toJSON())

    db.finish()
    
    print '{} POS tagged words'.format(pos_tagged_total)
    print 'of which {} are {} ({}%)'.format(target_total, pos, float(target_total) * 100 / pos_tagged_total)
    print 'of which {} are found in WordNet ({}%)'.format(in_wordnet_total, float(in_wordnet_total) * 100 / target_total)
    
    return 0
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Performs semantic classification on a sample and outputs its synsets "
                                                 "tree in JSON, containing frequency info.")
    parser.add_argument('password_set', type=int, help='the id of the collection of passwords to be processed')

    parser.add_argument('pos', help='part-of-speech of the semantic tree. n (noun) or v (verb)')
    parser.add_argument('file', help='complete path of the output file')
    parser.add_argument('-s', '--size', type=int, default=None,
                        help='size of the sample from which the words should be gotten.')

    db_group = parser.add_argument_group('Database Connection Arguments')    
    db_group.add_argument('--user', type=str, default='root', help="db username for authentication")
    db_group.add_argument('--pwd',  type=str, default='', help="db pwd for authentication")
    db_group.add_argument('--host', type=str, default='localhost', help="db host")
    db_group.add_argument('--port', type=int, default=3306, help="db port")
                                                                                                         
    args = parser.parse_args()
    
    database.USER = args.user
    database.PWD  = args.pwd
    database.HOST = args.host

    db = database.PwdDb(size=args.size)

    main(db, args.pos, args.file)






