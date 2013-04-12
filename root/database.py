"""
Created on Feb 24, 2012

@author: Rafa
"""

import MySQLdb.cursors
import threading
import query


class PwdDb():
    """ A few notes:
    
    - caching is implemented for saving, not for reading
    - as for reading, the result set is kept in the server (SSDictCursor)
      and the rows are fetched one by one 
    - the size param in the constructor is important when not planning to fetch only
      a sample. The MySQLDb docs mention: "you MUST retrieve the entire result set and
      close() the cursor before additional queries can be peformed on
      the connection."
      If you don't retrieve the entire result set before calling finish(), it will take
      forever to close the connection.
      
    """
    
    def __init__(self, save_cachesize=100000, offset=0, size=None,):
        self.saving_cache = []
        self.cachelimit = save_cachesize

        # different connections for reading and saving
        self._init_read_cursor(offset, size)
        self._init_save_cursor()

    def _init_read_cursor(self, offset, size):
        self.conn_read = self.connection()
        self.readcursor = self.conn_read.cursor()
        
        # getting number of 'sets' (or fragments) 
        self.readcursor.execute("SELECT * FROM sets ORDER BY set_id DESC LIMIT 1;")
        self.sets_size = self.readcursor.fetchone()["set_id"]
        self.readcursor.close()

        # fetching the first fragment        
        self.readcursor = self.conn_read.cursor()
        bounds = [offset, size] if size else None
        self.readcursor.execute(query.fragments(bounds))
        self.row = self.readcursor.fetchone()

    def _init_save_cursor(self):
        self.conn_save = self.connection()
        self.savecursor = self.conn_save.cursor()
        
    def connection(self):
        return MySQLdb.connect(host="localhost",  # your host, usually localhost
                     user="root",  # your username
                     passwd="root",  # your password
                     db="passwords",
                     cursorclass=MySQLdb.cursors.SSDictCursor)  # stores result in the server. records as dict
    
    def nextPwd(self):
        """
        only_dict - if True, will not return fragments from the dynamic dictionaries

        """
        # TODO: test accomplishing only_dict through WHERE clause

        if self.row is None:
            return None

        pwd_id = old_pwd_id = self.row["set_id"]
        pwd = []

        while pwd_id == old_pwd_id:
            wo = Fragment(self.row["set_contains_id"], self.row["dictset_id"], self.row["dict_text"],
                                self.row["pos"], self.row["sentiment"], self.row["synset"],
                                self.row["category"])
            pwd.append(wo)

            self.row = self.readcursor.fetchone()
            if self.row is None:
                break
            else:
                pwd_id = self.row["set_id"]

        return pwd
        
    def save(self, wo, cache=False):
        if cache:
            self.saving_cache.append((wo.pos, wo.senti, wo.synsets, wo.id))
            if len(self.cache) >= self.cachelimit:
                self.flush_save()
        else:
            self.savecursor.execute("UPDATE set_contains set pos=%s, sentiment=%s, synset=%s where id=%s;", (wo.pos, wo.senti, wo.synsets, wo.id))

#    def flush_save(self):
#        print "updating {} records on the database...".format(len(self.saving_cache))
#        u = Updater("UPDATE set_contains set pos=%s, sentiment=%s, synset=%s where id=%s;",
# self.saving_cache, self.cachelimit, self.conn_save, self.savecursor)
#        u.start()
    
    def flush_save (self):
        print "updating {} records on the database...".format(len(self.saving_cache))
        self.conn_save.ping(True) # if connection has died, ressurect it
        self.savecursor.executemany("UPDATE set_contains set pos=%s, sentiment=%s, synset=%s where id=%s;", self.saving_cache)
        self.conn_save.commit()
        self.saving_cache = []
    
    def saveCategory(self, wo):
        self.savecursor.execute("UPDATE set_contains set category=%s where id=%s;",
                             (wo.category, wo.id))
        
    def hasNext(self):
        return self.row is not None
    
    def finish(self):
        if len(self.saving_cache)>0:
            self.flush_save()
        self.readcursor.close()
        self.savecursor.close()
        self.conn_save.close()
        self.conn_read.close()


class Updater(threading.Thread):
    def __init__(self, query, cache, cachelimit, conn, cursor) :
        threading.Thread.__init__(self)
        self.query = query
        self.cache = cache
        self.cachelimit = cachelimit
        self.conn = conn
        self.cursor = cursor

    def run(self):
        self.cursor.executemany(self.query, self.cache[0:self.cachelimit])
        self.conn.commit()
        del self.cache[0:self.cachelimit]
        
 
class Fragment():
    
    def __init__(self, ident, dictset_id, word, pos=None, senti=None, synsets=None, category=None):
        self.id = ident
        self.dictset_id = dictset_id
        self.word = word
        self.pos = pos
        self.senti = senti
        self.synsets = synsets
        self.category = category

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


