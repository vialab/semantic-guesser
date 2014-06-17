tar -cvf semantic_guessmaker.tar root/parsing/ root/grammar/ root/cut/ root/pickles/ root/tree/ root/pos_tagger.py root/database.py root/grammar.py root/semantics.py root/util.py root/query.py root/remote_claws_tagger.py root/taggers.py root/timer.py root/__init__.py  root/*.conf db/  README.md root/cpp-argparse/ root/*.cpp root/Makefile root/tagset_conversion.py root/sentiwordnet.py files/coca_500k.csv --exclude='*.pickle' --exclude='.*' --exclude='root/grammar/*' --exclude='*.pyc'

# add files that are an exception to an exclude rule

tar -rvf semantic_guessmaker.tar root/pickles/brown_clawstags.pickle

# compress

gzip -9 semantic_guessmaker.tar
