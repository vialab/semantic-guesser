"""
Loads WordNet into a DefaultTree.

1. Nodes with multiple parents are duplicated
2. Senses are separated from semantic class, i.e.,
   for each non-leaf node, a node with prefix 's' 
   is appended as first child representing its sense.
   So all leaves represent senses, all internal nodes
   represent classes.
   For example:
       person.n.01
           s.person.n.01
           cripple.n.01
               humpback.n.02
           faller.n.02                 
           hater.n.01
   

Created on 2013-03-25

@author: rafa

"""

from nltk.corpus import wordnet as wn 
from default_tree import DefaultTree, DefaultTreeNode
from ..cut import findcut


def load(pos):
    
    tree = DefaultTree()
    
    if (pos=='n'):
        roots = wn.synsets('entity')
    else:
        roots = [s for s in wn.all_synsets(pos) if len(s.hypernyms())==0]
    
    root_node = DefaultTreeNode('root')
    
    for synset in roots:
        append_child(synset, root_node)
    
    tree.root = root_node 
    
    return tree  

def append_child(synset, parent):
    node = parent.insert(synset.name)
    hyponyms = synset.hyponyms()
    
    # if not leaf, insert the child representing the sense 
    if len(hyponyms)>0: 
        node.insert('s.'+synset.name)
    
    for h in hyponyms:
        append_child(h, node)

def freq_dist():
    dist = dict()
    f = open('/home/rafaveguim/workspace/pwd_classifier/root/tree/all_nouns.txt', 'r')

    LIMIT = 100000
    
    word = f.readline()[:-2]
    counter = 0
    while word is not None:
        counter += 1
        if counter>=LIMIT:
            break
        if word in dist:
            dist[word] += 1
        else:
            dist[word] = 1
        word = f.readline()[:-2]
        
    return dist

def populate(tree, dist, pos):
    for key, freq in dist.items():
        try :
            synset = wn.synsets(key,pos)[0]
        except:
            continue
        for path in synset.hypernym_paths():
            path = [s.name for s in path]
            if len(synset.hyponyms())>0:  # internal node
                path.append('s.'+path[-1])
            tree.insert(path, freq)
    return tree
            
            
if __name__ == '__main__':
    # TODO: need to get the correct synset, by part-of-speech
    pos = 'n'
    tree = load(pos)
    dist = freq_dist()
#    print dist
    tree = populate(tree, dist, pos)
    print tree.root.print_nested()
#    print findcut(tree.root, tree.root.value)
#    print tree.root.print_nested()
     