""" Left child, right sibling tree 
Inspired by Cormen's Introduction to Algorithms 3rd edition (p. 247)
"""

import json

class TreeNode:
    
    def __init__(self, key):
        self.leftChild    = None
        self.rightSibling = None
        self.key          = key
        self.value        = 0
        
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
    
    def wrap(self):
        children = list()
        for child in self.children() :
            children.append(child.wrap())
        if len(children) == 0 :
            return {'key': self.key, 'value': self.value}
        else :    
            return {'key': self.key, 'value': self.value, 'children': children}

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
        
        # insert all keys into the tree
        for key in path :
            currNode = currNode.insert(key)
        
        # increments the count of the leaf
        currNode.value += 1;

            
    def toJSON(self):   
        return json.dumps(self.root.wrap())
    

#tree = Tree()
#tree.insert(['object', 'automobile', 'car'])
#tree.insert(['object', 'automobile'])
#print 'end'