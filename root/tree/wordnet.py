"""
Specialized Tree and TreeNode for WordNet.
   
Created on 2013-03-25

@author: rafa

"""

from nltk.corpus import wordnet as wn 
from default_tree import DefaultTree, DefaultTreeNode


class WordNetTreeNode(DefaultTreeNode):
    
    # a counter for ids. Everytime a node is created, next_id is assigned to it
    # and incremented.
    next_id = 0
    
    def __init__(self, key):
        DefaultTreeNode.__init__(self, key)
        self.cut = False  # True if this node belongs to a tree cut

        # a unique identifier is necessary, since many nodes are duplicated
        # and preserve the same name
        self.id = WordNetTreeNode.next_id
        WordNetTreeNode.next_id += 1  

    def wrap(self):
        """ Returns a representation of this node (including all children)
        as a single object, JSON-style.
        """
        children = list()
        for child in self.children():
            children.append(child.wrap())
        if len(children) == 0:
            return {'key': self.key, 'value': self.value, 'id': self.id}
        else:
            return {'key': self.key, 'value': self.value,
                    'entropy': self._entropy, 'id': self.id, 'children': children}

    def create_node(self, key):
        return WordNetTreeNode(key)


class WordNetTree(DefaultTree):
    """
    A POS-specific tree representation of WordNet.

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
    """
    
    def __init__(self, pos):
        """ Loads the WordNet tree for a given part-of-speech.
           'entity.n.01' is the root for nouns; otherwise, creates an artificial
           root named 'root' whose children are all the root nodes (the verbs ontology
           has several roots).
            
        """
        self.pos = pos
        self.load(pos)

    def load(self, pos):
        if pos == 'n':
            roots = wn.synsets('entity')
        else:
            roots = [s for s in wn.all_synsets(pos) if len(s.hypernyms()) == 0]
        
        self.root = WordNetTreeNode('root')
        
        for synset in roots:
            self.__append_synset(synset, self.root)
        
    def __append_synset(self, synset, parent):
        """ Given a parent node, creates a node for the informed synset 
        and inserts it as a child.
        If the synset is not a leaf, creates its first child representing
        its sense, with 's.' as a prefix, e.g.,
            person.n.01
                s.person.n.01
                .
                .
        """
        node = parent.insert(synset.name)
        hyponyms = synset.hyponyms()
        
        # if not leaf, insert a child representing the sense 
        if len(hyponyms) > 0:
            node.insert('s.'+synset.name)
        
        for h in hyponyms:
            self.__append_synset(h, node)
            
    def insert_synset(self, synset, freq=1):
        paths = synset.hypernym_paths()
        
        if len(paths) > 1:
            freq = float(freq) / len(paths)
        
        # multiplies the sense if has more than one parent 
        for i, path in enumerate(paths):
            path = [s.name for s in path]
            if len(synset.hyponyms()) > 0:  # internal node
                path.append('s.' + path[-1])
            self.insert(path, freq)
            
            
if __name__ == '__main__':
    pass
