from nltk.tag import NgramTagger, SequentialBackoffTagger
from nltk.corpus import wordnet, names
from nltk.probability import FreqDist
import csv
from root.tagset_conversion import TagsetConverter
from sentiwordnet import SentiWordNetCorpusReader, SentiSynset
from nltk.corpus import wordnet as wn
from sets import Set

class QuadgramTagger(NgramTagger):
	def __init__(self, *args, **kwargs):
		NgramTagger.__init__(self, 4, *args, **kwargs)

class WordNetTagger(SequentialBackoffTagger):
	'''
	>>> wt = WordNetTagger()
	>>> wt.tag(['food', 'is', 'great'])
	[('food', 'NN'), ('is', 'VB'), ('great', 'JJ')]
	'''
	def __init__(self, *args, **kwargs):
		SequentialBackoffTagger.__init__(self, *args, **kwargs)
		
		self.wordnet_tag_map = {
			'n': 'NN',
			's': 'JJ',
			'a': 'JJ',
			'r': 'RB',
			'v': 'VB'
		}
	
	def choose_tag(self, tokens, index, history):
		word = tokens[index]
		fd = FreqDist()
		
		for synset in wordnet.synsets(word):
			fd.inc(synset.pos)
		
		return self.wordnet_tag_map.get(fd.max())

class NamesTagger(SequentialBackoffTagger):
	'''
	>>> nt = NamesTagger()
	>>> nt.tag(['Jacob'])
	[('Jacob', 'NNP')]
	'''
	def __init__(self, *args, **kwargs):
		SequentialBackoffTagger.__init__(self, *args, **kwargs)
		self.name_set = set([n.lower() for n in names.words()])
	
	def choose_tag(self, tokens, index, history):
		word = tokens[index]
		
		if word.lower() in self.name_set:
			return 'NNP'
		else:
			return None

class COCATagger(SequentialBackoffTagger):
	def __init__(self, *args, **kwargs):
		SequentialBackoffTagger.__init__(self, *args, **kwargs)
		coca_list = csv.reader(open('../files/coca_500k.csv'), delimiter='	')
		self.tag_map = dict([(row[1], row[2]) for row in coca_list])
		self.tagset_converter = TagsetConverter()
	
	def choose_tag(self, tokens, index, history):
		word = tokens[index]
		return self.tagset_converter.claws7ToBrown(self.tag_map[word]) if word in self.tag_map else None

class SentiWordnetTagger():
	def __init__(self):
		f = '../files/SentiWordNet_3.0.0_20120206.txt'
		self.swn = SentiWordNetCorpusReader(f)
	
	def tag(self, word, pos):
		synsets = self.swn.senti_synsets(word, pos)
		
		if not synsets: return None
		
		s = synsets[0]
		ident = s.offset
		if s.pos_score > s.neg_score:	 tag = 'p'
		elif  s.pos_score < s.neg_score: tag = 'n'
		else:							 tag = 'z'
		
		return (ident, tag)

class SemanticTagger():
	
	def __init__(self):
		self.categories = (	
						(self.synsets('animal'), 'animal'),
						(self.synsets('food'), 'food'),
						(self.synsets('emotion'), 'emotion'),
						(self.synsets('color'), 'color'),
						(self.synsets('place'), 'place'),
						(self.synsets('sexual_activity', 'sexy'), 'sexual'),
						(self.synsets('professional'), 'profession'),
						(self.synsets('belief', 'religious_person'), 'religious' ),
						(self.synsets('nation', 'inhabitant'), 'nation' ),
						(self.synsets('body_part'), 'body' ),
						(self.synsets('time_period'), 'time' ),
						(self.synsets('clothing'), 'clothing' ),
						(self.synsets('sports'), 'sports' )
						)
	
	def synsets(self, *args):
		a = set()
		for s in args:
			a |= set(wn.synsets(s))
		return a
	
	def _tagIt(self, s):
		paths = s.hypernym_paths()
		for p in paths:
			for cat in self.categories:
				if set(p).intersection(cat[0]):
					return cat[1]
		return None
	
	def tag(self, *args):
		if (len(args)==2):
			return self.tag_by_pos_offset(args[0], args[1])
		else:
			return self.tag_by_word(args[0])
		
	
	def tag_by_pos_offset(self, pos, offset):
		if not (pos and offset): return None
		
		s = wn._synset_from_pos_and_offset(pos, offset)
		
		return self._tagIt(s)
	
	def tag_by_word(self, word):
		try:
			s = wn.synsets(word)[0]
		except IndexError:
			return None
		
		return self._tagIt(s)
	

#s = wn.synsets('hat')[0]
#print s.definition
#t = SemanticTagger()
#
#tag = t.tag('n', s.offset)
#
#print tag