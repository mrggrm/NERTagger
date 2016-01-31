import os
import re
from data_wrapper import WrapperTools

class NER_Tagger:
	"""A simple NER tagger"""

	def train(self,training_file):
		"""Trains a CRF tagger using Mallet"""
		wt = WrapperTools()
 		words = wt.unwrap(training_file)
 		self.featurize(words,"featurized_training")
 		os.system("java -cp " +\
 			"\"../mallet-2.0.8RC3/class:../mallet-2.0.8RC3/lib/mallet-deps.jar\" " +\
 			"cc.mallet.fst.SimpleTagger --train true " +\
 			"--model-file trained_model featurized_training")


	def test(self,test_file):
		"""Tests the trained tagger using Mallet"""
		wt = WrapperTools()
 		words = wt.unwrap(test_file)
 		self.featurize(words,"featurized_test")
 		os.system("java -cp " +\
 			"\"../mallet-2.0.8RC3/class:../mallet-2.0.8RC3/lib/mallet-deps.jar\" " +\
 			"cc.mallet.fst.SimpleTagger " +\
 			"--model-file featurized_training featurized_test" )


	def featurize(self,tweets,output="featurized"):
		"""Takes the output of WrapperTools and creates a document
		in the necessary format for Mallet, i.e. 
		f1 f2 ... fn label"""
		fw = open(output,"w")
		# Put featurizing methods here; if they are all in the output format 
		# [[f1, f2, word, tag]...], just appending each new feature to the beginning
		# of the list, it should be easy to write to the file and keep all features separate
		# Inefficient, but easier to keep straight when all of us 
		# work on separate features
		tweets = starts_with_punctuation(tweets)
		tweets = is_word_shape_like_ne(tweets)
		for tweet in tweets:
			for word in tweet:
				for f in word:
					fw.write(str(f)+" ")
				fw.write("\n")
		fw.close()
		return

def starts_with_punctuation(tweets):
	for tweet in tweets:
		i = 0
		for entry in tweet:
			word = entry[-2]
			if word.startswith("@") or word.startswith("#") or len(word) < 2:
				entry.insert(0,False)
			elif word.find("http") > -1 or re.search(r"\.[a-z]{3}",word):
				entry.insert(0,False)
			else:
				entry.insert(0,True)
			i+=1
	return tweets

def is_word_shape_like_ne(tweets):
	"""Adds a feature for whether the word shape is likely to be 
	a named entity, checking that the previous word is not EOS,
	and other punctuation"""
	capsword = re.compile(r"[A-Z][a-z]+")
	punc = re.compile(r"[.!?:]")
	caps_non_entities = load_set_from_file("capitalized_non_entities.txt")
	for tweet in tweets:
		i = 0
		for entry in tweet:
			word = entry[-2]
			if word.lower() in caps_non_entities:
				entry.insert(0,False)
			elif re.match(capsword,word) and i != 0 and not re.match(punc,tweet[i-1][-2]):
					entry.insert(0,True)
			else:
				entry.insert(0,False)
			i+=1
	return tweets

def load_set_from_file(filename):
	newset = set()
	f = open(filename)
	for line in f:
		newset.add(line.strip().lower())
	return newset
			

if __name__ == "__main__":
	wt = WrapperTools()
 	words = wt.unwrap("./proj1-data/train.gold")
 	NT = NER_Tagger()
 	NT.train("./proj1-data/train.gold")
 	NT.test("./proj1-data/dev.gold")





