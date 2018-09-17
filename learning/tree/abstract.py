"""
Created on 2013-03-23

@author: rafa
"""
from collections import deque

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

    def trim(self, threshold):
        pass

class DepthFirstIterator(object):

    def __init__(self, node):
        self.to_visit = deque()
        self.to_visit.append((0, node))

    def __iter__(self):
        return self

    def next(self):
        if len(self.to_visit) == 0:
            raise StopIteration
        else:
            depth, node = self.to_visit.popleft()
            children = node.children()
            for child in children:
                self.to_visit.appendleft((depth+1, child))

            return (depth, node)
