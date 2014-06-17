
#Parsing
wordminer.py connects to a database containing the passwords and dictionaries to perform password segmentation. The results are saved into the database.

    cd parsing/
    python wordminer.py

For options,

    python wordminer.py --help




#How to compile guessmaker?

g++ -std=c++0x guessmaker.cpp cpp-argparse/OptionParser.cpp -o guessmaker
