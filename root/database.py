'''
Created on Feb 24, 2012

@author: 100457636
'''

import MySQLdb.cursors


class PwdDb():
    
    def __init__(self):
        # different connections for reading and saving
        self.conn_read = self.connection()
        self.conn_save = self.connection()
        
        self.cur = self.conn_read.cursor() 
        self.saveCur = self.conn_save.cursor()
        
        # Use all the SQL you like
        self.cur.execute("SELECT sets.set_id AS set_id, " + \
                            "set_contains.id AS set_contains_id, dictionary.dict_text, " + \
                            "pos, sent, synsets, category " + \
                            "FROM set_contains LEFT JOIN sets ON set_contains.set_id = sets.set_id " +\
                            "LEFT JOIN dictionary ON set_contains.dict_id = dictionary.dict_id; ") 
        self.row = self.cur.fetchone()
        # print all the first cell of all the rows
#       for row in self.cur.fetchall :
#           print row[2]
    
    def connection(self):
        return MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="root", # your username
                     passwd="root", # your password
                     db="passwords",
                     cursorclass = MySQLdb.cursors.SSDictCursor)
    
    def nextPwd(self):
        if (self.row is None): 
            return None
        old_pwd_id = self.row["set_id"]
        pwd_id     = old_pwd_id
        pwd = []
        while (pwd_id == old_pwd_id):
            wo = WordOccurrence(self.row["set_contains_id"], self.row["dict_text"],
                                self.row["pos"], self.row["sent"], self.row["synsets"],
                                self.row["category"])
            pwd.append(wo)
            self.row = self.cur.fetchone()
            if (self.row is None):  break
            else:                   pwd_id = self.row["set_id"]
        return pwd
        
        
    def save(self, wo):
#        pos = wo.pos if wo.pos is not None else 'null'
#        senti = wo.senti if wo.senti is not None else 'null'
#        synsets = wo.synsets if wo.synsets is not None else 'null'
        
#        q = "UPDATE set_contains set pos=%s, sent=%s, synsets=%d where id=%d;" % (pos, senti, synsets, wo.id)
#        print q
        self.saveCur.execute("UPDATE set_contains set pos=%s, sent=%s, synsets=%s where id=%s;",
                             (wo.pos, wo.senti, wo.synsets, wo.id))
    
    def saveCategory(self, wo):
        self.saveCur.execute("UPDATE set_contains set category=%s where id=%s;",
                             (wo.category, wo.id))
        
    def hasNext(self):
        return self.row is not None
    
    def finish(self):
        self.conn_save.commit()
        self.saveCur.close()
        self.conn_save.close()
        self.conn_read.close()
    
class WordOccurrence():
    
    def __init__(self, ident, word, pos=None, senti=None, synsets=None, category=None):
        self.id = ident
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
#wo = WordOccurrence(id, "rafa", pos, senti, synsets)
#db.save(wo)
#db.finish()
#db = PwdDb()


