"""
Specialized Tree and TreeNode for WordNet.

Created on 2013-03-25
@author: rafa
"""

from nltk.corpus import wordnet as wn
from learning.tree.default_tree import DefaultTree, DefaultTreeNode, DepthFirstIterator
from collections import deque

class WordNetTreeNode(DefaultTreeNode):

    # a counter for ids. Everytime a node is created, next_id is assigned to it
    # and incremented.
    next_id = 0

    def __init__(self, key, parent=None, value=0):
        DefaultTreeNode.__init__(self, key)

        self.cut = False  # True if this node belongs to a tree cut
        self.parent = parent
        self.value = value
        self.leaf_count = 0  # lazy (updated with WordNetTree.updateCounts())

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
            return {'key': self.key, 'value': self.value, 'id': self.id, 'leaf_count': self.leaf_count}
        else:
            return {'key': self.key, 'value': self.value,
                    'entropy': self._entropy, 'id': self.id, 'children': children, 'leaf_count': self.leaf_count}

    def path(self):
        """ Returns the path to the root based on the parent attribute."""
        path = list()

        curr = self
        while curr:
            path.insert(0, curr)
            curr = curr.parent

        return path

    def updateCounts(self):
        """ Visit nodes in a bottom-up fashion updating all cumulative
        attributes (e.g, value, leaf_count).
        """
        nodes = self.flat()

        # clear values of internal nodes
        for node in nodes:
            if not node.is_leaf():
                node.value = 0
                node.leaf_count = 0
            else:
                node.leaf_count = 1

        # visit nodes in reverse order, so that
        # parents always come after their children
        for node in reversed(nodes):
            if node.parent:
                node.parent.value += node.value
                node.parent.leaf_count += node.leaf_count

    def create_node(self, key, value=0):
        newnode = WordNetTreeNode(key, self)
        newnode.value = value
        return newnode

    # def __getstate__(self):
    #     # do not reference other nodes, or recursionlimit will
    #     # easily be reached. instead, rely on ids
    #     return {
    #         'value': self.value,
    #         'leaf_count': self.leaf_count,
    #         'leftchild': self.leftchild.id,
    #         'rightsibling': self.rightsibling.id,
    #         'key': self.key
    #     }
    #
    # def __setstate__(self, d):
    #     self.value = d['value']
    #     self.leaf_count = d['leaf_count']
    #     self.leftchild = d['leftchild']
    #     self.rightsibling = d['rightsibling']
    #     self.key = d['key']


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

    def __init__(self, pos, wordnet=None, init=True):
        """ Loads the WordNet tree for a given part-of-speech. 'entity.n.01' is
           the root for nouns; otherwise, creates an artificial root named
           'root' whose children are all the root nodes (the verbs ontology has
           several roots).

        Args:
            pos - 'n' for nouns and 'v' for verbs
            wordnet - optional - an instance of WordNetCorpusReader
            init - optional - if True, then "initialize" tree by creating the
            structure (nodes and links) described in nltk.corpus.wordnet
        """
        self.pos = pos
        self.wn = wn if wordnet is None else wordnet

        if init:
            self.load(pos)

    def load(self, pos):
        wn = self.wn

        if pos == 'n':
            roots = wn.synsets('entity')
        else:
            roots = [s for s in wn.all_synsets(pos) if len(s.hypernyms()) == 0]

        self.root = WordNetTreeNode('root')

        for synset in roots:
            self.__append_synset(synset, self.root)

        # unfortunately, the block above is not guaranteed to build
        # the entire WordNet tree. The reason is that it starts at root
        # adding the descendants retrieved from synset.hyponyms(). For some
        # odd reason that method not always returns all hyponyms. For
        # example, portugal.n.01 is not retrieved as a hyponym of
        # european_country.n.01, but if we call
        #   wn.synsets('portugal')[0].hypernym_paths()
        # european-country.n.01 appears as its ancestor.

        # check for synsets that were not foundss
        index = self.hashtable()
        for synset in wn.all_synsets(pos):
            if synset.name() not in index:
                for path in synset.hypernym_paths():
                    keys = [s.name() for s in path]
                    self.__extend(keys,
                        is_internal = len(path[-1].hyponyms()) > 0)

    def updateCounts(self):
        self.root.updateCounts()

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

            for hypo in reversed(hyponyms):
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

    def __getstate__(self):
        nodes = dict()

        for depth, node in DepthFirstIterator(self.root):
            nodes[node.id] = (node.key,
                              node.value,
                              node.leaf_count,
                              node.leftchild.id if node.leftchild else None,
                              node.rightsibling.id if node.rightsibling else None)

        return {
            'root': self.root.id,
            'pos':  self.pos,
            'nodes': nodes
        }

    def __setstate__(self, d):
        nodes = d['nodes']

        root_id = d['root']
        root_key, root_value, root_leaf_count, root_leftchild_id, root_rightsibling_id = nodes[root_id]
        root_node = WordNetTreeNode(root_key, value=root_value)
        root_node.id = root_id
        root_node.leaf_count = root_leaf_count

        queue = deque()
        queue.append((None, root_node, root_leftchild_id, root_rightsibling_id))

        while len(queue) > 0:
            parent, node, leftchild_id, rightsibling_id = queue.popleft()

            if rightsibling_id is not None:
                k, v, l, c, s = nodes[rightsibling_id]
                rightsibling =  WordNetTreeNode(k, value=v)
                rightsibling.id = rightsibling_id
                rightsibling.parent = parent
                rightsibling.leaf_count = l
                node.rightsibling = rightsibling
                queue.appendleft((parent, rightsibling, c, s))

            if leftchild_id is not None:
                k, v, l, c, s = nodes[leftchild_id]
                leftchild =  WordNetTreeNode(k, value=v)
                leftchild.id = leftchild_id
                leftchild.leaf_count = l
                node.leftchild = leftchild
                leftchild.parent = node
                queue.appendleft((node, leftchild, c, s))

        self.root = root_node
        self.pos  = d['pos']


class IndexedWordNetTree(WordNetTree):
    def __init__(self, pos, wordnet=None):
        super(IndexedWordNetTree, self).__init__(pos, wordnet)
        self.index = self.hashtable()

    def get_nodes(self, key):
        return self.index[key] if key in self.index else None

    def add(self, tree, update=True):
        """Add the counts of a tree to this one."""
        if isinstance(tree, IndexedWordNetTree):
            index = tree.index
        else:
            index = tree.hashtable()

        for leaf in self.leaves():
            leaf.value += index[leaf.key].value

        if update:
            self.updateCounts()

    def __getstate__(self):
        return WordNetTree.__getstate__(self)

    def __setstate__(self, d):
        WordNetTree.__setstate__(self, d)
        self.index = self.hashtable()


if __name__ == '__main__':
    pass
