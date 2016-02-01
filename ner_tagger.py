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
 		self.featurize(words,"featurized_test",False)
 		os.system("java -cp " +\
 			"\"../mallet-2.0.8RC3/class:../mallet-2.0.8RC3/lib/mallet-deps.jar\" " +\
 			"cc.mallet.fst.SimpleTagger " +\
 			"--model-file trained_model featurized_test > tagged_test" )
 		print self.get_precision_and_recall(words,"tagged_test")


 	def get_precision_and_recall(self,tweets,test):
 		"""Compares the gold standard with the tagged file
 		returns precision, recall"""
 		tp = 0
 		fp = 0
 		tn = 0
 		fn = 0
 		total = 0
 		t = open(test)
 		g = [word for words in tweets for word in words]
 		for line in t:
 			new = line.strip()
 			if len(new) == 0:
 				continue
 			gold = g[total][-1]
 			if gold == "O":
 				if new == "O":
 					tn += 1
 				else:
 					fp += 1
 			else:
 				if new == gold:
 					tp += 1
 				else:
 					fn += 1
 			total += 1
 		return float(tp)/float(tp+fp),float(tp)/float(tp+fn)


	def featurize(self,tweets,output="featurized",label=True):
		"""Takes the output of WrapperTools and creates a document
		in the necessary format for Mallet, i.e. 
		f1 f2 ... fn label"""
		fw = open(output,"w")
		# Put featurizing methods here; if they are all in the output format 
		# [[f1, f2, word, tag]...], just appending each new feature to the beginning
		# of the list, it should be easy to write to the file and keep all features separate
		# Inefficient, but easier to keep straight when all of us 
		# work on separate features

		#names_dict is only retrieved once to increase efficiency
		names_dict = self.read_names("census_first_names", {})
		names_dict = self.read_names("census_last_names", names_dict)

		tweets = starts_with_punctuation(tweets)
		tweets = is_word_shape_like_ne(tweets)
		tweets = self.is_a_name(tweets, names_dict)
		tweets = self.whole_tweet_is_upper_lower(tweets)


		for tweet in tweets:
			for word in tweet:
				for i in range(len(word)):
					if i < len(word)-1 or label:
						fw.write(str(word[i])+" ")
				fw.write("\n")
		fw.close()
		return

	def is_a_name(self, tweets, names_dict):
		for tweet in tweets:
			for word in tweet:
				word.insert(0, word[-2].lower() in names_dict)
		return tweets


	def read_names(self, filename, names_dict):
		""" 
			Retrieves names fron census bureau files
		"""
		the_file = open(filename)
		all_lines = the_file.readlines()
		# line.split()[0] is the name itself
		# hashing allows of O(1) checks. The 1 is meaningless
		for line in all_lines:
			names_dict[line.split()[0].lower()] = 1
		return names_dict


	def whole_tweet_is_upper_lower(self, tweets):
		"""
			Checks to see if the whole tweet is in one case
		"""
		for tweet in tweets:
			boolean = self.individual_tweet_is_upper_lower(tweet)
			# apply feature to each word in tweet
			for word in tweet:
				word.insert(0, boolean)
		return tweets


	def individual_tweet_is_upper_lower(self, tweet):
		"""
			Helper method for whole_tweet_is_upper_lower
		"""
		lower = [1 for word in tweet if word[-2].islower()]
		upper = [1 for word in tweet if word[-2] isupper()]
		return len(upper) == len(tweet) or len(lower) == len(tweet)

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
 	#NT.train("./proj1-data/train.gold")
 	NT.test("./proj1-data/dev.gold")
