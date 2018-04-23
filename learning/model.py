from learning.tree.wordnet      import IndexedWordNetTree
from learning.tree.default_tree import TreeCut
from learning.tree.cut          import wagner, li_abe
from collections                import defaultdict, Counter
from multiprocessing            import Process, Manager, Pool, Queue

from misc import util

import shutil
import re
import os
import sys
import logging
import numpy as np
import pickle
import math
import multiprocessing


log = logging.getLogger(__name__)

class TreeCutModel():
    def __init__(self, pos='n', estimator='mle', specificity=None):
        """
        Args:
            pos: the part-of-speech of this tree: 'v' (verb) or 'n' (noun)
        """
        self.pos  = pos
        self.tree = None
        self.treecut = None
        self.specificity = specificity
        self.estimator = estimator

    def fit(self, X):
        """ Fit a tree cut model.

        Args:
          X: An iterable for tuples of the form (synset, count).

        Returns:
          self
        """
        pos  = self.pos
        specificity = self.specificity

        self.tree = tree = IndexedWordNetTree(pos)
        for synset, count in X:
            if synset.pos() == pos:
                self._increment_synset_count(synset, count)
        tree.updateCounts()

        N = tree.root.value
        if self.estimator == 'mle':
            estimator = MleEstimator(N)
        else:
            k = tree.root.leaf_count
            estimator = LaplaceEstimator(N, k, 1)

        if specificity:
            cut = wagner.findcut(tree, specificity, estimator)
        else:
            cut = li_abe.findcut(tree, estimator)

        self.treecut = TreeCut(tree, cut)


    def fit_tree(self, tree):
        pos  = self.pos
        specificity = self.specificity
        self.tree = tree

        N = tree.root.value
        if self.estimator == 'mle':
            estimator = MleEstimator(N)
        else:
            k = tree.root.leaf_count
            estimator = LaplaceEstimator(N, k, 1)

        if specificity:
            cut = wagner.findcut(tree, specificity, estimator)
        else:
            cut = li_abe.findcut(tree, estimator)

        self.treecut = TreeCut(tree, cut)


    def predict(self, X):
        """
        For each synset, return a list of classes that represent it in the tree
        cut model. The *list* is due to a synset potentially being present in
        multiple subtrees (multiple inheritance).

        Args:
            X - an iterable or a wordnet.Synset

        Return:
            if X is an iterable, return a list of lists of node keys (str)
            if X is a Synset, return a list of node keys (str)
        """

        try:
            iter(X)
        except:
            return list(set([node.key for node in self.treecut.abstract_synset(X)]))

        labels = []

        for synset in X:
            keys = set([node.key for node in self.treecut.abstract_synset(synset)])
            labels.append(list(keys))

        return labels

    def _increment_synset_count(self, synset, count=1):
        """ Given  a  WordNetTree, increases the  count  (frequency)
        of a  synset (does not propagate to its ancestors). This
        method is more efficient than WordNetTree.increment_synset()
        as it uses WordNetTree.hashtable() to avoid searching.

        It's different  from increment_node() in that it  increments
        the counts of ALL nodes  matching a key. In fact, it divides
        the count by the number of nodes matching the key.
        increment_node() resolves  ambiguity using the ancestor path
        received as argument.
        """
        index = self.tree.index
        paths = synset.hypernym_paths()

        key = synset.name()

        if key in index and len(index[key]) == len(paths):
            count = float(count) / len(paths)
            nodes = index[key]
            for n in nodes:
                if n.has_children():
                    n = n.find('s.' + n.key)
                n.increment_value(count, cumulative=False)
        else:
            # this block used to exist because WordNetTree.load used a method
            # (depth search) that missed a few synsets (it's a nltk.wordnet bug)
            # the line below would insert the synset in the tree
            # I kept this line just in case there is problem with WordNetTree
            # coverage
            print(synset, count)
            self.tree.increment_synset(synset, count, cumulative=False)

    def __getstate__(self):
        return {
            'pos': self.pos,
            'treecut': self.treecut,
            'specificity': self.specificity,
            'estimator': self.estimator
        }

    def __setstate__(self, d):
        self.pos = d['pos']
        self.treecut = d['treecut']
        self.specificity = d['specificity']
        self.estimator = d['estimator']
        self.tree = self.treecut.tree

    def pickle(self, outfolder):
        name = 'noun_treecut.pickle' if self.pos == 'n' else 'verb_treecut.pickle'
        sys.setrecursionlimit(sys.getrecursionlimit()*2)
        filepath = os.path.join(outfolder, name)
        pickle.dump(self, open(filepath, 'wb'))

    @classmethod
    def from_pickle(cls, f):
        return pickle.load(open(f, 'rb'))


class Estimator(object):
    def probability(self, node):
        """Probability of a node with freq f."""
        pass


class MleEstimator(Estimator):
    def __init__(self, n):
        """
        @params:
            n - int - sample size
        """
        self.n = n

    def probability(self, x):
        if type(x) == int or type(x) == float:
            return self._probability(x, self.n)
        else:
            return self.node_probability(x)

    def node_probability(self, node):
        return self._probability(node.value, self.n)

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

    def probability(self, x):
        if type(x) == int or type(x) == float:
            return self._probability(x, 1, self.n, self.k, self.alpha)
        else:
            return self.node_probability(x)

    def node_probability(self, node):
        f = node.value
        c = node.leaf_count
        return self._probability(f, c, self.n, self.k, self.alpha)

    def _probability(self, f, c, n, k, alpha, *args):
        return float(f + c*alpha)/(n + k*alpha)


def _datafile(name):
    return open(os.path.join(os.path.dirname(__file__), '../data/'+name),
        encoding='utf-8')


class GrammarTagger(object):

    MaleNames   = set([name.strip() for name in _datafile('mnames.txt')])
    FemaleNames = set([name.strip() for name in _datafile('fnames.txt')])
    Countries   = set([country.strip() for country in _datafile('countries.txt')])
    # Months      = set([month.strip() for month in _datafile('months.txt')])
    Surnames    = set([surname.strip() for surname in _datafile('surnames.txt')])
    Cities      = set([city.strip() for city in _datafile('cities.txt')])

    def _get_tag(self, string, pos, synset, tagtype):
        if tagtype == 'pos':
            tag = self._tag_pos(string, pos)
        elif tagtype == 'backoff':
            tag = self._tag_semantic_backoff_pos(string, pos, synset)
        elif tagtype == 'pos_semantic':
            tag = self._tag_pos_semantic(string, pos, synset)

        return tag

    def _tag_pos(self, string, pos, *args):
        """ Classifies  the  chunk into number, word, character  sequence or
        special  character sequence.  Includes a POS tag if possible. Does not
        include a semantic symbol/tag.
        If chunk is a word, the tag consists of its POS tag. For numbers and
        character sequences, a tag of the form categoryN is  retrieved where N
        is  the length  of the segment.  Words with unknown pos  are tagged as
        'unk'.
        Examples:
            love    -> vb
            123     -> number3
            audh    -> char4
            kripton -> unk
            !!!     -> special3
        Returns:
            str -- tag
        """
        if not pos:
            return self.tag_nonword(string)
        else:
            return pos


    def _tag_semantic_backoff_pos(self, string, pos, synset):
        """  Returns a  list of  tags  containing  EITHER  semantic  OR syntactic
        (part-of-speech) symbols. If the chunk is a proper noun, returns either
        month, fname, mname, surname, city or country, as suitable.
        For other words, returns  semantic tags if the  word is found in Wordnet;
        otherwise, falls  back to a POS tag. Aside from  these classes, there is
        also numberN, charN, and specialN, for numbers,  character sequences  and
        sequences of special characters, respectively, where N denotes the length
        of the chunk.
        Examples:
            loved -> s.love.v.01
            paris -> city
            jonas -> mname
            cindy -> fname
            aaaaa -> char5
        Returns:
            list of str -- tags
        """
        # dictionary-based semantic tags (name, country, etc.) take precedence
        # over wordnet
        if pos in ['np', 'np1', 'np2']:
            tag = self.propername_tag(string)
            if not tag:
                tag = synset if synset else self._tag_pos(string, pos)
            return tag

        if synset: return synset

        return self._tag_pos(string, pos)

    def _tag_pos_semantic(self, string, pos, synset):
        """ Fully classify the segment. Returns a list of tags possibly  containing
        semantic AND syntactic (part-of-speech) symbols. If the segment is a proper
        noun,  returns either month, fname,  mname,  surname,  city  or country, as
        suitable.
        For other  words, returns  tags of  the  form  pos_synset, where pos is  a
        part-of-speech tag and  synset is the corresponding  WordNet synset.  If no
        synset exists,  the symbol 'unk' is used. Aside from these classes, there
        is also numberN, charN, and specialN, for numbers, character sequences  and
        sequences of  special characters,  respectively, where N denotes the length
        of the segment.
        Examples:
            loved -> vvd_s.love.v.01
            paris -> city
            jonas -> mname
            cindy -> fname
            aaaaa -> char5

        Returns:
            list of str -- tags
        """
        if not pos:
            return self.tag_nonword(string)
        else:
            syntag = synset if synset else 'unk'
            return pos + '_' + syntag

    def propername_tag(self, string):
        if string in GrammarTagger.Cities:
            return 'city'
        elif string in GrammarTagger.Countries:
            return 'country'
        elif string in GrammarTagger.MaleNames:
            return 'mname'
        elif string in GrammarTagger.FemaleNames:
            return 'fname'
        elif string in GrammarTagger.Surnames:
            return 'surname'
        else:
            return None

    def tag_nonword(self, string):
        size = str(len(string))

        if re.fullmatch('\d+', string):
            category = 'number'
        elif re.fullmatch('[^a-zA-Z0-9]+', string):
            category = 'special'
        elif re.fullmatch('[a-zA-z]+', string):
            category = 'char'
        else:
            category = 'mixed'

        return category + size

    def is_propername(self, string):
        return string in GrammarTagger.MaleNames or \
            string in GrammarTagger.FemaleNames or \
            string in GrammarTagger.Cities or \
            string in GrammarTagger.Months or \
            string in GrammarTagger.Surnames or \
            string in GrammarTagger.Countries

class Processor(object):

    def __init__(self, tagger, tagtype):
        self.tagger = tagger
        self.tagtype = tagtype

    def __call__(self, data):

        process_id = multiprocessing.current_process()._identity[0]

        # log.info("Process {} received {} items.".format(process_id, len(data)))

        tags = defaultdict(Counter)
        base_structures = Counter()

        for x, count in data:
            base_structure = ''
            for string, pos, synset in x:
                tag = self.tagger._get_tag(string, pos, synset, self.tagtype)
                tags[tag][string] += count
                base_structure += '({})'.format(tag)

            base_structures[base_structure] += count


        # log.info("Process {} has done its share. Time to rest.".format(process_id))
        return (tags, base_structures)


class Grammar(object):

    def __init__(self, tagtype='backoff', estimator='mle'):
        self.base_structures = Counter()
        self.probabilities   = dict()
        self.tag_dicts       = defaultdict(Counter)
        # self.verb_treecut = None
        # self.noun_treecut = None
        self.estimator = estimator
        self.tagger = GrammarTagger()
        self.counter = 0                          # record # of observations

        # booleans
        self.lowres = None
        self.tagtype = tagtype

    def add_vocabulary(self, vocab):
        tagger = GrammarTagger()
        for string, pos, synset in vocab:
            tag = tagger._get_tag(string, pos, synset, self.tagtype)
            self.tag_dicts[tag][string] = 0

    def get_vocab(self):
        vocab = set()
        for tag_dict in self.tag_dicts.values():
            for word in tag_dict.keys():
                vocab.add(word)
        return vocab

    def _get_tag_prob_estimator(self,tag):
        samplesize          = sum(self.tag_dicts[tag].values())
        vocabsize           = len(self.tag_dicts[tag])
        if self.estimator == 'laplace':
            estimator = LaplaceEstimator(samplesize, vocabsize, 1)
        else:
            estimator = MleEstimator(samplesize)

        return estimator

    def fit_parallel(self, X, num_workers=4):
        import gc
        gc.collect()
        pool = Pool(num_workers, maxtasksperchild=2)

        share = min(int(2e5), math.ceil(len(X)/num_workers))
        # share = int(1e5)
        tagger = GrammarTagger()

        num_parts = math.ceil(len(X)/share)
        x_gen = (X[i*share:i*share+share] for i in range(num_parts))

        # delegate work to all available processes
        i  = 0
        for result in pool.imap(Processor(tagger, self.tagtype), x_gen):
            tag_results, base_struct_results = result
            for base_struct, count in base_struct_results.items():
                self.base_structures[base_struct] += count
                self.counter += count
            for tag, terminals in tag_results.items():
                for string, count in terminals.items():
                    self.tag_dicts[tag][string] += count
            i += 1
            log.info("Processed {}/{} result batches...".format(i, num_parts))


        log.info("Fitting completed.")

    def fit(self, X, num_workers=None):
        if num_workers:
            self.fit_parallel(X, num_workers)
            return

        for x, count in X:
            self.fit_incremental(x, count)

    def fit_incremental(self, x, count):
        """
        Args:
            x - a list of tuples in the form (string, pos, str(synset))
        """
        log.debug(x)
        base_structure = ''
        for string, pos, synset in x:
            tag = self.tagger._get_tag(string, pos, synset, self.tagtype)
            self.tag_dicts[tag][string] += count
            base_structure += '({})'.format(tag)

        self.base_structures[base_structure] += count
        log.debug(base_structure)

    def sample(self, N):
        """ Sample N observations from this probabilistic model.

        Return:
            list of tuples (password, base_struct, probability)
        """
        # Prepare data structures for fast-ish sampling

        base_structs      = []
        base_struct_probs = []
        tag2words         = dict() # tag2words['jj'] = ['hot', 'cold', ...]
        tag2probs         = dict() # tag2probs['jj'] = np.array([.1, .005, ...])

        for k, v in self.base_structures.items():
            base_structs.append(k)
            base_struct_probs.append(v)
        base_struct_probs = np.array(base_struct_probs)
        base_struct_probs = base_struct_probs/np.sum(base_struct_probs) # calculate MLE

        for tag, v in self.tag_dicts.items():
            W = []
            P = []
            estimator = self._get_tag_prob_estimator(tag)
            for word, count in v.items():
                W.append(word)
                P.append(estimator.probability(count))
            tag2words[tag] = W
            tag2probs[tag] = P

        # Sample

        base_struct_sample_indices = np.random.choice(  # sample from base structures
            len(base_structs), size=N,
            replace=True, p=base_struct_probs
        )

        # outcomes = []                            # final sample outcome:
        #                                          # list of tuples (string, prob)

        for i in base_struct_sample_indices:     # for each base structure,
            base_struct  = base_structs[i]       # sample a word from each of its tags
            outcome      = ''                    # one sampling outcome
            outcome_prob = base_struct_probs[i]

            for tag in re.findall('\(([^\(\)]+)\)', base_struct):
                pdist          = tag2probs[tag]
                j              = np.random.choice(len(pdist), replace=True, p=pdist)
                outcome       += tag2words[tag][j]
                outcome_prob  *= pdist[j]

            yield (outcome, base_struct, outcome_prob)


    def predict(self, X):
        """
        A generator that returns the probabilities of strings under
        this grammar.

        Args:
            X - a list of lists of tuples in the form (string, pos, str(synset))
        """

        tag_prob_cache = dict()         # tag_prob_cache[tag][word] = p

        def prob(tag, string):
            if tag not in tag_prob_cache:
                tag_prob_cache[tag] = dict()
                samplesize          = sum(self.tag_dicts[tag].values())
                vocabsize           = len(self.tag_dicts[tag].keys())

                if self.estimator == 'laplace':
                    estimator = LaplaceEstimator(samplesize, vocabsize, 1)
                else:
                    estimator = MleEstimator(samplesize)

                for k, count in self.tag_dicts[tag].items():
                    tag_prob_cache[tag][k] = estimator.probability(count)

            try:
                return tag_prob_cache[tag][string]
            except KeyError:
                return 0

        for x in X:
            base_structure = ''
            p = 1
            for string, pos, synset in x:
                tag = self.tagger._get_tag(string, pos, synset, self.tagtype)
                base_structure += '({})'.format(tag)

                p *= prob(tag, string)

            p *= self.base_structures[base_structure]/self.counter

            yield p


    def predict_async(self):
        """
        An asynchronous generator that returns the probabilities of
        strings under this grammar. This is useful for when the next
        input depends on the previous output.

        Example:
            > predict = predict_async()
            > predict.send(None)
            > predict.send([('hot', 'jj', None), ('dogs', 'nn2', 's.dog.n.01')])
              2.1873503560328376e-12

        Args:
            x - a list of tuples in the form (string, pos, str(synset))
        """

        tag_prob_cache = dict()         # tag_prob_cache[tag][word] = p

        def prob(tag, string):
            if tag not in tag_prob_cache:
                tag_prob_cache[tag] = dict()
                samplesize          = sum(self.tag_dicts[tag].values())
                vocabsize           = len(self.tag_dicts[tag].keys())

                if self.estimator == 'laplace':
                    estimator = LaplaceEstimator(samplesize, vocabsize, 1)
                else:
                    estimator = MleEstimator(samplesize)

                for k, count in self.tag_dicts[tag].items():
                    tag_prob_cache[tag][k] = estimator.probability(count)

            try:
                return tag_prob_cache[tag][string]
            except KeyError:
                return 0

        while True:
            x = yield
            base_structure = ''
            p = 1
            for string, pos, synset in x:
                tag = self.tagger._get_tag(string, pos, synset, self.tagtype)
                base_structure += '({})'.format(tag)

                p *= prob(tag, string)

            p *= self.base_structures[base_structure]/self.counter

            yield p


    def base_structure_probabilities(self):
        total = 0
        rank = self.base_structures.most_common()
        for struct, count in rank:
            total += count

        return [(struct, count/total) for struct, count in rank]

    def tag_probabilities(self):
        tag_dicts     = self.tag_dicts
        probabilities = defaultdict(Counter)

        for tag in tag_dicts.keys():
            samplesize = sum(tag_dicts[tag].values())
            vocabsize  = len(tag_dicts[tag].keys())

            if self.estimator == 'laplace':
                est = LaplaceEstimator(samplesize, vocabsize, 1)
            else:
                est = MleEstimator(samplesize)

            for lemma, freq in tag_dicts[tag].most_common():
                probabilities[tag][lemma] = est.probability(freq)

        return probabilities

    # def __getstate__(self):
    #     d = dict(self.__dict__)
    #     # these attributes will be saved in plain text (not pickled)
    #     d['base_structures'] = Counter()
    #     d['tag_dicts'] =  defaultdict(Counter)
    #     return d

    # def __setstate__(self, state):
    #

    def write_to_disk(self, path):
        # remove previous grammar
        try:
            shutil.rmtree(path)
        except OSError: # in case the above folder does not exist
            pass

        # recreate the folders empty
        os.makedirs(os.path.join(path, 'nonterminals'))

        with open(os.path.join(path, 'rules.txt'), 'w+') as f:
            for struct, p in self.base_structure_probabilities():
                f.write('{}\t{}\n'.format(struct, p))

        tags = self.tag_probabilities()
        for tag in tags.keys():
            with open(os.path.join(path, 'nonterminals', str(tag) + '.txt'), 'w+') as f:
                for lemma, p in tags[tag].most_common():
                    f.write("{}\t{}\n".format(lemma, p))

        self_filepath = os.path.join(path, 'grammar.pickle')
        pickle.dump(self, open(self_filepath, 'wb'), -1)


    def read(self, path):
        grammar_dir = util.abspath(path)

        with open(os.path.join(grammar_dir, 'rules.txt')) as f:
            for line in f:
                fields = line.split()
                tags = fields[0]
                # map grammar rule (tags) to probability
                self.base_structures[tags] = float(fields[1])

        tagdicts_dir = os.path.join(grammar_dir, 'nonterminals')

        for fname in os.listdir(tagdicts_dir):
            if not fname.endswith('.txt'): continue

            with open(os.path.join(tagdicts_dir, fname)) as f:
                tag = fname.replace('.txt', '')
                for line in f:
                    fields = line.split('\t')
                    try:
                        word, prob = fields
                        self.tag_dicts[tag][word] = float(prob)
                    except:
                        sys.stderr.write("error inserting {} in the tag dictionary {}\n"
                                .format(fields, tag))



    @classmethod
    def from_files(cls, path):
        gpath = os.path.join(path, 'grammar.pickle')
        g = pickle.load(open(gpath, "rb"))
        # g.read(path)
        return g
