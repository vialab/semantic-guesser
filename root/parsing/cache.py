import oursql
from queries import *
import sys
import time

class pwReadCache(object):
    '''A class to cache/buffer the SQL reads from the database, to speed up the process.'''
    def __init__(self, sqleng, pwsetID, size=10000, initial=0):
        '''Provides an iterator interface to a buffer. Implementation of More Magic.'''
        if (size <= 0):
            raise ValueError("size must be over 0.")
        self._db = sqleng
        self._size = size
        self._tuplelist = list()
        self._lowBounds = initial
        self._highBounds = self._lowBounds + self._size
        self._pwsetID = pwsetID
        query = '''SELECT count(*) FROM passwords WHERE pwset_id = %s'''
        with self._db.cursor() as cur:
            cur.execute(query, (self._pwsetID,))
            self._count = cur.fetchone()[0] #grabs the tuple count of the table.

    def __iter__(self):
        '''Used to allow the with construct'''
        exit = False
        while (True):
            if self._refill() is False:
                exit = True
            for x in self._tuplelist:
                yield x
            if exit is True:
                break

    def _refill(self):
        '''Refills the internal cache of tuples.'''

        # Edit 1: no more using ids for delimiting the results window, due to the ORDER BY clause
        # Edit 2: no more using ORDER BY. Assumes the passwords are sorted in the db.
        print 'retrieving passwords from db. offset: {} quantity: {} ...'.format(self._lowBounds, self._size)
        query = "SELECT pass_id, pass_text FROM passwords WHERE pwset_id = %s " \
            "LIMIT %s OFFSET %s"
#       query = '''SELECT pass_id, pass_text FROM passwords WHERE pwset_id = ?
#               ORDER BY pass_id LIMIT ? OFFSET ?'''
        self._tuplelist = list()
        with self._db.cursor() as cur:
            cur.execute(query, (self._pwsetID, self._size, self._lowBounds))
            res = cur.fetchall()
            for pass_id, pass_text in res:
                self._tuplelist.append((pass_id,pass_text))
        self._lowBounds = self._highBounds
        self._highBounds += self._size
        print 'passwords successfully retrieved.'
        if self._lowBounds > self._count:
            return False
        else:
            return True # marks that there's no more in the DB


class WriteBuffer(object):
    '''A buffering class for sql writes, to speed everything up nicely.'''
    def __init__(self, dbsql, dictionary, flushCount=10000):
        '''dbsql is the connection from the library. dictionary is a link to the dictionary object being used.'''
        self._db = dbsql
        if flushCount > 0: self._flushCount = flushCount
        else: raise ValueError('flush count has to be greater than 0')
        self._data = list()
        self._count = 0
        self._dictionary = dictionary
        query = '''SELECT max(set_id) FROM sets;'''
        with self._db.cursor() as cur:
            cur.execute(query)
            self._last_id = cur.fetchone() #gets the last id in the results.
            self._last_id = self._last_id[0]
        if self._last_id is None:
            self._last_id = 0 #this is a protection against when the output db (sets) is empty.


    def _flush(self):
        '''The function that coordinates the commit of the internal data store to the sql store.'''
        t0 = time.time()
        query1 = '''INSERT INTO sets (pass_id, set_pw) VALUES (%s, %s);'''
        query2 = '''SELECT max(set_id) FROM sets;'''
        query3 = '''INSERT INTO set_contains (set_id, dict_id, s_index, e_index) VALUES (%s,%s,%s,%s)'''
        # example:
        # (15, ([[('too', 0, 3), ('hot', 3, 6)], [('too', 0, 3), ('ott', 4, 7)]], 6))
        print ("in _flush function")
        with self._db.cursor() as cur:
            stage1 = self._genStage1()
            cur.execute("SET autocommit = 0;")
            cur.execute("SET unique_checks = 0;")
            cur.execute("SET foreign_key_checks = 0;")
            print("Stage 1 Commit Starting.")
            cur.executemany(query1, stage1) #commit the stage1
            cur.execute("COMMIT;")
            print("Stage 1 Commit Complete.")
            cur.execute(query2) #retrieve the last set_id added

            self._last_id = cur.fetchone()[0] #reset the last_id field

            stage2 = self._genStage2(self._last_id - len(stage1) + 1)

            print("Stage 2 Commit Starting.")
            cur.executemany(query3, stage2)
            cur.execute("COMMIT;")
            print("Stage 2 Commit Complete.")
            cur.execute("SET autocommit = 1;")
            cur.execute("SET unique_checks = 1;")
            cur.execute("SET foreign_key_checks = 1;")
            self._data = list()
        self._count = 0
        t1 = time.time()
        print "Flush took {}.".format(t1-t0)


    def _genStage1(self):
        '''Generates the package of data for the stage1 commit into the database.'''
        stage1 = list()
        for result in self._data:
            pass_id = result[0]
            result = result[1][0] #don't care about result length field.
            for rset in result: #walks through the sets of results.
                stage1.append((pass_id, self._genSetPW(rset))) #smooshes the results into a tuple.
        return stage1

    def _genStage2(self, startingID):
        '''Generates the package of data for stage2 commit into db.'''
        #-- refresh dictionary (for dynamic entries)
#        self._dictionary = reloadDynamicDictionary( self._db, self._dictionary)
        stage2 = []

        currID = startingID

        for result in self._data:
            result = result[1][0]
            for rset in result: # rset is the list of fragments of a password
                for word, sIndex, eIndex in rset:
                    try:
                        stage2.append((currID, self._dictionary[word][1], sIndex, eIndex))
                    except KeyError, e: # if key fragment not found in memory, go to db
                        try:
                            entry = dictIDbyWord(self._db, [word])
                            stage2.append((currID, entry[word], sIndex, eIndex))
                        except:
                            print "Word {} not found in memory and db...".format(word)
                            print entry
                currID += 1

        return stage2

    def _genSetPW(self, tups):
        '''Simply gets the password for the set from the list of words.'''
        return ''.join([x[0] for x in tups])

    def addCommit(self, pwID, resultSet):
        '''Adds data to the internal store to be flushed at a later time,
        when flushCount is exceeded, or object is deleted.
        Return True if this entry triggered flushing; False otherwise.'''
        self._data.append((pwID, resultSet))
        self._count += 1
        if self._count > self._flushCount:
            self._flush()
            return True
        return False
