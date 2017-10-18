To produce the .sql files:

schema.sql

    mysqldump -u root -p --no-data passwords > schema.sql

lexicon.sql

    mysqldump -u user -p --no-create-info passwords dictionary bigrams cities150000 COCA_wordlist dictionary dictionary_set trigrams bnc  > lexicon.sql
