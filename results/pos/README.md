This folder contains the outputs of tests made to verify the quality of tagging (see pos_tagger.py).

The format is:
pos-sample-{size}-{commit}.csv (tab-separated)
where:
+ size   - size of the sample
+ commit - refers to the git version of pos_tagger.py that was used to generate the pos-tags.

Random IDs
==========
Each sample contains a list of random passwords (and its fragments). The IDs are generated once and kept in a random-ids file.
The name format is random-ids-{size}-{extent}.txt

+ size   - number of ids generated
+ extent - \[0, extent\] is the range which the samples are drawn from.

Example: random-ids-1000-5000 contains 1000 numbers out of the range \[0,5000\]


