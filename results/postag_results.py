"""
Outputs a random sample of certain size with the results of POS tagging.
"""

import oursql
import random
import csv

SIZE = 5000  # Sample's size
COMMIT = '25b8f6ecf4' # version of pwd_classifier that tagged this sample
#EXTENT = 500000 # Range of values. Depending on how many sets were computed.  

def connect():
    return oursql.connect(host='localhost', user='root', passwd='root', db='passwords', raise_on_warnings=False, charset='utf8', use_unicode=True, port=3306)

def extent(conn):
    q = "SELECT set_id FROM sets ORDER BY set_id DESC"
    c = conn.cursor(plain_query=True)
    c.execute(q)
    return c.fetchone()[0]

if __name__ == '__main__':
    random.seed()
    
    db = connect()
    
    query = """select sets.set_id, set_pw, dictionary.dict_id, dict_text, dictset_id, pos  
    from set_contains 
    left join sets on set_contains.set_id = sets.set_id 
    left join dictionary on set_contains.dict_id = dictionary.dict_id
    where set_contains.set_id in ({});"""
    ex = extent(db)
    ids = random.sample(range(0, ex), SIZE)
    ids = str(ids)[1:-1]
    cursor = db.cursor(plain_query=True)
    cursor.execute(query.format(ids))
    
    sample_filename = 'pos/pos-sample-{}-{}.csv'.format(SIZE, COMMIT)
    csv_writer = csv.writer(open(sample_filename,"wb"), dialect='excel-tab')    
    for line in cursor.fetchall():
        csv_writer.writerow(line)
    
    ids_filename = 'pos/random-ids-{}-{}.txt'.format(SIZE, ex) 
    ids_file = open(ids_filename, 'wb')
    ids_file.write(ids)
    ids_file.close()
    
    
    