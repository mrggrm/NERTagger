import re

class WrapperTools:
    """
        Instantiate this class then use unwrap to open 
        data files
    """

    def unwrap(self, filepath):
        """
            Use this method to get data from files
            returns it in the form:
                [ [[word, tag]...[word, tag]], [[word, tag]...[word, tag]], ...]
        """
        all_lines = self.get_file_lines(filepath)
        split_tweets = self.split_tweets(all_lines)
        tagged = self.separate_tags(split_tweets)
        return tagged


    def separate_tags(self, split_tweets):
        """
           calls separate_tag_for_single_word on each word
           in each tweet 
        """
        tagged = split_tweets
        for tweet_index, tweet in enumerate(tagged):
            for word_index, word in enumerate(tweet):
                tagged[tweet_index][word_index] = self.separate_tag_for_single_word(word)
        return tagged


    def separate_tag_for_single_word(self, word):
        """
            removes newline and splits the word from the tag
        """
        word = re.sub(r'\n', '', word)
        word = word.split("\t")
        return word

    def split_tweets(self, all_lines):
        """
            returns: [ [a tweet] [another tweet] ... ]
        """
        split_by_tweets = []
        curr_tweet = []
        for token in all_lines:
            if token == "\n":
                split_by_tweets.append(curr_tweet)
                curr_tweet = []
            else:
                curr_tweet.append(token)
        return split_by_tweets


    def get_file_lines(self, filepath):
        """
            Opens the file and returns the lines
        """
        the_file = open(filepath)
        all_lines = the_file.readlines()
        return all_lines
