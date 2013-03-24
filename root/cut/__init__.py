""" Encloses the functionality for the 'uneven cut', i.e., a tree cut that
captures the appropriate semantic generalization level for a tree like
WordNet. 

Created on Mar 23, 2013

@author: Rafa

"""

import mdl


def findcut(node, sample_size):
    if node.is_leaf():
        return [node]
    else:
        c = []
        
        for child in node.children():
            c.extend(findcut(child, sample_size))
        
        if desc_length([node], sample_size) < desc_length(c, sample_size):
            return [node]
        else:
            return c
        

def desc_length(cut, sample_size):
    """ Returns the description length of a cut """
    cut = [(n.key, n.value, 1 if n.is_leaf() else n.leaves()) for n in cut]
    try:
        return mdl.compute_dl(cut, sample_size)
    except:
        print "error", cut