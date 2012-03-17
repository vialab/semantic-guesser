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
from root.tagset_conversion import TagsetConverter
from root.taggers import SentiWordnetTagger

def getTagger():
    """ Builds our chain of Taggers """
    
    train_sents = brown.tagged_sents();
    
    default_tagger = DefaultTagger('KK')
    coca_tagger = COCATagger(default_tagger)
    wn_tagger = WordNetTagger(coca_tagger)
    names_tagger = NamesTagger(wn_tagger)
    
    print "creating backoff chain..."
    return backoff_tagger(train_sents, [UnigramTagger, BigramTagger, TrigramTagger], 
                               backoff=names_tagger)


def main():
    """ Tags the dataset by POS and sentiment at
        the same time """    
        
    pos_tagger = getTagger()
    senti_tagger = SentiWordnetTagger()
    tsc = TagsetConverter()
    
    print "tagging process initialized..."
    start = time()
    
    db = PwdDb()
    print "connected to database, tagging..."
    while (db.hasNext()):
        pwd = db.nextPwd() # list of Words
        # extracts to a list of strings and tags them
        pos_tagged = pos_tagger.tag([wo.word for wo in pwd]) 
        
        for i in range(len(pos_tagged)):
            pos = pos_tagged[i][1] # Brown pos tag
            pwd[i].pos = pos
            # converts to wordnet tagset and tag by sentiment
            senti = senti_tagger.tag(pwd[i].word, tsc.brownToWordNet(pos))
            if (senti is not None):
                pwd[i].synsets = senti[0]
                pwd[i].senti = senti[1] 
            
            db.save(pwd[i])
    
    db.finish()
    
    print "tagging process took " + str(time()-start) + " seconds."
    
    return 0;

if __name__ == "__main__":
    main()