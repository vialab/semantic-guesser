from nltk.tag import brill
from nltk.probability import FreqDist, ConditionalFreqDist


def backoff_tagger(train_sents, tagger_classes, backoff=None):
    for cls in tagger_classes:
        backoff = cls(train_sents, backoff=backoff)
    
    return backoff


def word_tag_model(words, tagged_words, limit=200):
    fd = FreqDist(words)
    most_freq = fd.keys()[:limit]
    cfd = ConditionalFreqDist(tagged_words)
    return dict((word, cfd[word].max()) for word in most_freq)

patterns = [
    (r'^\d+$', 'CD'),
    (r'.*ing$', 'VBG'),  # gerunds, i.e. wondering
    (r'.*ment$', 'NN'),  # i.e. wonderment
    (r'.*ful$', 'JJ')    # i.e. wonderful
]


def train_brill_tagger(initial_tagger, train_sents, **kwargs):
    sym_bounds = [(1,1), (2,2), (1,2), (1,3)]
    asym_bounds = [(-1,-1), (1,1)]
    
    templates = [
        brill.SymmetricProximateTokensTemplate(brill.ProximateTagsRule, *sym_bounds),
        brill.SymmetricProximateTokensTemplate(brill.ProximateWordsRule, *sym_bounds),
        brill.ProximateTokensTemplate(brill.ProximateTagsRule, *asym_bounds),
        brill.ProximateTokensTemplate(brill.ProximateWordsRule, *asym_bounds)
    ]
    
    trainer = brill.FastBrillTaggerTrainer(initial_tagger, templates, deterministic=True)
    return trainer.train(train_sents, **kwargs)

def unigram_feature_detector(tokens, index, history):
    return {'word': tokens[index]}

# test
# t = StatyBackoffTagger()
# t.tag(['she', 'said'])
# t.tag(['he', 'ate'])
# t.tag(['the', 'problem'])
  
    