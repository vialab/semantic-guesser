'''
Created on 2013-03-23

@author: rafa
'''


class Tree:
    def __init__(self, root):
        self.root = root


class TreeNode :
    def __init__(self, key):
        self.key   = key
        self.value = 0 
           
    def insert(self, key=None, node=None):
        pass
    
    def children(self):
        pass
    
    def child(self, key):
        pass
    
    def is_leaf(self):
        return not bool(self.children())
    
    def leaves(self):
        """ Returns number of leaves under this node """
        pass