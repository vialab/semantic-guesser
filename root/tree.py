""" Left child, right sibling tree.
Inspired by Cormen's Introduction to Algorithms 3rd edition (p. 247).

@author: Rafa

"""

import json
from math import log

class TreeNode:
    
    def __init__(self, key):
        self.leftChild    = None
        self.rightSibling = None
        self.key          = key
        self.value        = 0
        self._entropy     = 0
        
    def children(self):
        children = list()
        c = self.leftChild # c is the current child
        # moving to the right until the last child
        while c is not None :
            children.append(c)
            c = c.rightSibling
        return children
    
    def insert(self, key):
        '''Inserts a child to this node.
        If it already exists, do nothing...
        In both cases, returns the child.
        '''
        newKid = None
        if self.leftChild is None :
            self.leftChild = newKid = TreeNode(key)
        else :
            c = self.leftChild # c is the current child
            
            while True:
                # if key is already there, do nothing
                if c.key == key :
                    #c.value += 1
                    return c
                if c.rightSibling is None : # if reached the last child
                    # add the key as right sibling of the last child
                    c.rightSibling = newKid = TreeNode(key)
                    break
                    
                # moving to the right
                c = c.rightSibling
        
        return newKid 
    
    def child (self, key):
        """Returns the child corresponding to the key
        or None. 
        """
        c = self.leftChild # current child
        while c is not None :
            if c.key == key :
                return c
            else :
                c = c.rightSibling
        return None
    
    def entropy(self):
        self._entropy = 0
        total = self.value
        
        for c in self.children():
            p = float(c.value)/total
            self._entropy -= p * log(p,2)
        
        return self._entropy
          
    
    def wrap(self):
        """ Returns a representation of this node (including all children)
        as a single object, JSON-style.
        """
        children = list()
        for child in self.children() :
            children.append(child.wrap())
        if len(children) == 0 :
            return {'key': self.key, 'value': self.value}
        else :    
            return {'key': self.key, 'value': self.value, 
                    'children': children, 'entropy': self._entropy}

class Tree:
    
    def __init__(self):
        self.root = TreeNode('root')
        self.root.value = 0
        
    def insert(self, path):
        """Insert a subtree.
        Increments the value of the last node (leaf in this path), 
        regardless it will be a leaf in this tree.
        
        Args:
            path: a list of keys, from root to leaf, e.g.:
                ['connect', 'join', 'copulate', 'sleep_together']    
        """
        currNode = self.root
        
        # insert all keys into the tree, increasing their value
        for key in path :
            currNode.value += 1
            currNode = currNode.insert(key)
        
        # increments the count of the leaf
        currNode.value += 1

    def updateEntropy(self, node=None):
        """ The __entropy of the nodes is not updated
        every time the structure changes cause it can be
        too expensive. You need to update this attribute
        manually by calling this method.
        """
        if node is None:
            self.updateEntropy(self.root)
        else:
            e = node.entropy()
            for c in node.children():
                self.updateEntropy(c)
                    
            
    def toJSON(self):   
        return json.dumps(self.root.wrap())
    

#tree = Tree()
#tree.insert(['object', 'automobile', 'car'])
#tree.insert(['object', 'automobile', 'truck'])
#tree.insert(['house'])
#tree.insert(['building'])
#tree.insert(['car'])
#tree.insert(['six'])
#tree.insert(['seven'])
#tree.insert(['eight'])
#tree.insert(['nine'])
#tree.insert(['ten'])
#tree.updateEntropy()
#print tree.toJSON()