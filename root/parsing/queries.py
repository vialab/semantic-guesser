from oursql import CollatedWarningsError
from dictionary_trie import Trie
from utils import *

NUM_DICT_ID    = 200
MIXED_NUM_SC_DICT_ID = 201
SC_DICT_ID = 202
CHAR_DICT_ID = 203
MIXED_ALL_DICT_ID = 204

# trie     = Trie()

ngrams = dict()

toEscape = ['\\', '\'', ' ']

# the Trie, at least in the way I implemented, is a SUPER FAILURE
# in terms of memory consumption
# def initializeTrie(dbe):
# 
#     # populating our unigram trie
#     with dbe.cursor() as cursor:
#             query = 'SELECT word,MAX(freq) FROM passwords.COCA_wordlist group by word'
#             cursor.execute(query, )
#             for word, freq in cursor:
#                     trie.insert(word, freq)
#             cursor.close()
#     # then the bigram trie        
#     with dbe.cursor() as cursor:
#             query = 'SELECT word1, word2, freq FROM passwords.bigrams'
#             cursor.execute(query, )
#             for word1, word2, freq in cursor:
#                     trie.insert(word1+' '+word2, freq)
#             cursor.close()
#     # then the trigram trie        
#     with dbe.cursor() as cursor:
#             query = 'SELECT word1, word2, word3, freq FROM passwords.trigrams'
#             cursor.execute(query, )
#             for word1, word2, word3, freq in cursor:
#                     trie.insert(word1+' '+word2+' '+word3, freq)
#             cursor.close()

# def storeTrieInFile():
#     trie.saveState('coca_trie.pik')

def loadNgrams(dbe):
    # unigrams
    with dbe.cursor() as cursor:
        query = 'SELECT word,MAX(freq) FROM passwords.COCA_wordlist group by word'
        cursor.execute(query, )
        for word, freq in cursor:
            ngrams[word] = freq
        cursor.close()
    
    # bigrams        
    with dbe.cursor() as cursor:
        query = 'SELECT word1, word2, freq FROM passwords.bigrams'
        cursor.execute(query, )
        for word1, word2, freq in cursor:
                ngrams[word1+' '+word2] = freq
        cursor.close()
    
    # trigrams        
    with dbe.cursor() as cursor:
        query = 'SELECT word1, word2, word3, freq FROM passwords.trigrams'
        cursor.execute(query, )
        for word1, word2, word3, freq in cursor:
            ngrams[word1+' '+word2+' '+word3] = freq
        cursor.close()

def getDataSetSize(dbe, tableName):

    with dbe.cursor() as cursor:
        query = '''SELECT count(*) FROM ''' + tableName + ''';'''
        cursor.execute(query, )
        count = cursor.fetchall()[0][0]
        cursor.close()
        
    return count

def freqReadCache(dbe):

    # we actually need to sum these up to be accurate, instead of just their
    # raw count.
    with dbe.cursor() as cursor:
        query = '''SELECT sum(freq) FROM COCA_wordlist;'''
        cursor.execute(query, )
        num_unigrams = cursor.fetchall()[0][0]
        query = '''SELECT sum(freq) FROM bigrams;'''
        cursor.execute(query, )
        num_bigrams = cursor.fetchall()[0][0]
        query = '''SELECT sum(freq) FROM trigrams;'''
        cursor.execute(query, )
        num_trigrams = cursor.fetchall()[0][0]
        
        cursor.close()
        
    return (num_unigrams, num_bigrams, num_trigrams)

def resetDynamicDictionary( dbe ):
    query = '''DELETE FROM dictionary where dictset_id >= ''' + str(NUM_DICT_ID) + ''';'''
    with dbe.cursor() as cur:
        cur.execute(query, ())

def reloadDynamicDictionary(dbe, oldDictionary):
    result = getDictionary(dbe, [NUM_DICT_ID, MIXED_NUM_SC_DICT_ID, SC_DICT_ID, CHAR_DICT_ID])
    for x in result:
        oldDictionary[x] = result[x]
        #print ("reloadDictionary: ", x, ":", oldDictionary[x])

    #print ("test: ", oldDictionary[u'D'])
    return oldDictionary

def addToDynamicDictionary(dbe, dynDictionaryID, segment):
    '''Adds a segment to the db with a certain dictset_id.
    Notice that it won't make the segment lowercase; so 'lWic' ~= 'lwic'.
    It will, however, strip it, i.e., 'lwic  ' == 'lwic'    
    '''
    # right-strip it cause MySQL doesn't consider trailing spaces
    segment = segment.rstrip()

    query = '''INSERT INTO dictionary (dictset_id, dict_text)
    select * from (select ''' + str(dynDictionaryID) + ''' as id,  \'''' + escape(segment, toEscape) + '''\' as text  )
    as tmp where not exists (select dictset_id, dict_text from dictionary where
    dictset_id = ? and dict_text = ?);'''

    with dbe.cursor() as cur:
        cur.execute(query, (dynDictionaryID, segment,))

#     cur.close()  # no need for this
    
    # Apparently we don't need to return the dynDictID
#     result = dictIDbyWord(dbe, [segment], dynDictionaryID)
#     try:
#         dynDictID = result[segment]
#     except KeyError, e:
#         print 'KeyError -> segment: ', segment, ' not found in: ', result
#         raise
#     return dynDictID

def pwIDfromText(sqleng, password, pwsetID):
    '''Not used anymore'''
    with sqleng.cursor() as cursor:
        query = '''SELECT pass_id FROM passwords
                WHERE pwset_id = ? AND pass_text = ?
                LIMIT 1;'''
        cursor.execute(query, params=(pwsetID, escape(password, toEscape)))
        pwid = cursor.fetchall()[0][0]
        cursor.close()
    return pwid

def dictIDbyWord(sqleng, dictwordset, dictsetID=None):
    result = dict()
    
    query = '''SELECT dict_id, dict_text FROM dictionary
                WHERE dict_text = ?'''
    if dictsetID :
        query += ''' AND dictset_id = ?;'''
    
    with sqleng.cursor() as cur:
        for x in dictwordset:
            params = (x, dictsetID) if dictsetID else (x,)
            cur.execute(query, params)
            for dict_id, dict_text in cur:
                result[dict_text] = dict_id
    return result
        
def partIter(iterable, const):
    '''A partial iterator, outputs the constant value with each of the iterable.'''
    pool = tuple(iterable)
    for x in pool:
        yield (const, x)

def resIter(setID, resSet, idMap):
    '''Iterator generator used for storing the results. A nice little generator.'''
    pool = tuple(resSet)
    for x in pool:
        yield (setID, idMap[x[0]][1], x[1], x[2])

def wordsFromResultSet(resultSet):
    '''Returns just the words for the result set, for use in storage.'''
    words = list()
    for sets in resultSet[0]:
        for wordTups in sets:
            if wordTups[0] not in words:
                words.append(wordTups[0])
    return words
        
def storeResults(sqleng, passID, dictsetID, resultSet, dictionary):
    '''Older function used to store the results into the database, depreciated.'''
    words = wordsFromResultSet(resultSet) #gets s simple list of all words in resultSet
    print(words)
    dwords = dictionary
    sets = dict() #this is supposed to be dict[set#] = "string of pass"
    for x in range(len(resultSet[0])): #i hate iterating this way =/
        setext = ''
        for wordTup in resultSet[0][x]:
            setext += wordTup[0]
        sets[x] = setext
    
    print("sets:",sets)
    print("rs:",resultSet)
    print()
    
    insQuery = '''INSERT INTO sets (pass_id, set_pw) VALUES ( ? , ? );'''
    linkQuery = '''INSERT INTO set_contains (set_id, dict_id, s_index, e_index) VALUES
            ( ? , ? , ? , ? );'''
    
    with sqleng.cursor() as cur:
        for x in range(len(sets)):
            #this is where all the time is comming from.
            cur.execute(insQuery, (passID, sets[x]))
            rid = cur.lastrowid
            cur.executemany(linkQuery, resIter(rid, resultSet[0][x], dwords)) #i hopes this is right

def getDictionary(sqleng, dictset_ids):
    
    query = '''SELECT dict_text, dict_id FROM dictionary WHERE dictset_id = ?
            ORDER BY dict_id asc;'''
    dictionary = dict()
    tmp = None # for throwing keyerrors on dicitonary
    with sqleng.cursor() as cur:
        #this execution should be more or less 30 seconds for the size of DB currently.
        for x in dictset_ids:
            #print ("X=", x)
            cur.execute(query, (x,))
            res = cur.fetchall()
            ## THIS PRIORITIZES DICTIONARIES.
            ## assumption: the dictionaries are in priority order (in the dictset_ids list)
            for dict_text, dict_id in res:
                try: # previously, it was making dict_text.lower(). I just removed the lower() part to preserve the case [Rafael]
                    tmp = dictionary[dict_text]
                except:
                    # TODO: This change is experimental. *Apparently*, we don't need dict_text in the tuple,
                    # but the guessability code needs dictset_id  
#                     dictionary[dict_text] = (dict_text, dict_id)
                    dictionary[dict_text] = (x, dict_id)
    print("dictionary length:",len(dictionary))
    return dictionary
    

def passCount(dbe, passSetID):
    '''Not used anymore.'''
    query = '''SELECT count(*) FROM passwords WHERE pwset_id = ?'''
    with dbe.cursor() as cur:
        cur.execute(query, (passSetID,))
        count = cur.fetchone()[0]
    return count
            
def getFreq (dbe, word):
    return 0 if word not in ngrams else ngrams[word]
    
#     return trie.getFrequency(theWord)
        
#    query = '''SELECT MAX(freq) from COCA_wordlist WHERE word = ?'''
#    with dbe.cursor() as cur:
#        cur.execute(query, (theWord,))
#        freq = cur.fetchone()[0]
#        if not freq:
#            freq = 0
#    return freq;

def getBigramFreq (dbe, word1, word2):
    key = ' '.join([word1, word2])
    return 0 if key not in ngrams else ngrams[key]
 
#     return trie.getFrequency(word1+' '+word2)

#    query = '''SELECT MAX(freq) from bigrams WHERE word1 = ? and word2 = ?'''
#    with dbe.cursor() as cur:
#        cur.execute(query, (word1, word2,))
#        freq = cur.fetchone()[0]
#        if not freq:
#            freq = 0
#    return freq;

def getTrigramFreq (dbe, word1, word2, word3):
    key = ' '.join([word1, word2, word3])
    return 0 if key not in ngrams else ngrams[key]

#     return trie.getFrequency(word1+' '+word2+' '+word3)

#    query = '''SELECT MAX(freq) from trigrams WHERE word1 = ? and word2 = ? and word3=?'''
#    with dbe.cursor() as cur:
#        cur.execute(query, (word1, word2, word3))
#        freq = cur.fetchone()[0]
#        if not freq:
#            freq = 0
#    return freq;
