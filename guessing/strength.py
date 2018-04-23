#!/usr/bin/env python

"""
Estimate strength as described in Dell'Amico and Filippone (2015)*.

* Dell'Amico, Matteo, and Maurizio Filippone.
  "Monte Carlo strength evaluation: Fast and reliable password checking."
  Proceedings of the 22nd ACM SIGSAC Conference on Computer and Communications Security.
  ACM, 2015.
"""

import argparse
import pickle
import sys

import pandas as pd

from learning       import model
from guessing.score import score
from pathlib        import Path


def options():
    desc = """Estimate strength of each password in a list as described
    in Dell'Amico and Filippone (2015). Requires a password sample with
    pre-computed probabilities (see scorer.py).
    """

    epilog = """Example:

    scorer.py /path/to/mygrammar sample.txt > scored_sample.txt

    strength.py scored_sample.txt mygrammar passwords.txt"""

    # usage = "recognizer.py -p -g mygrammar sample.txt | strength.py mygrammar passwords.txt"

    parser = argparse.ArgumentParser(description=desc, epilog=epilog)
    parser.add_argument('sample', type=argparse.FileType('r'),
        help='a large and diverse list of passwords and their probabilities')
    parser.add_argument('--grammar', help="grammar path for computing "
    "password probabilities.")
    parser.add_argument('passwords', nargs='?', type=argparse.FileType('r'),
        default=sys.stdin,
        help='a list of passwords whose strength one wants to know. '
        'Strength is defined as the number of guesses needed to crack the '
        'password with the grammar used to estimate the sample\'s probabilities. '
        'File is a space-delimited file with fields password, base structure, '
        'and probability. If --grammar is set, then file is a list of '
        'passwords.')
    parser.add_argument('-d','--dedupe', action="store_true",
        help="drop duplicates in the sample. Default is False.")

    return parser.parse_args()


def read_sample(f):
    return pd.read_csv(f, sep='\t', names=['password', 'p'])

def password_score_iterator(password_file, grammar_path):
    if grammar_path is None:
        for line in password_file:
            if line == '': break
            password, base_struct, p = line.rstrip().rsplit(maxsplit=2)
            yield (password, base_struct, float(p))
    else:
        grammar_dir = Path(grammar_path)

        tc_nouns = pickle.load(open(grammar_dir / 'noun_treecut.pickle', 'rb'))
        tc_verbs = pickle.load(open(grammar_dir / 'verb_treecut.pickle', 'rb'))
        grammar  = model.Grammar.from_files(grammar_path)

        return score((line.lower().rstrip() for line in password_file),
            grammar, tc_nouns, tc_verbs)

def main():
    opts = options()

    sample = read_sample(opts.sample)  # a pandas frame
    # drop duplicates
    if opts.dedupe:
        sample = sample.drop_duplicates("password")

    # load sample, sort it and compute cumulative probability
    sample = sample.sort_values('p', ascending=False)

    # compute the estimated number of passwords output before this one in a
    # process where the grammar's language is output in highest probability order
    # see Session 3.2 in Dell'Amico and Filippone (2015)
    n = len(sample)
    sample['strength'] = (1/sample['p']).cumsum() * 1/n

    # now sort it ascending, cause that's the only way binary search
    # will work in pandas (asc p is desc strength)
    sample = sample.sort_values('strength', ascending=False)

    # restore index
    sample = sample.reset_index().drop("index", axis=1)

    for password, struct, p in password_score_iterator(opts.passwords, opts.grammar):
        if p == 0:  # password isn't guessed by this grammar
            continue

        # find bisector (index where elements should be inserted to maintain order)
        # invert Dellamico's 3.2 instruction since our array is in ascending order
        bisector = sample['p'].searchsorted(p, side='left')[0]  # note left

        bisector = min(max(bisector+1, 0), n-1) # index of the lowest prob. higher than p

        strength = sample['strength'][bisector]

        sys.stdout.write("{}\t{:.2f}\n".format(password, strength))


if __name__ == '__main__':
    main()
