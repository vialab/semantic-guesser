"""
Specialized Tree and TreeNode for WordNet.

Created on 2013-03-25
@author: rafa
"""

from nltk.corpus import wordnet as wn
from default_tree import DefaultTree, DefaultTreeNode
from collections import deque

class WordNetTreeNode(DefaultTreeNode):

    # a counter for ids. Everytime a node is created, next_id is assigned to it
    # and incremented.
    next_id = 0

    def __init__(self, key, parent=None):
        DefaultTreeNode.__init__(self, key)

        self.cut = False  # True if this node belongs to a tree cut
        self.parent = parent

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

    def path(self):
        """ Returns the path to the root based on the parent attribute."""
        path = list()

        curr = self
        while curr:
            path.insert(0, curr)
            curr = curr.parent

        return path

    def create_node(self, key, value=0):
        newnode = WordNetTreeNode(key, self)
        newnode.value = value
        return newnode


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

    # def key(synset):
    #     if len(synset.hyponyms()) > 0:
    #         syn_node.insert('s.'+syn.name())


    def load(self, pos):
        if pos == 'n':
            roots = wn.synsets('entity')
        else:
            roots = [s for s in wn.all_synsets(pos) if len(s.hypernyms()) == 0]

        self.root = WordNetTreeNode('root')

        for synset in roots:
            self.__append_synset(synset, self.root)

        # check for synsets that were not found
        index = self.hashtable()
        for synset in wn.all_synsets(pos):
            if synset.name() not in index:
                for path in synset.hypernym_paths():
                    keys = [s.name() for s in path]
                    self.__extend(keys,
                        is_internal = len(path[-1].hyponyms()) > 0)



    def __extend(self, path, is_internal=False):
        """ Given a path representing a subtree,
        create and insert nodes that are missing.
        @params:
            path - list(str) - list of node keys, first element should
                match the tree's root.
        """
        if len(path) < 1:
            return

        parent = self.root

        # traverse path, if the key of a node isn't found among
        # the children of the node's parent, then the node doesn't
        # exist in tree, so create it and insert it.
        # if the parent of this new node was a leaf prior to the node's
        # insertion, now it isn't, so create and insert a leaf-copy named
        # s.{nodekey}

        while len(path) > 0:
            key  = path.pop(0)
            node = parent.find(key)
            if node is None:
                if parent.is_leaf():
                    parent.insert('s.' + parent.key)

                node = parent.insert(key)
                if len(path) > 0: # if node is internal
                    node.insert('s.' + key)

            parent = node

        if is_internal:
            node.insert('s.'+key)


    def __append_synset(self, synset, root):
        """Appends the whole  subtree rooted at a  synset to a  root.
        Visits all descendant synsets in a DFS fashion (iteratively),
        creating a WordNetTreeNode for each synset.
        If the synset is not a leaf, creates a child representing its
        sense, with 's.' as a prefix, e.g.,
            person.n.01
                s.person.n.01
                .
                .
        The measure above preserves the constraint that leaves should
        represent senses and internal nodes should represent classes.
        """
        stack = deque()
        stack.append((synset, root)) # -> (child, parent)

        while len(stack):
            syn, parent = stack.pop()
            syn_node = parent.insert(syn.name())

            hyponyms = syn.hyponyms()

            # if not leaf, insert a child representing the sense
            if len(hyponyms) > 0:
                syn_node.insert('s.'+syn.name())

            for hypo in hyponyms:
                stack.append((hypo, syn_node))


    def increment_synset(self, synset, freq=1, cumulative=True):
        paths = synset.hypernym_paths()

        if len(paths) > 1:
            freq = float(freq) / len(paths)

        # multiplies the sense if has more than one parent
        for i, path in enumerate(paths):
            path = [s.name() for s in path]
            if len(synset.hyponyms()) > 0:  # internal node
                path.append('s.' + path[-1])
            self.insert(path, freq, cumulative)


class IndexedWordNetTree(WordNetTree):
    def __init__(self, pos):
        super(IndexedWordNetTree, self).__init__(pos)
        self.index = self.hashtable()
#        nodes = self.flat()
#        self.index = dict()
#        for n in nodes:
#            self.index[n.key] = n

    def get_nodes(self, key):
        return self.index[key] if key in self.index else None

if __name__ == '__main__':
    pass
