"""
This script generates a context-free grammar
that captures the semantic patterns of a list of
passwords.

It's based on Weir (2009)*.

*http://dl.acm.org/citation.cfm?id=1608146

Created on Apr 18, 2013

"""

__author__ = 'rafa'

from database import PwdDb
import semantics
from cut import wagner
import sys
import traceback
from nltk.probability import FreqDist, ConditionalFreqDist
from timer import Timer

node_index = dict()

class DictionaryTag:
    map = {10: 'month',
           20: 'fname',
           30: 'mname',
           40: 'surname',
           50: 'country',
           60: 'city',
           200: 'number',
           201: 'num+special',
           202: 'special',
           203: 'char',
           204: 'all_mixed'}

    @classmethod
    def get(cls, id):
        return DictionaryTag.map[id] if id in DictionaryTag.map else None
    
    @classmethod
    def gaps(cls):
        return [ v for k, v in DictionaryTag.map.items() if k > 90]

def generalize(synset):
    """ Generalizes a synset based on a tree cut. """

    if synset.pos not in ['v', 'n']:
        return None

    # an internal node is split into a node representing the class and other
    # representing the sense. The former's name starts with 's.'
    key = synset.name if is_leaf(synset) else 's.' + synset.name
        
    node = node_index[key]
    if not node:
        print "{} could not be generalized".format(key)
        return None
    
    path = node.path()
    
    # given the hypernym path of a synset, selects the node that belongs to the cut
    for parent in path:
        if parent.cut:
            return parent.key
        

def is_leaf(synset):
    return not bool(synset.hyponyms())


def classify(segment):

    if segment.pos in ['NP', None] and segment.dictset_id in DictionaryTag.map:
        tag = DictionaryTag.map[segment.dictset_id]
    else:
        synset = semantics.synset(segment.word, segment.pos)
        if synset is not None:
            # TODO: sometimes generalize is returning None. #fixit 
            tag = '{}_{}'.format(segment.pos, generalize(synset)) 
        else:
            tag = segment.pos

    return tag


def stringify_pattern(tags):
    return ''.join(['({})'.format(tag) for tag in tags])


def main(db):
    tags_file = open('grammar/debug.txt', 'w+')
    
    patterns_dist = FreqDist()  # distribution of patterns
    segments_dist = ConditionalFreqDist()  # distribution of segments, grouped by semantic tag
    
    counter = 0
    
    while db.hasNext():
        segments = db.nextPwd()
        password = ''.join([s.word for s in segments])
        tags     = [] 

        for s in segments:  # semantic tags
            tag = classify(s)
            tags.append(tag)
            segments_dist[tag].inc(s.word)
            
        pattern = stringify_pattern(tags)
        
        patterns_dist.inc(pattern)
        
        for i in range(len(segments)):
            tags_file.write("{}\t{}\t{}\t{}\n".format(password, segments[i].word, tags[i], pattern))

        counter += 1
        if counter % 100000 == 0:
            print "{} passwords processed so far ({:.2%})... ".format(counter, float(counter)/db.sets_size)
         
    tags_file.close()
        
    with open('grammar/rules.txt', 'w+') as f:
        total = patterns_dist.N()
#         items = sorted(items, key=lambda x: x[1], reverse=True)
        for pattern, freq in patterns_dist.items():
            f.write('{}\t{}\n'.format(pattern, float(freq)/total))
    
    for tag in segments_dist.keys():
        total = segments_dist[tag].N()
        with open('grammar/seg_dist/'+tag+'.txt', 'w+') as f:
            for k, v  in segments_dist[tag].items():
                f.write("{}\t{}\n".format(k, float(v)/total))
    

# TODO: Option for online version (calculation of everything on the fly) and from db
if __name__ == '__main__':
    try:
        nouns_tree = semantics.load_semantictree('n')
        verbs_tree = semantics.load_semantictree('v')

        cut = wagner.findcut(nouns_tree, 5000)
        for c in cut: c.cut = True
        
        cut = wagner.findcut(verbs_tree, 5000)
        for c in cut: c.cut = True
        
        flat = nouns_tree.flat() + verbs_tree.flat()
        
        for node in flat:
            if node.key not in node_index:
                node_index[node.key] = node
        
        with Timer('grammar generation'):
            db = PwdDb(100, random=True)
            try:
                main(db)
            except KeyboardInterrupt:
                db.finish()
                raise
    except:
        e = sys.exc_info()[0]
        traceback.print_exc()
        sys.exit(1)
    
    