'''
Created on Feb 24, 2012

@author: Rafa
'''

import MySQLdb.cursors
import threading

class PwdDb():
    
    def __init__(self):
        self.saving_cache = []
        self.cachelimit   = 100000
        self.cachecount   = 0
        
        # different connections for reading and saving
        self.conn_read = self.connection()
        self.conn_save = self.connection()
        
        self.readcursor = self.conn_read.cursor() 
        self.savecursor = self.conn_save.cursor()
        
        self.readcursor.execute("SELECT * FROM sets ORDER BY set_id DESC LIMIT 1;")
        self.sets_size = self.readcursor.fetchone()["set_id"]
        self.readcursor.close()
        
        self.readcursor = self.conn_read.cursor()
        
        self.readcursor.execute("SELECT sets.set_id AS set_id, " + \
                            "set_contains.id AS set_contains_id, dict_text, dictset_id, " + \
                            "pos, sentiment, synset, category, dictset_id " + \
                            "FROM set_contains LEFT JOIN sets ON set_contains.set_id = sets.set_id " +\
                            "LEFT JOIN dictionary ON set_contains.dict_id = dictionary.dict_id; ") 
        self.row = self.readcursor.fetchone()
        
    
    def connection(self):
        return MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="root",
                     passwd="root",
                     db="passwords",
                     cursorclass = MySQLdb.cursors.SSDictCursor) # stores result in the server. records as dict
    
    def nextPwd(self):
        if (self.row is None): 
            return None
        old_pwd_id = self.row["set_id"]
        pwd_id     = old_pwd_id
        pwd = []
        while (pwd_id == old_pwd_id):
            wo = Fragment(self.row["set_contains_id"], self.row["dictset_id"], self.row["dict_text"],
                                self.row["pos"], self.row["sentiment"], self.row["synset"],
                                self.row["category"])
            pwd.append(wo)
            self.row = self.readcursor.fetchone()
            if (self.row is None):  break
            else:                   pwd_id = self.row["set_id"]
        return pwd
        
    # TODO: Get rid of cachecount    
    def save(self, wo, cache=False):
        if cache :
            self.saving_cache.append((wo.pos, wo.senti, wo.synsets, wo.id))
            self.cachecount += 1
            if self.cachecount >= self.cachelimit :
                self.flush_save()
                self.cachecount = 0
        else :
            self.savecursor.execute("UPDATE set_contains set pos=%s, sentiment=%s, synset=%s where id=%s;", (wo.pos, wo.senti, wo.synsets, wo.id))

#    def flush_save(self):
#        print "updating {} records on the database...".format(len(self.saving_cache))
#        u = Updater("UPDATE set_contains set pos=%s, sentiment=%s, synset=%s where id=%s;", self.saving_cache, self.cachelimit, self.conn_save, self.savecursor)
#        u.start()
    
    def flush_save (self):
        print "updating {} records on the database...".format(len(self.saving_cache))
        self.conn_save.ping(True) # if connections has died, ressurect it
        self.savecursor.executemany("UPDATE set_contains set pos=%s, sentiment=%s, synset=%s where id=%s;", self.saving_cache)
        self.conn_save.commit()
        self.saving_cache = []
    
    def saveCategory(self, wo):
        self.savecursor.execute("UPDATE set_contains set category=%s where id=%s;",
                             (wo.category, wo.id))
        
    def hasNext(self):
        return self.row is not None
    
    def finish(self):
        if len(self.saving_cache)>0 :
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


