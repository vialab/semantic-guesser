from tag_util import backoff_tagger
from nltk.tag.sequential import DefaultTagger, BigramTagger, TrigramTagger
from nltk.corpus import treebank
from nltk.corpus import brown
from nltk.tag import UnigramTagger
import csv
from synth_dataset import sentences
from taggers import WordNetTagger
from taggers import NamesTagger
from taggers import COCATagger
from time import time
from database import PwdDb
from database import WordOccurrence
import pickle

def getTagger():
    train_sents = brown.tagged_sents();
    
    default_tagger = DefaultTagger('KK')
    coca_tagger = COCATagger(default_tagger)
    wn_tagger = WordNetTagger(coca_tagger)
    names_tagger = NamesTagger(wn_tagger)
    
    print "creating backoff chain..."
    return backoff_tagger(train_sents, [UnigramTagger, BigramTagger, TrigramTagger], 
                               backoff=names_tagger)

#phrases = sentences()
def main():    
    tagger = getTagger()
    #tagger = DefaultTagger('KK')
    
    print "tagging process initialized..."
    start = time()
    
    #resultWriter = csv.writer(open('../results/brown-wordnet-names-coca.csv','wb'))
    db = PwdDb()
    print "connected to database, tagging..."
    while (db.hasNext()):
    #for n in range(3):
        pwd = db.nextPwd()
        tagged = tagger.tag([wo.word for wo in pwd])
        for i in range(len(tagged)):
            pwd[i].pos = tagged[i][1]
            db.save(pwd[i])
    
    #===============================================================================
    # for p in phrases :
    #    for pair in tagger.tag(p) :
    #        resultWriter.writerow([pair[0], pair[1]])
    #===============================================================================
    
    db.finish()
    
    print "tagging process took " + str(time()-start) + " seconds."
    
    return 0;
    
if __name__ == "__main__":
    main()