import oursql
from queries import *

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
        query = '''SELECT count(*) FROM passwords WHERE pwset_id = ?'''
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
 
        # no more using ids for delimiting the results window, due to the ORDER BY clause
        print 'retrieving passwords from db. offset: {} quantity: {} ...'.format(self._lowBounds, self._size) 
        query = '''SELECT pass_id, pass_text FROM passwords WHERE pwset_id = ?
                ORDER BY pass_text LIMIT ? OFFSET ?'''
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
            cur.execute(query, plain_query=True)
            self._last_id = cur.fetchone() #gets the last id in the results.
            self._last_id = self._last_id[0]
        if self._last_id is None:
            self._last_id = 0 #this is a protection against when the output db (sets) is empty.
    
#     def __del__(self):
#         '''This is called when the object is trying to be deleted, to ensure that it's buffer is written out to disk.'''
#         if self._count > 0:
#             print("Del called, flushing write buffer.")
#             self._flush()
    
    def _flush(self):
        '''The function that coordinates the commit of the internal data store to the sql store.'''
        query1 = '''INSERT INTO sets (pass_id, set_pw) VALUES (?,?);'''
        query2 = '''SELECT (set_id) FROM sets WHERE set_id > ?;'''
        query3 = '''INSERT INTO set_contains (set_id, dict_id, s_index, e_index) VALUES (?,?,?,?)'''
        # example:
        # (15, ([[('too', 0, 3), ('hot', 3, 6)], [('too', 0, 3), ('ott', 4, 7)]], 6))
        print ("in _flush function")
        with self._db.cursor() as cur:
            stage1 = self._genStage1()
            cur.execute("SET autocommit = 0;", plain_query=True)
            cur.execute("SET unique_checks = 0;", plain_query=True)
            cur.execute("SET foreign_key_checks = 0;", plain_query=True)
            print("Stage 1 Commit Starting.")
            cur.executemany(query1, stage1) #commit the stage1
            cur.execute("COMMIT;", plain_query=True)
            print("Stage 1 Commit Complete.")
            cur.execute(query2, (self._last_id,)) #retrieve all the newly created result IDd
            set_ids = [x[0] for x in cur.fetchall()] #buffer them locally.
            self._last_id = max(set_ids) #reset the last_id field to the max of the returned ones.
            #pair and create the stage2 commit.
            set_ids = sorted(set_ids)
            print("sorted the set_ids")
            if len(set_ids) != len(stage1):
                raise ValueError('something dun broke.')
        #with self._db.cursor() as cur:
            stage2 = self._genStage2(set_ids)
            print("Stage 2 Commit Starting.")
            cur.executemany(query3, stage2)
            cur.execute("COMMIT;", plain_query=True)
            print("Stage 2 Commit Complete.")
            cur.execute("SET autocommit = 1;", plain_query=True)
            cur.execute("SET unique_checks = 1;", plain_query=True)
            cur.execute("SET foreign_key_checks = 1;", plain_query=True)
            self._data = list()
        self._count = 0

                
    def _genStage1(self):
        '''Generates the package of data for the stage1 commit into the database.'''
        stage1 = list()
        for result in self._data:
            pass_id = result[0]
            result = result[1][0] #don't care about result length field.
            for rset in result: #walks through the sets of results.
                stage1.append((pass_id, self._genSetPW(rset))) #smooshes the results into a tuple.
        return stage1
    
    def _genStage2(self, setIDs):
        '''Generates the package of data for stage2 commit into db.'''
        stage2 = list()
        stage2o = list()

        #-- refresh dictionary (for dynamic entries)
#        self._dictionary = reloadDynamicDictionary( self._db, self._dictionary)
        
        for result in self._data:
            result = result[1][0]
            for rset in result:
                stage2.append(rset)
        for (x,y) in zip(setIDs, stage2):
            for p in y: # y is the list of fragments of a password
                # p is a tuple like (fragment, start_index, end_index)
                try :
                    stage2o.append((x, self._dictionary[p[0]][1], p[1], p[2]))
                except KeyError, e: # if key fragment not found in memory, go to db
                    try :
                        entry = dictIDbyWord(self._db, [p[0]])
                        stage2o.append((x, entry[p[0]], p[1], p[2]))
                    except :
                        print p[0]
                        print entry
        return stage2o
    
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
