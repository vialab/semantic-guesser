from nltk.corpus import wordnet as wn
from collections import defaultdict, Counter
from pattern.en  import pluralize, lexeme
from pos_tagger  import BackoffTagger
from database    import Fragment

class WordNetVocabulary(set):
    def __init__(self):
        self.postagger = BackoffTagger()
        self.update(noun_vocab(self.postagger))
        self.update(verb_vocab(self.postagger))


class FreqDist(dict):
    """ More precisely, a multinomial frequency distribution.
        https://en.wikipedia.org/wiki/Multinomial_distribution
    """

    def __init__(self, samplespace, defaultfreq = 0):
        """
        @params:
        defaultfreq - has the effect of assigning a prior frequency to all classes.
        """
        super(FreqDist, self).__init__(dict().fromkeys(samplespace, defaultfreq))
        self.defaultfreq = defaultfreq
        self.total = defaultfreq * len(samplespace)

    def inc(self, key, value = 1):
        """Increment the value of a class.
        @params:
        key   - string - name of the class
        value - int    - value to add (or subtract, if negative)"""
        if key in self:
            self[key]  += value
            self.total += value
        else:
            self[key]   = self.defaultfreq + value
            self.total += self.defaultfreq + value


    def group_by_freq(self):
        groups = defaultdict(lambda : [])
        for key, value in self.iteritems():
            groups[value].append(key)

        return groups

    def pmf_by_freq(self, estimator):
        """ Probability mass function fx(x) where x is the frequency in the data.
        It informs how much prob. mass is allocated to outcomes that were seen x
        times in the data.
        For example:
            fx(0) = 0.56 means 56% of the prob. space is given to words that were
            never seen in the data.
        Return - dict where key is frequency and value is a float in the range [0,1]
        """
        pmf = defaultdict(lambda : 0)
        for key, freq in self.iteritems():
             pmf[freq] += estimator.probability(freq)
        return pmf

class Estimator(object):
    def probability(self, f):
        """Probability of a class with freq f."""
        pass

class MleEstimator(Estimator):
    def __init__(self, n):
        """
        @params:
            n - int - optional - sample size
        """
        self.n = n

    def probability(self, f):
        return self._probability(f, self.n)

    def _probability(self, f, n):
        return float(f)/n

class LaplaceEstimator(Estimator):
    """
    See https://en.wikipedia.org/wiki/Additive_smoothing
    """
    def __init__(self, n, k, alpha):
        """
        @params:
            f - class frequency
            n - sample size
            k - total number of classes
            alpha - pseudocount (prior count), usually 1 for add-one smoothing
        """
        self.n = n
        self.k = k
        self.alpha = alpha

    def probability(self, f):
        return self._probability(f, self.n, self.k, self.alpha)

    def _probability(self, f, n, k, alpha):
        return float(f + alpha)/(n + k*alpha)


def lemmas(synset):
    lemmas = wn.synset(synset).lemmas()
    lemmas = [l.name() for l in lemmas]
    return lemmas

def noun_vocab(postagger = None):
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

def verb_vocab(postagger = None):
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
            # this step can introduce errors, as getpostag isn't
            # guaranteed to return a verb tag
            forms = [(form, getpostag(form)) for form in forms]

        for form, postag in forms:
            if postag[0] == 'n': # dirty hack to avoid inconsistency introduced by tagger
                continue
            verbs.add((form, postag))
            if "'" in form:  # remove ' (couldn't -> couldnt)
                verbs.add((form.replace("'", ""), postag))

    return verbs

def prior_group_fdist(treecut, pos = 'n', tagtype = 'backoff',
    tagger = None, defaultfreq = 0):
    """
    Initializes the frequency distribution of lemmas, grouped per tag.
    Attributes frequency a default freq. to each lemma.
    This is equivalent to assigning a uniform prior distribution over the lemmas.

    Splits each lemma into all its possible inflections, and assign defaultfreq
    to each, for instance:
        travel     vvi
        travels    vvz
        travelling vvg
        travelled  vvd
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
    from grammar import classify
    lemmas = verb_vocab(tagger) if pos == 'v' else noun_vocab(tagger)

    group_dist = defaultdict(lambda: Counter())

    for lemma, lemma_pos in lemmas:
        tags = classify(Fragment(0, 90, lemma, pos=lemma_pos), tagtype,
                treecut if pos == 'n' else None,
                treecut if pos == 'v' else None)
        for tag in tags:
            group_dist[tag][lemma] = defaultfreq

    return group_dist


def prior_lemma_fdist(pos = 'n', tagger = None, defaultfreq = 0):
    """
    Initializes the frequency distribution of lemmas, attributing frequency defaultfreq
    to each lemma.
    This is equivalent to a uniform prior distribution over the lemmas.

    Splits each lemma into all its possible inflections, and assign defaultfreq
    to each, for instance:
        travel     vvi
        travels    vvz
        travelling vvg
        travelled  vvd

    Returns a dictionary of the form:
        {lemma: frequency}

    Other notes:
    Uses pattern.en pluralizer (accuracy 96%), and the dictionary-based
    inflection engine lexeme.
    lexeme uses a rule-based algorithm (91% accuracy) when given a verb that
    isn't in it's 8,500 words dictionary.
    """
    dist = dict()

    lemmas = verb_vocab(tagger) if pos == 'v' else noun_vocab(tagger)

    for lemma, postag in lemmas:
        dist[lemma] = defaultfreq

    return dist

# dist = init_lemma_dist('v')
