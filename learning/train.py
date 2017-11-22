import re
import logging
import itertools
import multiprocessing

import wordsegment as ws

from argparse import ArgumentParser
from collections import Counter
from learning.pos import BackoffTagger
from learning.tagset_conversion import TagsetConverter
from learning.model import TreeCutModel, Grammar
from nltk.corpus import wordnet as wn
from functools import reduce
from pattern.en import pluralize, lexeme
from multiprocessing import Process, Manager


# load global resources
log = logging.getLogger(__name__)
tag_converter = TagsetConverter()
ws.load()

def tally(path):
    """Return a Counter for passwords."""
    pwditer = (line.rstrip('\n') for line in open(path, encoding='latin-1')
        if not re.fullmatch('\s+', line))
    return Counter(pwditer)


def getchunks(password):
    # split into character/digit/symbols chunks
    temp = re.findall('(\W+|[a-zA-Z]+|[0-9]+)', password)

    # split character chunks into word chunks
    chunks = []
    for chunk in temp:
        if chunk[0].isalpha() and len(chunk) > 1:
            words = ws.segment(chunk)
            chunks.extend(words)
        else:
            chunks.append(chunk)

    if len(chunks) == 0:
        log.warning("Unable to chunk password: {}".format(password))

    return chunks


def synset(word, pos):
    """
    Given a POS-tagged word, determine its synset by converting the CLAWS tag
    to a WordNet tag and querying the associated synset from NLTK's WordNet.

    If more than one synset is retrieved, return the first, which is, presumably,
    the most frequent. More on this at:
    http://wordnet.princeton.edu/wordnet/man/cntlist.5WN.html

    If the fragment has no POS tag or no synset is found in WordNet for the POS
    tag, None is returned.

    - pos: a part-of-speech tag from the CLAWS7 tagset

    """

    if pos is None:
        return None

    wn_pos = tag_converter.clawsToWordNet(pos)

    if wn_pos is None:
        return None

    synsets = wn.synsets(word, wn_pos)

    return synsets[0] if len(synsets) > 0 else None


def pos_tag(chunks, tagger):
    """ Assign POS tags to alphabetic chunks, except when they are short (less
    than 3 chars) AND have no adjacent chunks of the same type (e.g. "1ab!!").
    Such a chunks are likely to be short strings in a random password.

    Example:
        >>> pos_tag(['i', 'love', 'you', '2'])
        [('i', 'ppis1'), ('love', 'vv0'), ('you', 'ppy'), ('2', None)]

        >>> train.pos_tag(['123','ab','!!'], tagger)
        [('123', None), ('ab', None), ('!!', None)]

    """
    if len(chunks) == 1:
        chunk = chunks[0]
        if chunk.isalpha():
            return tagger.tag(chunks)
        else:
            return [(chunk, None)]

    # try to tag only consecutive sequences of alphabetic chunks
    # (which are likely to be non-random)
    # assign None to isolated alpha chunks and all other types of chunks

    tags = []
    alpha_mask = [c[0].isalpha() for c in chunks]

    sequence = []  # sequence cache
    for i, isalpha in enumerate(alpha_mask):
        if not isalpha:

            if len(sequence) > 0:
                tags.extend(tagger.tag(sequence))
                sequence = []

            tags.append((chunks[i], None))

        # if this alpha chunk has an adjacent alpha chunk, it should be tagged
        elif len(alpha_mask) > i+1 and alpha_mask[i+1] or \
             i > 0 and alpha_mask[i-1]:
            sequence.append(chunks[i])
        elif len(chunks[i]) > 2:
            sequence.append(chunks[i])
        else:  # it's alpha but short and isolated, then None
            tags.append((chunks[i], None))

    if len(sequence) > 0:
        tags.extend(tagger.tag(sequence))

    return tags


def lemmas(synset):
    lemmas = wn.synset(synset).lemmas()
    lemmas = [l.name() for l in lemmas]
    return lemmas


def noun_vocab(tcm, postagger=None):
    """
    Return all nouns found in wordnet in both singular and plurar forms,
    along with POS tag and synset (as given by a TreeCutModel instance).
    """
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
        for syn in wn.synsets(lemma, 'n'):
            for classy in tcm.predict(syn):
                nouns.add((lemma, singular_n_pos, classy))
                nouns.add((plural, plural_n_pos, classy))

    return nouns


def verb_vocab(tcm, postagger = None):
    """
    Return all verbs found in wordnet in various inflected forms.
    """
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

        classes = [classy for syn in wn.synsets(lemma, 'v') for classy in tcm.predict(syn)]

        for classy in classes:
            for form, postag in forms:
                if postag[0] == 'n': # dirty hack to avoid inconsistency introduced by tagger
                    continue
                verbs.add((form, postag, classy))
                if "'" in form:  # remove ' (couldn't -> couldnt)
                    verbs.add((form.replace("'", ""), postag, classy))

    return verbs


def product(list_a, list_b):
    for a in list_a:
        for b in list_b:
            try:
                yield a + [b]
            except TypeError:
                yield [a, b]


def tally_chunk_tag(path, num_workers):
    def do_work(in_queue, out_list):
        postagger = BackoffTagger.from_pickle()
        i = 0
        while True:
            try:
                password, count = in_queue.get()
            except:
                return

            chunks = getchunks(password)
            try:
                postagged_chunks = pos_tag(chunks, postagger)
            except:
                log.error("Error: {}".format(chunks))
                raise

            out_list.append((postagged_chunks, count))
            i += 1

            if i % 100000 == 0:
                process_id = multiprocessing.current_process()._identity[0]
                log.info("Process {} has worked on {} passwords..."
                    .format(process_id, i))

    manager = Manager()

    results = manager.list()
    work = manager.Queue(num_workers)

    # start for workers
    pool = []
    for i in range(num_workers):
        p = Process(target=do_work, args=(work, results))
        p.start()
        pool.append(p)

    passwords = [] # list of list of tuples (one tuple per chunk)
    counts = []

    for password, count in tally(path).items():
        work.put((password, count))

    for p in pool:
        p.join()

    return results


def train_grammar(path, outfolder, estimator='laplace', specificity=None,
    num_workers=2):
    """Train a semantic password model"""

    wn.ensure_loaded()
    # Chunking and Part-of-Speech tagging
    log.info("Counting, chunking and POS tagging... ")

    passwords = tally_chunk_tag(path, num_workers)

    def syn_generator(passwords):
        # debug_n_total = 0
        for chunks, count in passwords:
            for string, pos in chunks:
                syn = synset(string, pos)
                if syn:
                    yield (syn, count)

    # Train tree cut models
    log.info("Training tree cut models... ")
    tcm_n = TreeCutModel('n', estimator=estimator, specificity=specificity)
    tcm_n.fit(syn_generator(passwords))

    tcm_v = TreeCutModel('v', estimator=estimator)
    tcm_v.fit(syn_generator(passwords))

    log.info("Training grammar...")

    grammar = Grammar(estimator=estimator)

    # feed grammar with the 'prior' vocabulary
    if estimator == 'laplace':
        grammar.add_vocabulary(noun_vocab(tcm_n, postagger))
        grammar.add_vocabulary(verb_vocab(tcm_v, postagger))

    for chunks, count in passwords:
        X = []  # list of list of tuples. X[0] holds one tuple for
                # every different synset of chunks[0]

        for string, pos in chunks:
            syn = synset(string, pos)
            synlist = [None] # in case synset is None

            if syn is not None:  # abstract (generalize) synset
                if syn.pos() == 'n':
                    synlist = tcm_n.predict(syn)
                elif syn.pos() == 'v':
                    synlist = tcm_v.predict(syn)

            chunkset = [] # all semantic variations of this chunk
            for syn in set(synlist):
                chunkset.append((string, pos, syn))
            X.append(chunkset)

        # navigate the cross-product of the chunksets
        if len(X) > 1:
            n_variations = reduce(lambda x,y: x * len(y), X, 1)
            count_ = count/n_variations
            for x in reduce(product, X):
                grammar.fit_incremental(x, count_)
        elif len(X) == 1:
            for x in X[0]:
                grammar.fit_incremental([x], count)
        else:
            log.warning("Unable to feed chunks to grammar: {}".format(chunks))

    grammar.write_to_disk(outfolder)

    return grammar



def options():
    parser = ArgumentParser()
    parser.add_argument('passwords', help='a password list')
    parser.add_argument('output_folder', help='a folder to store the grammar model')
    parser.add_argument('--estimator', default='mle', choices=['mle', 'laplace'])
    parser.add_argument('-a', '--abstraction', type=int, default=None,
        help='Detail level of the grammar. An integer > 0 proportional to \
        the desired specificity.')
    parser.add_argument('-v', action = 'append_const', const = 1, help="""
        verbose level (e.g., -vvv) """)
    parser.add_argument('--tags', default='pos_semantic',
        choices=['pos_semantic', 'pos', 'backoff', 'word'])
    parser.add_argument('-w', '--num_workers', type=int, default=2,
        help="number of cores available for parallel work")
    return parser.parse_args()


if __name__ == '__main__':
    opts = options()
    filepath = opts.passwords

    verbose_levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    verbose_level = sum(opts.v) if opts.v else 0
    logging.basicConfig(level=verbose_levels[verbose_level])
    log.setLevel(verbose_levels[verbose_level])


    train_grammar(filepath, 
                  opts.output_folder,
                  opts.estimator,
                  opts.abstraction,
                  opts.num_workers)
