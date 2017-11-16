# Semantic Guesser

Train probabilistic context-free grammars that encode
linguistic password patterns.



## Usage

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


## Installation

virtualenv is preferred:

```
cd semantic_guesser
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

Then download NLTK data:

```
python -m nltk.downloader wordnet
```
