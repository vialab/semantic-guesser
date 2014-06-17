
#Dependencies

[Oursql](https://launchpad.net/oursql)

[NLTK](http://www.nltk.org/). After installing it, you should also [install the following data packages](http://www.nltk.org/data.html):

  * Brown Corpus
  * Wordnet
  * Word Lists

#Usage

##Before you start (data dependencies)

Before you begin using the parsing and classification code, a MySQL database must be set up and the required data included.

    mysql -u user -p < root/db/passwords_schema.sql
    mysql -u user -p < root/db/lexicon.sql

The above commands will create the database schema and insert the lexicon. If you would like to have the RockYou passwords on the db, download it [here](https://www.dropbox.com/s/euew2yikglyqpv2/sql.tar.gz) and insert it in the database:

    mysql -u user -p < root/db/rockyou.sql

Note that this will add the RY passwords with the password_set ID 1, so be careful if you already have data in the passwords table.

##Authentication

Make sure you modify the file root/db_credentials.conf with your credentials.

##Parsing
wordminer.py connects to a database containing the passwords and dictionaries to perform password segmentation. The results are saved into the database.
For example, to parse a group of passwords whose ID in the database is 1:

    cd parsing/
    python wordminer.py 1

For more options:

    python wordminer.py --help

## Classification

Before generating the grammar. You need to run the scripts for POS tagging and semantic classification.
Assuming you're targeting the group of passwords 1:

    cd root/
    python pos_tagger.py 1

## Grammar generation

    cd root/
    python grammar.py 1

The grammar files will be saved in a subdirectory of grammar/ identified by the ID of the corresponding password list.

## Generating guesses

Compile guessmaker with:

    cd root/
    make all
    ./guessmaker -s 1
     
For more options:

    ./guessmaker --help
