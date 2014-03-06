#!/usr/bin/env python

import re

def rank():
    regex = '\(([^()]+)\)'
    nonterminal_dist = dict()
    
    with open('grammar/rules.txt') as f:
        for i, line in enumerate(f):
            fields = line.split()
            base_struct = fields[0]
            prob = float(fields[1])
            nonterminals = re.findall(regex, base_struct)
            for n in nonterminals:
                try:
                    nonterminal_dist[n] += prob
                except:
                    nonterminal_dist[n] = prob
            
    sorted_entries = sorted(nonterminal_dist.items(), cmp = lambda x,y: cmp(x[1], y[1]), reverse=True)
    
    return sorted_entries
    
    
if __name__ == "__main__":
    for a, b in rank():
        print "{}\t{:.5}".format(a,b)
