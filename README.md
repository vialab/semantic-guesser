
#Dependencies

[Oursql](https://launchpad.net/oursql)

[NLTK](http://www.nltk.org/). After installing it, you should also [install the following data packages](http://www.nltk.org/data.html):

  * Brown Corpus
  * Wordnet
  * Word Lists

#Before you start (data dependencies)

Before you begin using the parsing and classification code, a MySQL database must be set up and the required data included.

    mysql -u user -p < root/db/passwords_schema.sql
    mysql -u user -p < root/db/lexicon.sql

The above commands will create the database schema and insert the lexicon. If you would like to have the RockYou passwords on the db, download it [here](https://www.dropbox.com/s/euew2yikglyqpv2/sql.tar.gz) and insert it in the database:

    mysql -u user -p < root/db/rockyou.sql

Note that this will add the RY passwords with the password_set ID 1, so be careful if you already have data in the passwords table.

#Parsing
wordminer.py connects to a database containing the passwords and dictionaries to perform password segmentation. The results are saved into the database.

    cd parsing/
    python wordminer.py

For options,

    python wordminer.py --help

# Classification

coming soon

# Grammar generation

coming soon

#How to compile guessmaker?

g++ -std=c++0x guessmaker.cpp cpp-argparse/OptionParser.cpp -o guessmaker
