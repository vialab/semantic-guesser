# Semantic Password Guesser

Tools for training probabilistic context-free grammars on password lists. The
models encode syntactic and semantic linguistic patterns and can be used to
generate guesses.

## Basic Usage

To train a grammar with a password list:

```
cd semantic_guesser  
python -m learning.train password_list.txt ~/grammars/test_grammar
```

A password list has one password per line:

```
$ head password_list.txt
@fl!pm0de@
pass
steveol
chotzi
lb2512
scotch
passwerd
flipmode
flipmode
alden2
```

## Options

```
usage: train.py [-h] [--estimator {mle,laplace}] [-a ABSTRACTION] [-v]
                [--tags {pos_semantic,pos,backoff,word}] [-w NUM_WORKERS]
                [passwords] output_folder

positional arguments:
  passwords             a password list
  output_folder         a folder to store the grammar model

optional arguments:
  -h, --help            show this help message and exit
  --estimator {mle,laplace}
  -a ABSTRACTION, --abstraction ABSTRACTION
                        Detail level of the grammar. An integer > 0
                        proportional to the desired specificity.
  -v                    verbose level (e.g., -vvv)
  --tags {pos_semantic,pos,backoff,word}
  -w NUM_WORKERS, --num_workers NUM_WORKERS
                        number of cores available for parallel work

```


## Generating guesses

The guess generator is a C++ program, you need to compile it first.

```
cd guessing
make
```

Then run it with a trained grammar model.

```
guessmaker -g /path/to/my/grammar
```

guessmaker implements the algorithms described in [Matt Weir's dissertation][1]: next and deadbeat. Deadbeat is the default.

## Installation

venv is preferred:

```
cd semantic_guesser
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

Then download NLTK data:

```
python -m nltk.downloader wordnet wordnet_ic
```

[1]: http://purl.flvc.org/fsu/fd/FSU_migr_etd-1213 "Weir, C. M. (2010). Using Probabilistic Techniques to Aid in Password Cracking Attacks."