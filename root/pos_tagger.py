from database import PwdDb
from nltk.corpus import brown, treebank
from nltk.tag.sequential import DefaultTagger, BigramTagger, TrigramTagger
from tag_util import backoff_tagger
from taggers import COCATagger, NamesTagger, WordNetTagger, SentiWordnetTagger
from tagset_conversion import TagsetConverter
from time import time
import nltk
import csv

def getTagger():
    """ Builds a chain of Taggers with context
    (bigram and trigram taggers) based on Brown corpus
    and unigrams based on COCA """
    
    train_sents = brown.tagged_sents();
    
    default_tagger = DefaultTagger('NN')
    wn_tagger      = WordNetTagger(default_tagger)
    names_tagger   = NamesTagger(wn_tagger)
    coca_tagger    = COCATagger(names_tagger)
    
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
    start   = time()
    counter = 0
     
    #csv_writer = csv.writer(open("../results/context-coca-names-wn.csv","wb"), dialect='excel')
    
    db = PwdDb()
    total  = db.sets_size 
    print "connected to database, tagging..."
    
    while (db.hasNext()):
        pwd = db.nextPwd() # list of fragments
        counter += 1
        # filters fragments that are not dictionary words
        pwd = [f for f in pwd if f.dictset_id<=90]
        
        # extracts to a list of strings and tags them
        pos_tagged = pos_tagger.tag([f.word for f in pwd])
        
        for i, f in enumerate(pwd):
            pos = pos_tagged[i][1] # Brown pos tag
            f.pos = pos
            # converts to wordnet tagset and tags by sentiment
            senti = senti_tagger.tag(f.word, tsc.brownToWordNet(pos))
            f.synsets = senti[0] if senti is not None else None
            f.senti   = senti[1] if senti is not None else None 
            
            #csv_writer.writerow([j, pwd[i].word, pos]) # output
            
            db.save(f, True)
        
        if counter % 100000 == 0 : #db.cachelimit :
            print "{} passwords processed. {}% completed...".format(counter, (float(counter)/total)*100 )
    
    db.finish()
    
    print "tagging process took " + str(time()-start) + " seconds."
    
    return 0;

if __name__ == "__main__":
#    main()
    
#    train_sents = treebank.tagged_sents();
    
#    t = backoff_tagger(train_sents, [BigramTagger, TrigramTagger], backoff=DefaultTagger('kk'))
    
    # tests
#    t = getTagger()
    print nltk.pos_tag(['all', 'yours'])
    print nltk.pos_tag(['fuck','you', 'all'])
    print nltk.pos_tag(['all','that', 'counts'])
    print nltk.pos_tag(['all','day'])
    print nltk.pos_tag(['all','day'])
    print nltk.pos_tag(['all','the', 'cake'])
    print nltk.pos_tag(['all', 'alone'])
    print nltk.pos_tag(['to', 'lose', "one's", 'all'])
