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

    wn_pos = tag_converter.brownToWordNet(pos)

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

    db = database.PwdDb(pwset_id, sample=samplesize)

    while db.hasNext():
        fragments = db.nextPwd()  # list of Fragment

        for f in fragments:
            # we don't want dynamic dict. entries
            if f.is_gap():
                continue

            # best effort to get a synset matching the fragment's pos
            synset_ = synset(f.word, f.pos)

            # check if the synset returned has the pos we want
            if synset_ is not None and synset_.pos == tree.pos:
                tree.insert_synset(synset_)

    return tree


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
        tree = WordNetTree(pos)
        populate(tree, samplesize, pwset_id)
        print 'no pickling. loaded tree from scratch'
        f = open(path, 'w+')
        pickle.dump(tree, f)  # dumps tree to make the job faster next time
    return tree


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

            wn_pos = tag_converter.brownToWordNet(w.pos)  # assumes the pwds are pos-tagged using Brown tags
            if wn_pos == pos:
                target_total += 1
                
            synset_ = synset(w.word, w.pos)  # best effort to get a synset matching the fragment's pos
            
            # check if the synset returned has the pos we want
            if synset_ is not None and synset_.pos == pos:
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






