'''
Created on 2013-06-28

@author: rafa
'''

import argparse
import guesser
from parsing import testWordMiner as parser
import grammar
import database
from pos_tagger import BackoffTagger
import os
import sys
import util

base_structures = dict()
tag_dicts = dict()

# class Terminal:
#     def __init__(self, word, p):
#         self.word = word
#         self.p = p
# 
#     def __eq__(self, other):
#         if isinstance(other, self.__class__):
#             return self.word == other.word
#         else:
#             return False
#     
#     def __ne__(self, other):
#         return not self.__eq__(other)
#     
#     def __gt__(self, other):
#         return self.word > other.word

def options():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=argparse.FileType('r'), help='a list of clear text passwords')
    return parser.parse_args()

def segment(password, dictionary, db):
    permutations = parser.permuteString(password.lower())
    words = list()
    for x in permutations:
        if x[0] in dictionary:
            words.append(x)

    candidates = parser.generateCandidates(words, password)
    # candidates comes pretty raw. we need a representation that
    # stores dictset_id, pos, etc... for semantic classification
    candidates = transform(candidates, dictionary)
    
    for c in candidates:
        processGaps(db, c, password)
    
    if candidates == []:
        candidates = [processGaps(db, [], password)]
    
    return [ [s[0] for s in c] for c in candidates]

def processGaps(db, segmentation, password):
    if (segmentation == []):
        dynDictionaryID = parser.tagChunk(password)
        segment = database.Fragment(0, dynDictionaryID, password)
        segmentation.append((segment, 0, len(password)))
        return segmentation
          
    lastEndIndex = 0
    nextStartIndex = 0
    i = 0
    try:
        for x in segmentation:
            (xw, xs, xe) = x
            nextStartIndex = xs
            if (nextStartIndex > lastEndIndex):
                # find the gap, see if it is a #/sc chunk
                segmentation = addInTheGapsHelper(db, segmentation, i, password, lastEndIndex, nextStartIndex)
            lastEndIndex = xe
            i = i + 1
        if (len(password) > lastEndIndex):
                segmentation = addInTheGapsHelper(db, segmentation, i, password, lastEndIndex, len(password))
    except :
        print ("Warning: caught unknown error in addTheGaps -- resultSet=", segmentation, "password", password)

    return segmentation

def addInTheGapsHelper(db, segmentation, i, password, lastEndIndex, nextStartIndex):
    # attention for the strip() call! space info is lost! who cares?!
    gap = password[lastEndIndex:nextStartIndex].strip()
    
    dynDictionaryID = parser.tagChunk(gap) 
    
    if ((len(gap) > 0) and (dynDictionaryID > 0)):
        segment = database.Fragment(0, dynDictionaryID, gap)
        segmentation.insert(i, (segment, lastEndIndex, nextStartIndex))
        
    return segmentation

def transform(seg_candidates, dictionary):
    """ Takes a segmentation candidate from testWordMiner.generateCandidates and
    transforms into simple list of list of tuples like (segment, sindex, eindex)"""
    
    result = []
    
    for (segmentations, coverage) in seg_candidates:
        for s in segmentations:
            tmp = []
            for (segment, s_index, e_index) in s:
                tmp.append((database.Fragment(0, dictionary[segment][0], segment), s_index, e_index))
            result.append(tmp)
            
    return result

def probability(base_struct, segmentation):
    if base_struct in base_structures:
        p = base_structures[base_struct]
    else:
        return 0
    
    tags = guesser.unpack(base_struct)
    
    for i, tag in enumerate(tags):
        word = segmentation[i].word
        terminals = tag_dicts[tag]
         
        if word in terminals:
            p *= terminals[word]
        else:
            return 0
        
    return p

def is_guessable(pattern, segments):
    answer = True
    if pattern in base_structures:
        tags = guesser.unpack(pattern)
        for i, segment in enumerate(segments):
            # if segment.word in not among the words of the tag 
            if segment.word not in tag_dicts[tags[i]]:
                answer = False
                break
    else:
        answer = False
    
    return answer

def load_grammar(base_structures, tag_dicts):
    grammar_dir = util.abspath('grammar')
    
#     with Timer('Loading grammar'):
    with open(os.path.join(grammar_dir, 'rules.txt')) as f:
        #regex = '\(([^()]+)\)'
        for line in f:
            fields = line.split()
#             tags = tuple(re.findall(regex, fields[0]))  # extracts the tags
            tags = fields[0]
            base_structures[tags] = float(fields[1])  # maps grammar rule (tags) to probability
    
    tagdicts_dir = os.path.join(grammar_dir, 'seg_dist')
    
#     with Timer('Loading tag dictionaries'):
    for fname in os.listdir(tagdicts_dir):
        if not fname.endswith('.txt'): continue
        
        with open(os.path.join(tagdicts_dir, fname)) as f:
            tag = fname.replace('.txt', '')
            words = dict()
            for line in f:
                fields = line.split('\t')
                try:
                    words[fields[0]] = float(fields[1])
                except:
                    sys.stderr.write("error inserting {} in the tag dictionary {}\n".format(fields, tag))
                
            tag_dicts[tag] = words 

def pos_tag(tagger, fragments):
    tags = tagger.tag([ f.word for f in fragments if f.dictset_id <= 90])
    for j in range(len(fragments)):
        if fragments[j].dictset_id > 90:
            fragments[j].pos = None
        else:
            fragments[j].pos = tags.pop(0)[1]

def main(base_structures, tag_dicts, file):
    db = parser.connectToDb()
    dictionary = parser.getDictionary(db, parser.dict_sets)
    pos_tagger = BackoffTagger()
    
    guessable_count = 0
    
    i = 0
    for l in file:
        password = l.rstrip()
        
        if not password : continue
        
        segmentations = segment(password, dictionary, db)
        
        most_probable_seg = (None, 0)  # most probable rule that generates the password in the grammar -> (base_struct, probability)
        
        for s in segmentations:
            pos_tag(pos_tagger, s)
            
            base_struct = grammar.pattern(s)
            
            if base_struct in base_structures and base_structures[base_struct] < most_probable_seg[1]:
                continue
            
            p = probability(base_struct, s)
            
            if p > most_probable_seg[1]:
                most_probable_seg = (base_struct, p)
        
        guessable = most_probable_seg[0] is not None
                
        if guessable:
            guessable_count += 1 
        
        print "{}\t{}\t{}".format(password, most_probable_seg[1], most_probable_seg[0] if most_probable_seg[0] else "")
        
        i += 1
#        if i >= 1000: break
        
    
    # print # of guessable passwords
    print "{} guessable passwords out of {}, ({:%})".format(guessable_count, i, float(guessable_count)/i)
    
if __name__ == '__main__':
    opt = options() 
    load_grammar(base_structures, tag_dicts)
    main(base_structures, tag_dicts, opt.file)
