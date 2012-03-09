from nltk.tag import NgramTagger, SequentialBackoffTagger
from nltk.corpus import wordnet, names
from nltk.probability import FreqDist
import csv
from root.tagset_conversion import TagsetConverter

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

if __name__ == '__main__':
	import doctest
	doctest.testmod()