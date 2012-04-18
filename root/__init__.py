import csv
from tag_util import backoff_tagger
from nltk.tag.sequential import DefaultTagger, BigramTagger, TrigramTagger
from nltk.corpus import treebank
from nltk.corpus import brown
from nltk.tag import UnigramTagger
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
    """ Builds a chain of Taggers with context
    (bigram and trigram taggers) based on Brown corpus
    and unigrams based on COCA"""
    
    train_sents = brown.tagged_sents();
    
    default_tagger = DefaultTagger('KK')
    wn_tagger = WordNetTagger(default_tagger)
    names_tagger = NamesTagger(wn_tagger)
    coca_tagger = COCATagger(names_tagger)
    
    print "creating backoff chain..."
    return backoff_tagger(train_sents, [BigramTagger, TrigramTagger], 
                               backoff=coca_tagger)


def main():
    """ Tags the dataset by POS and sentiment at
        the same time """    
        
    pos_tagger = getTagger()
    senti_tagger = SentiWordnetTagger()
    tsc = TagsetConverter()
    
    print "tagging process initialized..."
    start = time()
    
    #csv_writer = csv.writer(open("../results/context-coca-names-wn.csv","wb"), dialect='excel')
    
    db = PwdDb()
    print "connected to database, tagging..."
    while (db.hasNext()):
#    for j in range(30000):
        pwd = db.nextPwd() # list of Words
        # extracts to a list of strings and tags them
        pos_tagged = pos_tagger.tag([wo.word for wo in pwd])
        
        for i in range(len(pos_tagged)):
            pos = pos_tagged[i][1] # Brown pos tag
            pwd[i].pos = pos
            # converts to wordnet tagset and tags by sentiment
            senti = senti_tagger.tag(pwd[i].word, tsc.brownToWordNet(pos))
            pwd[i].synsets = senti[0] if senti is not None else None
            pwd[i].senti   = senti[1] if senti is not None else None 
            
            #csv_writer.writerow([j, pwd[i].word, pos]) # output
            
            db.save(pwd[i])
    
    db.finish()
    
    print "tagging process took " + str(time()-start) + " seconds."
    
    return 0;

if __name__ == "__main__":
    main()