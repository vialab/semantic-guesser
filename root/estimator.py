from nltk.corpus import wordnet as wn
from collections import defaultdict
from pattern.en  import pluralize, lexeme
from pos_tagger  import BackoffTagger
from grammar     import classify
from database    import Fragment

def lemmas(synset):
    lemmas = wn.synset(synset).lemmas()
    lemmas = [l.name() for l in lemmas]
    return lemmas

def noun_universe(postagger = None):
    if not postagger:
        postagger = BackoffTagger()

    getpostag = lambda word : postagger.tag([word])[0][1]
    singular_n_pos = getpostag("house")
    plural_n_pos   = getpostag("houses")

    nouns = set()

    for lemma in wn.all_lemma_names(pos = 'n'):
        if '_' in lemma:
            continue

        plural = pluralize(lemma)
        nouns.add((lemma, singular_n_pos))
        nouns.add((lemma, plural_n_pos))

    return nouns

def verb_universe(postagger = None):
    if not postagger:
        postagger = BackoffTagger()

    getpostag = lambda word : postagger.tag([word])[0][1]

    # Most of the time lexeme() returns 4 or 5 words, inflected as declared below
    # To avoid assumptions on the tagset used, we query the tags using easy examples
    # (verb give). These POS tags are then bound to lexeme's results.
    infinitive_pos = getpostag("give")
    present_pos    = getpostag("gives")
    pres_prog_pos  = getpostag("giving")
    past_pos       = getpostag("gave")
    past_prog_pos  = getpostag("given")

    # three possibilities for return of function tenses
    # depending on how many variations a verb has
    tenses3 = [infinitive_pos, present_pos, pres_prog_pos]
    tenses4 = tenses3 + [past_pos]
    tenses5 = tenses4 + [past_prog_pos]

    verbs = set()

    for lemma in wn.all_lemma_names(pos = 'v'):
        if '_' in lemma:
            continue

        forms = lexeme(lemma) # all possible conjugations of this verb (lemma)

        if len(forms) == 3:
            forms = zip(forms, tenses3)
        elif len(forms) == 4:
            forms = zip(forms, tenses4)
        elif len(forms) == 5:
            forms = zip(forms, tenses5)
        else:
            forms = [(form, getpostag(form)) for form in forms]

        for form, postag in forms:
            verbs.add((form, postag))
            if "'" in form:  # remove ' (couldn't -> couldnt)
                verbs.add((form.replace("'", ""), postag))

    return verbs

def prior_group_fdist(pos = 'n', tagtype = 'backoff', tagger = None):
    """
    Initializes the frequency distribution of lemmas, grouped per tag.
    Attributes frequency 1 to each lemma, according to Laplace's Law (Rule of Succession).
    This is equivalent to a uniform prior distribution over the lemmas.
    See https://en.wikipedia.org/wiki/Rule_of_succession

    Splits each lemma into all its possible inflections, and assign 1 to each,
    for instance:
        travel     vvi 1
        travels    vvz 1
        travelling vvg 1
        travelled  vvd 1
    Then classifies each lemma according to its tagtype.

    Returns a dictionary of the form:
        {tag: {lemma: frequency}}
    where tag is the semantic category.

    Other notes:
    Uses pattern.en pluralizer (accuracy 96%), and the dictionary-based
    inflection engine lexeme.
    lexeme uses a rule-based algorithm (91% accuracy) when given a verb that
    isn't in it's 8,500 words dictionary.
    """
    lemmas = verb_universe(tagger) if pos == 'v' else noun_universe(tagger)

    group_dist = defaultdict(lambda: dict())

    for lemma, lemma_pos in lemmas:
        tag = classify(Fragment(0, 90, lemma, pos=lemma_pos), tagtype)
        group_dist[tag][lemma] = 1

    return group_dist


def prior_lemma_fdist(pos = 'n', tagger = None):
    """
    Initializes the frequency distribution of lemmas, attributing frequency 1
    to each lemma, according to Laplace's Law (Rule of Succession).
    This is equivalent to a uniform prior distribution over the lemmas.
    See https://en.wikipedia.org/wiki/Rule_of_succession

    Splits each lemma into all its possible inflections, and assign 1 to each,
    for instance:
        travel     vvi 1
        travels    vvz 1
        travelling vvg 1
        travelled  vvd 1

    Returns a dictionary of the form:
        {lemma: frequency}

    Other notes:
    Uses pattern.en pluralizer (accuracy 96%), and the dictionary-based
    inflection engine lexeme.
    lexeme uses a rule-based algorithm (91% accuracy) when given a verb that
    isn't in it's 8,500 words dictionary.
    """
    dist = dict()

    lemmas = verb_universe(tagger) if pos == 'v' else noun_universe(tagger)

    for lemma, postag in lemmas:
        dist[lemma] = 1

    return dist

# dist = init_lemma_dist('v')
