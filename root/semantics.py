'''
This script outputs a tree in JSON format representing the
hypernym paths of all verbs/nouns/etc. tagged in the db.

@author: Rafa
'''

from database import PwdDb
from tagset_conversion import TagsetConverter
from nltk.corpus import wordnet as wn
from tree.default_tree import DefaultTree 
import argparse

tag_converter = TagsetConverter()

def synset(f):
    """Given a fragment, determines its synset by
    converting the Brown tag to WordNet tag and querying
    the associated synset from WordNet.
    
    When the tag has no correspondent in WordNet, but
    the word exists (e.g., ('all', 'DT')), we get the 
    most common sense, e.g., ('all', 'n'). That means
    the returned synset's pos might not match the
    fragment's pos.
    
    f - fragment
    
    """
    synsets = None
    
    wn_pos = tag_converter.brownToWordNet(f.pos) if f.pos else None
    
    if wn_pos is not None:
        synsets = wn.synsets(f.word, wn_pos) 
    else:
        synsets = wn.synsets(f.word)
    
    # returns the most frequent
    return synsets[0] if len(synsets)>0 else None 
    

def main(pos, size, file_):
    
    db = PwdDb(size=size)
    
    tree = DefaultTree()
    treeFile = open(file_, 'wb')

    pos_tagged_total = 0  # number of pos-tagged words
    target_total     = 0  # number of words tagged as pos 
    in_wordnet_total = 0  # number of verbs that are found in wordnet

    
    while (db.hasNext()):
        words = db.nextPwd() # list of Words
        
        for w in words:
            if w.pos is None:
                continue
            pos_tagged_total += 1

            wn_pos = tag_converter.brownToWordNet(w.pos) # assumes the pwds are pos-tagged using Brown tags
            if wn_pos == pos:
                target_total += 1
                
            synset_ = synset(w) # best effort to get a synset matching the fragment's pos   
            
            # check if the synset returned has the pos we want
            if synset_ is not None and synset_.pos==pos:
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
    print 'of which {} are {} ({}%)'.format(target_total, pos, float(target_total)*100/pos_tagged_total)
    print 'of which {} are found in WordNet ({}%)'.format(in_wordnet_total, float(in_wordnet_total)*100/target_total)
    
    return 0
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('pos', help='part-of-speech of the semantic tree. n (noun) or v (verb)')
    parser.add_argument('file', help='complete path of the output file')
    parser.add_argument('-s', '--size', type=int, default=None,
                        help='size of the sample from which the words should be gotten.')
    
    args = parser.parse_args()
    
    main(args.pos, args.size, args.file)
