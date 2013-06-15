

from Queue import PriorityQueue
from argparse import ArgumentParser
from timer import Timer
from grammar import DictionaryTag
import util
import re
import os
import sys
import argparse

# from guppy import hpy

base_structures = dict()  # (tag1, tag2, tag3..) : probability 
tag_dicts = dict()  # tag: [(word, p)...]
gaps = DictionaryTag.gaps()

mangle_functions = [str.lower, str.upper, str.title]

def probability(base_struct, tags, terminals):
    p = base_structures[base_struct]
    
    for i, tag in enumerate(tags):
        word_index = terminals[i]
        p *= tag_dicts[tag][word_index][1]
    
    return p


def decode_guess_mangled(p, tags, terminals, pivot):
    """ Returns a list of mangled guesses based on the base struct """
    
    # [True, False, False, True...] where True denotes a tag is gapy
    gap_map = [tag in gaps for tag in tags] 
    if all(gap_map):
        return decode_guess(p, tags, terminals, pivot)
    
    guesses = list()
    
    for f in mangle_functions:
        guess = ''
        
        for i, tag in enumerate(tags):
            word_index = terminals[i]
            
            if gap_map[i]:
                guess += tag_dicts[tag][word_index][0]
            else:
                guess += f(tag_dicts[tag][word_index][0])
        
        guesses.append(guess)
    
    # makes a title guess, since the previous block will only make camel case
    if not gap_map[0] and not all(gap_map[1:]):
        guesses.append(guesses[0].title())
                
    return guesses
 

def decode_guess(p, tags, terminals, pivot):
    result = ''
    for i, tag in enumerate(tags):
        word_index = terminals[i]
        result += tag_dicts[tag][word_index][0]
    
    return [result]


def guess(min_length, max_guesses, mangled):
#     hp = hpy()
#     hp.setrelheap()
    
    queue = PriorityQueue()
    
    decode_function = decode_guess_mangled if mangled else decode_guess 
    
    #with Timer('Initializing priority queue'):
    # initializing the queue
    for b in base_structures.keys():
        tags = unpack(b)
        # the indexes of the most probable terminals relative to the tag dicts
        terminals = tuple([0]*len(tags))
        p = probability(b, tags, terminals)
        pivot = 0
        # NOTE: probability is put negative in the queue to allow higher probability order
        queue.put((-p, b, terminals, pivot))
 
    nguesses = 0  
    while not queue.empty():
        curr = queue.get()

        (p, base_struct, terminals, pivot) = curr
        tags = unpack(base_struct)
        
        gs = decode_function(p, tags, terminals, pivot)
            
        for g in gs: 
            if len(g) >= min_length:
                try:
                    print g
                    nguesses += 1
                    if nguesses >= max_guesses: return
                    # debugging
                    #if nguesses % 1000000 == 0: print queue.qsize()
                except:  # treat errors like "Broken pipe"
                    return
                
        
        for i in range(pivot, len(tags)):
            tag = tags[i]
            next_word_index = terminals[i] + 1
            
            # if possible, replace terminals[i] by the next lower probability value
            if next_word_index < len(tag_dicts[tag]):
                new_terminals = tuple([next_word_index if j == i else t for j, t in enumerate(terminals)])
                new_p = probability(base_struct, tags, new_terminals)
                new_pivot = i
                queue.put((-new_p, base_struct, new_terminals, new_pivot))


def unpack(base_struct):
    regex = '\(([^()]+)\)'
    return tuple(re.findall(regex, base_struct))


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
            words = []
            for line in f:
                fields = line.split('\t')
                try:
                    words.append((fields[0], float(fields[1])))
                except:
                    sys.stderr.write("error inserting {} in the tag dictionary {}\n".format(fields, tag))
            tag_dicts[tag] = words 


def options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--length', type=int, default=0, help='minimum length of the guesses')
    parser.add_argument('-n', '--limit', type=float, default=float('inf'), help='number of guesses')
    parser.add_argument('-m', '--mangle', action='store_true', help='if true, it will mangle every guess')
    return parser.parse_args()
    
    

if __name__ == '__main__':
    opts = options()
    load_grammar(base_structures, tag_dicts)
    guess(opts.length, opts.limit, opts.mangle)
    


    

#:::::::::::::::
# test
#:::::::::::::::

# base_structures[('D1', 'L3', 'S2', 'D1')] = 0.75
# base_structures[('L3', 'D1', 'S1')] = 0.25
#   
# tag_dicts['D1'] = [('4', 0.6), ('5', 0.2), ('6', 0.2)]
# tag_dicts['S1'] = [('!', 0.65), ('%', 0.3), ('#', 0.05)]
# tag_dicts['S2'] = [('$$', 0.7), ('**', 0.3)]
# tag_dicts['L3'] = [('yay', 1)]
#  
# guess(0, 999)    
   
