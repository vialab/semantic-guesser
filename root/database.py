"""
Provides a class to read and write passwords and their attributes to the database,
and functions to retrieve other information from the db, such as dictionary words.
Created on Feb 24, 2012

@author: Rafa
"""

import MySQLdb.cursors
import threading
import query
import random


def connection():
    return MySQLdb.connect(host="localhost",  # your host, usually localhost
                 user="rafa",  # your username
                 passwd="teamopasswords",  # your password
                 db="passwords",
                 cursorclass=MySQLdb.cursors.SSDictCursor)  # stores result in the server. records as dict


def names():
    cursor = connection().cursor()
    cursor.execute(query.names)
    return [row['dict_text'] for row in cursor.fetchall()]


class PwdDb():
    """ A few notes:
    
    - caching is implemented for saving, not for reading
    - as for reading, the result set is kept in the server (SSDictCursor)
      and the rows are fetched one by one 
    - the sample param in the constructor is important when planning to fetch only
      a sample. The MySQLDb docs mention: "you MUST retrieve the entire result set and
      close() the cursor before additional queries can be peformed on
      the connection."
      If you don't retrieve the entire result set before calling finish(), it will take
      forever to close the connection.
      
    """
    
    def __init__(self, sample=None, random=False, save_cachesize=100000, offset=0):
        self.savebuffer_size = save_cachesize
        self.readbuffer_size = 100000

        self.readbuffer = []
        self.row = None  # holds the next row to be retrieved by nextPwd(), 
        self.readpointer = -1  # always points to the last row stored in self.row 
        
        self.savebuffer  = []
         
        # different connections for reading and saving
        self._init_read_cursor(offset, sample, random)
        self._init_save_cursor()
    
    def _init_read_cursor(self, offset, limit, random):
        self.conn_read = connection()
        self.readcursor = self.conn_read.cursor()
        
        # getting number of 'sets' (or segments) 
        self.readcursor.execute("SELECT * FROM sets ORDER BY set_id DESC LIMIT 1;")
        self.sets_size = self.readcursor.fetchone()["set_id"]
        self.readcursor.close()

        self.readcursor = self.conn_read.cursor()
        
        bounds = [offset, limit] if limit else None
        random_ids = self.random_ids(0, self.max_pass_id(), limit) if random else None
        
        self.readcursor.execute(query.segments(bounds, random_ids))

        # fetching the first password
        self.fill_buffer()
        self.row = self.fetchone()

    def fill_buffer(self):
        self.readbuffer  = self.readcursor.fetchmany(self.readbuffer_size)
#         self.readbuffer  = [self.readcursor.fetchone()]
        self.readpointer = -1

    def fetchone(self):
        try:
            self.readpointer += 1
            return self.readbuffer[self.readpointer]
        except:
            self.fill_buffer()
            if len(self.readbuffer) < 1:
                self.readcursor.close()
                return None
            else:
                self.readpointer += 1
                return self.readbuffer[self.readpointer]
        
    def random_ids(self, min, max, size):
        return random.sample(range(min, max), size)

    def max_pass_id(self):
        c = self.conn_read.cursor()
        c.execute(query.max_pass_id())
        return c.fetchone()['max']

    def _init_save_cursor(self):
        self.conn_save = connection()
        self.savecursor = self.conn_save.cursor()
        

    def nextPwd(self):
        if self.row is None:
            return None

        pwd_id = old_pwd_id = self.row["set_id"]
        pwd = []

        while pwd_id == old_pwd_id:
            wo = Fragment(self.row["set_contains_id"], self.row["dictset_id"], self.row["dict_text"],
                                self.row["pos"], self.row["sentiment"], self.row["synset"],
                                self.row["category"], self.row["pass_text"], self.row["s_index"],
                                self.row["e_index"])
            pwd.append(wo)

            self.row = self.fetchone()
            if self.row is None:
                break
            else:
                pwd_id = self.row["set_id"]

        return pwd
        
    def save(self, wo, cache=False):
        if cache:
            self.savebuffer.append((wo.pos, wo.senti, wo.synsets, wo.id))
            if len(self.savebuffer) >= self.savebuffer_size:
                self.flush_save()
        else:
            self.savecursor.execute("UPDATE set_contains set pos=%s, sentiment=%s, synset=%s where id=%s;", (wo.pos, wo.senti, wo.synsets, wo.id))

#    def flush_save(self):
#        print "updating {} records on the database...".format(len(self.savsave_buffer#
#    u = Updater("UPDATE set_contains set pos=%s, sentiment=%s, synset=%s where id=%s;",
# self.savesave_bufferf.cachelimit, self.conn_save, self.savecursor)
#        u.start()
    
    def flush_save (self):
        print "updating {} records on the database...".format(len(self.savebuffer)) 
        self.conn_save.ping(True) # if connection has died, ressurect it
        self.savecursor.executemany("UPDATE set_contains set pos=%s, sentiment=%s, synset=%s where id=%s;", self.savebuffer)
        self.conn_save.commit()
        self.savebuffer = []
        
    def saveCategory(self, wo):
        self.savecursor.execute("UPDATE set_contains set category=%s where id=%s;",
                             (wo.category, wo.id))
        
    def hasNext(self):
        return self.row is not None
    
    def finish(self):
        if len(self.savebuffer) > 0:
            self.flush_save()
        self.readcursor.close()
        self.savecursor.close()
        self.conn_save.close()
        self.conn_read.close()


# class Updater(threading.Thread):
#     def __init__(self, query, cache, cachelimit, conn, cursor) :
#         threading.Thread.__init__(self)
#         self.query = query
#         self.cache = cache
#         self.cachelimit = cachelimit
#         self.conn = conn
#         self.cursor = cursor
# 
#     def run(self):
#         self.cursor.executemany(self.query, self.cache[0:self.cachelimit])
#         self.conn.commit()
#         del self.cache[0:self.cachelimit]
        
 
class Fragment():
    
    def __init__(self, ident, dictset_id, word, pos=None, senti=None, 
                 synsets=None, category=None, password=None, s_index=None, e_index=None):
        self.id = ident
        self.dictset_id = dictset_id
        self.word = word
        self.pos = pos
        self.senti = senti
        self.synsets = synsets
        self.category = category
        self.password = password
        self.s_index = s_index
        self.e_index = e_index

    def __str__(self):
        return self.word
    
    def __repr__(self):
        return self.word

    def is_gap(self):
        return self.dictset_id > 90


#db = PwdDb()
#pos = 'a'
#senti = None
#synsets = None
#id = 1
#
#wo = Fragment(id, "rafa", pos, senti, synsets)
#db.save(wo)
#db.finish()
#db = PwdDb()

#print names()
