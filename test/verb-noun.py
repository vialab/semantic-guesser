'''
Lists the verbs that are also nouns,
as well as their frequencies (as nouns and verbs).
It'll help us to define a threshold for f_verb/f_noun.
If this threshold is not met, the word is deemed as noun,
in favor of the 'concreteness' rule. 

Created on Mar 30, 2012

@author: Rafa
'''
from __future__ import division 
from root.database import PwdDb
from root.taggers import COCATagger
from root.tagset_conversion import TagsetConverter
import csv

def main():
    db = PwdDb()
    coca_tagger = COCATagger()
    csv_writer = csv.writer(open("verb_noun.csv","wb"), dialect='excel')
    tsc = TagsetConverter()
    
    for i in range(30001):
        pwd = db.nextPwd();
        for w in pwd:
            t = coca_tagger.tag([w.word])[0][1]
            if (t is None): continue
            t = tsc.brownToWordNet(t);
            if (t=='v'):
                v_freq = coca_tagger.getFrequency(w.word, t)
                n_freq = coca_tagger.getFrequency(w.word, 'n')
                if (n_freq is not None):
                    csv_writer.writerow([i, w.word, v_freq, n_freq, (v_freq/n_freq)])
                
    print 'the end'   
         
if __name__ == '__main__':
    main()