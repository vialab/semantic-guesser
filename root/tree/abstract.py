"""
Created on 2013-03-23

@author: rafa
"""


class Tree(object):
    def __init__(self, root):
        self.root = root


class TreeNode(object):
    def __init__(self, key):
        self.key = key
        self.value = 0 
           
    def insert(self, key=None, node=None):
        pass
    
    def remove(self, child):
        pass
    
    def children(self):
        pass
    
    def child(self, key):
        pass
    
    def is_leaf(self):
        return not bool(self.children())
    
    def leaves(self):
        """ Returns all leaves under this node """
        pass

#     def path(self, key):
#         """ Returns an array containing the path from root to the desired node """
#         pass

    def trim(self, threshold):
        pass
