from learning.tree.wordnet      import IndexedWordNetTree
from learning.tree.default_tree import TreeCut
from learning.tree.cut          import wagner, li_abe
from collections                import defaultdict, Counter
from multiprocessing            import Process, Manager

from misc import util

import shutil
import re
import os
import logging
import numpy as np
import pickle
import math

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
    return open(os.path.join(os.path.dirname(__file__), '../data/'+name))


class Grammar(object):

    MaleNames   = [name.strip() for name in _datafile('mnames.txt')]
    FemaleNames = [name.strip() for name in _datafile('fnames.txt')]
    Countries   = [country.strip() for country in _datafile('countries.txt')]
    Months      = [month.strip() for month in _datafile('months.txt')]
    Surnames    = [surname.strip() for surname in _datafile('surnames.txt')]
    Cities      = [city.strip() for city in _datafile('cities.txt')]

    def __init__(self, tagtype='backoff', estimator='mle'):
        self.base_structures = Counter()
        self.probabilities   = dict()
        self.tag_dicts       = defaultdict(lambda : Counter())
        self.verb_treecut = None
        self.noun_treecut = None
        self.estimator = estimator

        # booleans
        self.lowres = None
        self.tagtype = tagtype

    def add_vocabulary(self, vocab):
        for string, pos, synset in vocab:
            tag = self._get_tag(string, pos, synset, self.tagtype)
            self.tag_dicts[tag][string] = 0

    def fit_parallel(self, X, num_workers=4):
        def do_work(batch, tag_out, base_struct_out):
            tags = []
            base_structures = []

            for x, count in batch:
                base_structure = ''
                for string, pos, synset in x:
                    tag = self._get_tag(string, pos, synset, self.tagtype)
                    tags.append((tag, string, count))
                    base_structure += '({})'.format(tag)

                base_structures.append((base_structure, count))

            tag_out.extend(tags)
            base_struct_out.extend(base_structures)

        manager = Manager()
        tag_results = manager.list()
        base_struct_results = manager.list()

        share = math.ceil(len(X)/num_workers)
        for i in range(num_workers):
            work = X[i*share:i*share+share]
            p = Process(target=do_work,
                        args=(work, tag_results, base_struct_results))
            p.start()
            pool.append(p)

        for p in pool:
            p.join()

        for tag, string, count in tag_results:
            self.tag_dicts[tag][string] += count

        for base_structure, count in base_struct_results:
            self.base_structures[base_structure] += count

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
            tag = self._get_tag(string, pos, synset, self.tagtype)
            self.tag_dicts[tag][string] += count
            base_structure += '({})'.format(tag)

        self.base_structures[base_structure] += count
        log.debug(base_structure)


    def base_structure_probabilities(self):
        total = 0
        rank = self.base_structures.most_common()
        for struct, count in rank:
            total += count

        return [(struct, count/total) for struct, count in rank]

    def tag_probabilities(self):
        tag_dicts = self.tag_dicts
        probabilities = defaultdict(Counter)
        for tag in tag_dicts.keys():
            samplesize = sum(tag_dicts[tag].values())
            vocabsize = len(tag_dicts[tag].keys())

            if self.estimator == 'laplace':
                est = LaplaceEstimator(samplesize, vocabsize, 1)
            else:
                est = MleEstimator(samplesize)

            for lemma, freq in tag_dicts[tag].most_common():
                probabilities[tag][lemma] = est.probability(freq)

        return probabilities

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
                    f.write("{}\t{}\n".format(lemma.encode('utf-8'), p))

        # pickle the tree cuts
        with open(os.path.join(path, "noun-treecut.pickle"), 'wb') as f:
            pickle.dump(self.noun_treecut, f, -1)

        with open(os.path.join(path, "verb-treecut.pickle"), 'wb') as f:
            pickle.dump(self.verb_treecut, f, -1)

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
        'unkwn'.
        Examples:
            love    -> vb
            123     -> number3
            audh    -> char4
            kripton -> unkwn
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
        synset exists,  the symbol 'unkwn' is used. Aside from these classes, there
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
            syntag = synset if synset else 'unkwn'
            return pos + '_' + syntag

    def propername_tag(self, string):
        if string in Grammar.MaleNames:
            return 'mname'
        elif string in Grammar.FemaleNames:
            return 'fname'
        elif string in Grammar.Cities:
            return 'city'
        elif string in Grammar.Months:
            return 'month'
        elif string in Grammar.Surnames:
            return 'surname'
        elif string in Grammar.Countries:
            return 'country'
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
                words = []
                for line in f:
                    fields = line.split('\t')
                    try:
                        word, prob = fields
                        words.append(word)
                        self.probabilities[(tag, word)] = float(prob)
                    except:
                        sys.stderr.write("error inserting {} in the tag dictionary {}\n"
                                .format(fields, tag))
                self.tag_dicts[tag] = words

        with open(os.path.join(grammar_dir, 'verb-treecut.pickle'), 'rb') as f:
            self.verb_treecut = pickle.load(f)
        with open(os.path.join(grammar_dir, 'noun-treecut.pickle'), 'rb') as f:
            self.noun_treecut = pickle.load(f)
        with open(os.path.join(grammar_dir, 'params.pickle'), 'rb') as f:
            opts = pickle.load(f)
            self.lowres = opts.lowres
            self.tagtype = opts.tags

    @classmethod
    def from_files(cls, path):
        g = cls()
        g.read(path)
        return g
