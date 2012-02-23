
Contains the partial results of the tagging process.

**treebank-synth-data.txt** results from tagging the synthetic data using a backoff chain (TrigramTagger->BigramTagger->UnigramTagger->DefaultTagger("NN")) trained with the treebank corpus

**brown-synth-data.txt** same as above but using the Brown corpus

**brown-synth-data-kk.txt** same as above but using DefaultTagger("KK") to highlight non-tagged words

**brown-wordnet.csv** backoff chain (TrigramTagger->BigramTagger->UnigramTagger->WordNetTagger->DefaultTagger("NN")) trained with the brown corpus

**treebank-wordnet.csv** same as above but using treebank corpus

**brown-wordnet-names** results from tagging the synthetic data using a backoff chain (TrigramTagger->BigramTagger->UnigramTagger->NamesTagger->WordNetTagger->DefaultTagger("NN")) trained with the brown corpus

**treebank-wordnet-names** sames as above but using treebank