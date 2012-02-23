from tag_util import backoff_tagger
from nltk.tag.sequential import DefaultTagger, BigramTagger, TrigramTagger
from nltk.corpus import treebank
from nltk.corpus import brown
from nltk.tag import UnigramTagger
import csv
from synth_dataset import sentences
from taggers import WordNetTagger
from taggers import NamesTagger
from time import time

phrases = sentences()

train_sents = brown.tagged_sents();

default_tagger = DefaultTagger('KK')
wn_tagger = WordNetTagger(default_tagger)
names_tagger = NamesTagger(wn_tagger)

print "creating backoff chain..."
tagger  = backoff_tagger(train_sents, [UnigramTagger, BigramTagger, TrigramTagger], 
                           backoff=names_tagger)

print "tagging process initialized..."
start = time()

resultWriter = csv.writer(open('../results/brown-wordnet-names.csv','wb'), dialect='excel')

for p in phrases :
    for pair in tagger.tag(p) :
        resultWriter.writerow([pair[0], pair[1]])

print "tagging process took " + str(time()-start) + " seconds."