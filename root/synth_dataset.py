'''
Created on Feb 14, 2012

@author: Rafa
'''

import csv

def sentences():
    file_ = csv.reader(open('../files/synthDataset.csv'))
    
    oldPwdId = -1;
    sents = [] #store all the sentences found
    words = [] #temp to store words of a password
    
    header = True #to skip the headers
    
    for row in file_:
        if (header) : 
            header = False
            continue
        pwdId =  row[0]
        
        if (oldPwdId!=-1 and pwdId!=oldPwdId):
            sents.append(words)
            words = []
        
        words.append(row[3])
        oldPwdId = pwdId
    
    sents.append(words)
    return sents
            
        