""" Encloses the functionality for the 'uneven cut', i.e., a tree cut that
captures the appropriate semantic generalization level for a tree like
WordNet. 

Created on Mar 23, 2013

@author: Rafa

"""

import li_abe as _li_abe
import wagner as _wagner


class li_abe:
    
    def findcut(self, tree):
        return self._findcut(tree.root, tree.root.value)

    def _findcut(self, node, sample_size, **args):
        if node.is_leaf():
            return [node]
        else:
            c = []
            
            for child in node.children():
                c.extend(self._findcut(child, sample_size, **args))
            
            # using <= instead of < leads to better generalization
            # deviates slightly from Li & Abe
            if self.desc_length([node], sample_size, **args) <= self.desc_length(c, sample_size, **args):
                return [node]
            else:
                return c
                
    def desc_length(self, cut, sample_size, **args):
        """ Returns the description length of a cut """
        cut = [(n.key, n.value, 1 if n.is_leaf() else n.leaves()) for n in cut]
        dl = _li_abe.compute_dl(cut, sample_size)
        return dl
    

class wagner(li_abe):
    
    default_c = 50  # default weighting factor 
    
    def findcut(self, tree, weighting=None):
        if weighting is None:
            weighting = wagner.default_c
        return self._findcut(tree.root, tree.root.value, c=weighting)
    
    def desc_length(self, cut, sample_size, **args):
        """ Returns the description length of a cut """
        
        weighting_factor = args['c']
        cut = [(n.key, n.value, 1 if n.is_leaf() else n.leaves()) for n in cut]
        dl = _wagner.compute_dl(cut, sample_size, weighting_factor)
        
        return dl

#:::::::::::::::::::::
# PUBLIC API
#:::::::::::::::::::::

li_abe = li_abe()
wagner = wagner()