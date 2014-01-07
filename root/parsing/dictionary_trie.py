import cPickle as pickle

class Node:
    """ The node of a Trie. Stores a character. """
    
    def __init__(self, key):
        self.leftchild = None
        self.rightsibling = None
        self.key = key
        # frequency of the word whose last character is stored by this node.
        self.freq = 0
        
    
    def children(self):
        children = list()
        c = self.leftchild  # c is the current child
        # moving to the right until the last child
        while c is not None:
            children.append(c)
            c = c.rightsibling
        return children
    
    def child(self, key):
        """ Returns the child corresponding to the key or None. """
        c = self.leftchild  # current child
        while c is not None:
            if c.key == key:
                return c
            else:
                c = c.rightsibling
        return None
    
    def append(self, key=None):
        """Inserts a child to this node.
        If it already exists, do nothing...
        In both cases, returns the child.
        """
        newchild = Node(key)
        
        if self.leftchild is None:
            self.leftchild = newchild
        else:
            c = self.leftchild  # c is the current child
            
            while True:
                # if key is already there, do nothing
                if c.key == key:
                    return c
                if c.rightsibling is None:  # if reached the last child
                    # add the key as right sibling of the last child
                    c.rightsibling = newchild
                    break
                    
                c = c.rightsibling  # moving to the right
        
        return newchild
    
class Trie:
    """ A trie, or character tree, as described in en.wikipedia.org/wiki/Trie """
    def __init__(self):
        self.root = Node('')
    
    def insert(self, word, freq):
        """ Insert a word in this trie, with a certain frequency"""
        
        node = self.root
        for c in word:
            child = node.child(c)
            if child is None:
                child = node.append(c)
            node = child        
        node.freq = freq
    
    def getFrequency(self, word):
        """Returns the frequency of the given word. If the word isn't found, returns 0."""
        node = self.root
        for c in word:
            node = node.child(c)
            if node is None:
                return 0
        return node.freq
    
    def saveState(self, fileName):
        """ Don't call this. It's supposed to store the trie in a file, 
	but it'll take forever. """
        with open(fileName, 'w+b') as f:
            pickle.dump(self, f)
    
    @classmethod            
    def loadState(self, fileName):
        with open(fileName, 'rb') as f:
            return pickle.load(f)


# t = Trie()
# t.insert('a b', 2)
# t.insert('a c', 5)
# t.insert('abc', 1)
# print t.getFrequency('abc')
