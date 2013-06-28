import oursql
import random
import csv

SIZE = 5000  # Sample's size
EXTENT = 500000 # Range of values. Depending on how many sets were computed.  

def connect():
    return oursql.connect(host='localhost', user='root', passwd='root', db='passwords', raise_on_warnings=False, charset='utf8', use_unicode=True, port=3306)

if __name__ == '__main__':
    db = connect()
    random.seed()
    query = """select sets.set_id AS set_id, 
    sets.set_pw AS set_pwd, 
    dictionary.dict_id AS word_id, 
    dictionary.dict_text AS word,
    dictionary.dictset_id AS dictset 
    from set_contains 
    left join sets on set_contains.set_id = sets.set_id 
    left join dictionary on set_contains.dict_id = dictionary.dict_id
    where set_contains.set_id in ({});"""
    
    sample = random.sample(range(0, EXTENT), SIZE)
    
    cursor = db.cursor(plain_query=True)
    cursor.execute(query.format(str(sample)[1:-1]))
    
    csv_writer = csv.writer(open("files/random_result_set5000.csv","wb"), dialect='excel-tab')
    
    for line in cursor.fetchall():
        csv_writer.writerow(line)
    
    
        

     
    
