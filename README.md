#Semantic Guesser

##Todo

1) Modify remote_claws_tagger.py to create the pickles subdirectory if it is not already created

2) Modify the pos_tagger.py script to call remote_claws_tagger.py if claws tagger has not been run (the pickles folder is empty / non-existant)


##Dependencies

[Oursql](https://launchpad.net/oursql)

[NLTK](http://www.nltk.org/). After installing it, you should also [install the following data packages](http://www.nltk.org/data.html):

  * Brown Corpus
  * Wordnet
  * Word Lists

[BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup/)
     Install with "pip install beautifulsoup4"

[Mechanize](https://pypi.python.org/pypi/mechanize/0.2.5)
     Install with "pip install mechanize"

##Usage

###Before you start (data dependencies)

Before you begin using the parsing and classification code, a MySQL database must be set up and the required data included.

    mysql -u user -p < root/db/passwords_schema.sql
    mysql -u user -p < root/db/lexicon.sql

The above commands will create the database schema and insert the lexicon. If you would like to have the RockYou passwords on the db, download it [here](https://www.dropbox.com/s/bnxmxdvrkkz5lra/rockyou_ordered.sql.tar.gz) and insert it in the database:

    mysql -u user -p < root/db/rockyou.sql

Note that this will add the RY passwords with the password_set ID 1, so be careful if you already have data in the passwords table.

We need to tag the Brown Corpus with claws tagger. Claws Tagger has a website that allows you to submit one word and it returns the tag of that word. However, you cannot submit bulk words to that website, so this script will query the website, wait for a response and then send another query. Before running the script, the pickles directory must be created in the root directory:

    mkdir pickles

Then the script must be run (ensure all data dependencies listed above are installed first and the pickles directory has been created):

    python remote_claws_tagger.py

###Authentication

Make sure you modify the file root/db_credentials.conf with your MYSQL credentials.

###Parsing
wordminer.py connects to a database containing the passwords and dictionaries to perform password segmentation. The results are saved into the database.

**Important Note**
For performance reasons, make sure the passwords table is ordered by pass_text before running wordminer.py. Wordminer works in chunks of 100'000 words, and used to take 1+ days to run. The passwords table contains ~32'000'000 records, and each time 100'000 were fetched, the entire table was ordered by pass_text. As a result, preordering the table will speed up queries tremendously (only takes ~7 hours now on a high powered computer). If the RockYou passwords were loaded from the file provided above, they are already sorted.  

For example, to parse a group of passwords whose ID in the database is 1:

    cd parsing/
    python wordminer.py 1

For more options:

    python wordminer.py --help

### Classification

Before generating the grammar. You need to run the scripts for POS tagging and semantic classification.
Assuming you're targeting the group of passwords 1:

    cd root/
    python pos_tagger.py 1

### Grammar generation

    cd root/
    python grammar.py 1

The grammar files will be saved in a subdirectory of grammar/ identified by the ID of the corresponding password list.

### Generating guesses

Compile guessmaker with:

    cd root/
    make all
    ./guessmaker -s 1
     
For more options:

    ./guessmaker --help

## Publications

Veras, Rafael, Christopher Collins, and Julie Thorpe. "On the semantic patterns of passwords and their security impact." Network and Distributed System Security Symposium (NDSS’14). 2014. [Link] (http://thorpe.hrl.uoit.ca/documents/On_the_Semantic_Patterns_of_Passwords_and_their_Security_Impact_NDSS2014.pdf)

## Credits

Rafael Veras, Julie Thorpe and Christopher Collins
[Vialab][vialab] - [University of Ontario Institute of Technology][uoit]


[vialab]: http://vialab.science.uoit.ca
[uoit]:   http://uoit.ca

