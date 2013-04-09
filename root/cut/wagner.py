"""
The Li & Abe (1998) algorithm modified by a weighting factor,
as described in Wagner (2000).

Created on 2013-04-09

@author: rafa
"""

import li_abe
import math

def compute_dl(cut, sample_size, c):
    pdl = li_abe.compute_pdl(cut, sample_size)  # parameters description length
    dl  = li_abe.compute_dl(cut, sample_size)   # data description length 
    weighting_factor = c * (math.log(sample_size, 2) / sample_size)
    
    return pdl + weighting_factor*dl 


if __name__ == '__main__':
    pass
