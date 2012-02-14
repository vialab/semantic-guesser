'''
Created on Feb 14, 2012

@author: Rafa
'''

import csv

def sentences():
    return csv.reader(open('files/synthDataset.csv'))
    #for row in file:
        