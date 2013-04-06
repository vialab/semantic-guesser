""" Encloses the functionality for the 'uneven cut', i.e., a tree cut that
captures the appropriate semantic generalization level for a tree like
WordNet. 

Created on Mar 23, 2013

@author: Rafa

"""

import mdl


def findcut(tree):
    return _findcut(tree.root, tree.root.value)

def _findcut(node, sample_size):
    if node.is_leaf():
        return [node]
    else:
        c = []
        
        for child in node.children():
            c.extend(_findcut(child, sample_size))
        
        # using <= instead of < leads to better generalization
        # deviates slightly from Li & Abe
        if desc_length([node], sample_size) <= desc_length(c, sample_size):
            return [node]
        else:
            return c
        

def desc_length(cut, sample_size):
    """ Returns the description length of a cut """
    cut = [(n.key, n.value, 1 if n.is_leaf() else n.leaves()) for n in cut]
    dl = mdl.compute_dl(cut, sample_size)
    # print "Cut: {}\n\tDescription length: {}".format(cut, dl)
    return dl
