""" Encloses the functionality for the 'uneven cut', i.e., a tree cut that
captures the appropriate semantic generalization level for a tree like
WordNet.

Created on Mar 23, 2013

@author: Rafa

"""

from . import _li_abe
from . import _wagner



class li_abe:

    def findcut(self, tree, estimator=None):
        return self._findcut(tree.root, tree.root.value, estimator)

    def _findcut(self, node, samplesize, estimator=None, **args):
        # bind common args for the sake of conciseness
        findcut = lambda arg: self._findcut(arg, samplesize, estimator, **args)
        desc_length = lambda arg: self.desc_length(arg, samplesize, estimator, **args)

        if node.is_leaf():
            return [node]
        else:
            c = []

            for child in node.children():
                c.extend(findcut(child))

            # using <= instead of < leads to better generalization
            # deviates slightly from Li & Abe
            if desc_length([node]) <= desc_length(c):
                return [node]
            else:
                return c

    def desc_length(self, cut, sample_size, estimator=None, **args):
        """ Returns the description length of a cut """
        dl = _li_abe.compute_dl(cut, sample_size, estimator)
        return dl


class wagner(li_abe):
    """
    The classic Li & Abe MDL method tends to overgeneralize with
    large samples and undergeneralized with small ones. So a weight
    is introduced to normalize the importance of parameter description length
    and data description length. See:
    "Enriching a lexical semantic net with selectional preferences by
    means of statistical corpus analysis" Wagner (2000).
    """


    default_c = 50  # default weighting factor

    def findcut(self, tree, weight=None, estimator=None):
        if weight is None:
            weight = wagner.default_c
        return self._findcut(tree.root, tree.root.value, estimator, weight=weight)

    def desc_length(self, cut, sample_size, estimator=None, weight=50):
        """ Returns the description length of a cut """
        dl = _wagner.compute_dl(cut, sample_size, weight, estimator)

        return dl

#:::::::::::::::::::::
# PUBLIC API
#:::::::::::::::::::::

li_abe = li_abe()
wagner = wagner()
