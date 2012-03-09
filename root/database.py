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
                            "set_contains.id AS set_contains_id, dictionary.dict_text " + \
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
            wo = WordOccurrence(self.row["set_contains_id"], self.row["dict_text"])
            pwd.append(wo)
            self.row = self.cur.fetchone()
            if (self.row is None):  break
            else:                   pwd_id = self.row["set_id"]
        return pwd
        
        
    def save(self, wo):
        self.saveCur.execute("UPDATE set_contains set pos=%s where id=%s;", (wo.pos, wo.id))
    
    def hasNext(self):
        return self.row is not None
    
    def finish(self):
        self.conn_save.commit()
        self.saveCur.close()
        self.conn_save.close()
        self.conn_read.close()
    
class WordOccurrence():
    
    def __init__(self, id, word, pos=''):
        self.id = id
        self.word = word
        self.pos = pos

    def __str__(self):
        return self.word
    
    def __repr__(self):
        return self.word

#db = PwdDb()
#for n in range(50):
#    pwd = db.nextPwd()
#    print pwd

