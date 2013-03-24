'''
Created on Mar 13, 2012

@author: Rafa
'''

import MySQLdb.cursors
import csv

def main():
    conn = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="root", # your username
                     passwd="root", # your password
                     db="passwords",
                     cursorclass = MySQLdb.cursors.SSCursor)
    query = "SELECT s.set_id, dict.dict_text, s.category, s.sent, s.pos FROM passwords.set_contains as s  " + \
                            "left join dictionary as dict on dict.dict_id=s.dict_id;"
    cursor = conn.cursor()
    cursor.execute(query)
    
    nResults = 30000
    csv_writer = csv.writer(open("result_set.csv","wb"), dialect='excel')
    for i in range(nResults):
        row = [ v for v in cursor.fetchone()]
        row = [x if x is not None else "" for x in row]
        csv_writer.writerow(row)
    print "the end."
    
if __name__ == '__main__':
    main()