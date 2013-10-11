from database import PwdDb
import re

if __name__ == "__main__":
    db = PwdDb()

    histogram = [0]*10

    alpha_regex = r'[a-zA-Z]'

#     for i in range(10000):
    while db.hasNext():
        fragments = db.nextPwd()
        
#         password = fragments[0].password
        # reduces password to its alphabetic chars
        password = ''.join(re.findall(alpha_regex, fragments[0].password))


        # WE'RE SKIPPING PASSWORDS THAT DO NOT CONTAIN ALPHABETIC CHARACTERS
        if not password: continue
#         if not re.findall(alpha_regex, password):
#             continue
        
        nongap = ''.join([f.word for f in fragments if not f.is_gap()])
    
        coverage = float(len(nongap))/len(password)
        
        if coverage >= 1:
            histogram[9] += 1
        else:
            histogram[int(coverage*10)] += 1

#         print fragments[0].password
#         print password
#         print password
#         print nongap
#         print coverage
#         print int(coverage*10)
                
    
    total = sum(histogram)
    percent_hist = [ (float(count)/total)*100 for count in histogram]

    print histogram
    print percent_hist