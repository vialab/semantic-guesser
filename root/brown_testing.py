'''
Created on Feb 24, 2012

@author: 100457636
'''
from nltk.corpus import brown
from nltk.tag import UnigramTagger

train_sents = brown.tagged_sents()

tagger  = UnigramTagger(train_sents)

print tagger.tag(["doing"]) 