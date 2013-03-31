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
            
            
if __name__ == '__main__':
    pass
