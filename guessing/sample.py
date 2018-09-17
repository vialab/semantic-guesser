"""
Outputs a password sample of a given size from a grammar.
"""
import argparse

from learning import model

def options():
    parser = argparse.ArgumentParser()
    parser.add_argument('N', type=int, default=1000)
    parser.add_argument('grammar_dir')
    return parser.parse_args()

if __name__ == '__main__':
    opts = options()
    grammar = model.Grammar.from_files(opts.grammar_dir)
    for password, base_struct, p in grammar.sample(opts.N):
        print("{}\t{}".format(password, p))
