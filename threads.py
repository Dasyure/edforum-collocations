"""
  Purpose: find the most common issues each week on EdForum.
  How: look for the most common phrases in either:
    -> the title of the post & the post itself
    -> only the title (recommended)

  Instructions:

    # Instructions/Recommendations:
    #   Set title_only == True/False
    #   -> for title only: max_phrase_len == 5, min_repeat == 2
    #   -> otherwise     : max_phrase_len == 4, min_repeat == 3
"""
import json
import re
import nltk
import ssl
from datetime import datetime, timedelta
FILE_NAME = "discussion-threads.json"  # json file needs to be in same directory
START_DATE = "11-09-2023"             # Monday Week 1
WEEK1_DATE = datetime.strptime(START_DATE, '%d-%m-%Y').date()
DATE_LEN = 10                         # str len of "11-09-2023" is 10
MAX_WEEKS = 15

def ignored_words_setup():
    """
      Disables ssl checking to download 'stopwords', probably not the safest thing to do
    """
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    nltk.download('stopwords')



def get_week(week, date):
    """
      Finds the week, given the current week and new date provided. 
      Assumes data is in ascending order.

      Parameters:
      param1 (week): 
      param2 (date): Description of the second parameter.

      Returns:
      return_type: Description of the return value.
    """
    date_to_check = datetime.strptime(date[:DATE_LEN], '%Y-%m-%d').date()
    days_to_add = (week - 1) * 7  # if week 1, then no change
    start_week = WEEK1_DATE + timedelta(days=days_to_add)
    end_week = start_week + timedelta(days=7)
    if (start_week <= date_to_check < end_week):
        return week
    elif (date_to_check < start_week):
        return week - 1
    elif (end_week <= date_to_check):
        return week + 1
    return None


def generate_data(title_only):
    """
      Description of the function and its arguments.

      Parameters:
      title_only (bool): Whether to search only the title, or title + text

      Returns:
      info (dict): key is the week number, value is a list of strings 
    """
    info = {}
    for week in range(0, MAX_WEEKS):
        info[week] = []
    week = 0
    data = json.load(open(FILE_NAME))
    for post in data:
        week = get_week(week, post["created_at"])
        if post["user"]["role"] == "student":
            if title_only:
                info[week].append(post["title"])
            else:
                info[week].append(f'{post["title"]} {post["text"]}')
    return info

def get_common_phrases(texts, ignored_words, maximum_length=3, minimum_repeat=2) -> dict:
    """
      Description of the function and its arguments.
      https://dev.to/mattschwartz/quickly-find-common-phrases-in-a-large-list-of-strings-9in

      Parameters:
      texts (obj): list of strings
      ignored_words (list): list of words to ignore from the analysis
      maximum_length (int): maximum amounts of words in a phrase to search for
      minimum_repeat (int): how many times the phrase has to repeat to be included

      Returns:
      longest_phrases (dict): key represents the phrase, value is the occurence
    """
    phrases = {}
    # break down the texts into phrases
    for t in texts:
        # Replace separators and punctuation with spaces
        text = re.sub(r'[.!?,:;/\-\s]', ' ', t)
        # Remove extraneous chars
        text = re.sub(r'[\\|@#$&~%\(\)*\"]', '', text)

        words = text.split(' ')
        # Remove stopwords and empty strings
        words = [w for w in words if len(w) and w.lower() not in ignored_words]
        length = len(words)
        # Look at phrases no longer than maximum_length words long
        size = length if length <= maximum_length else maximum_length
        while size > 0:
            pos = 0
            # Walk over all sets of words
            while pos + size <= length:
                phrase = words[pos:pos+size]
                phrase = tuple(w.lower() for w in phrase)
                if phrase in phrases:
                    phrases[phrase] += 1
                else:
                    phrases[phrase] = 1
                pos += 1
            size -= 1
    # remove phrases found less than the minimum required number of times
    phrases = {k: v for k, v in phrases.items() if v >= minimum_repeat}
    longest_phrases = {}
    keys = list(phrases.keys())
    keys.sort(key=len, reverse=True)
    # remove sub-phrases
    for phrase in keys:
        found = False
        for l_phrase in longest_phrases:
            # If the entire phrase is found in a longer tuple...
            intersection = set(l_phrase).intersection(phrase)
            if len(intersection) == len(phrase):
                # ... and their frequency overlaps by 75% or more, we'll drop it
                difference = (
                    phrases[phrase] - longest_phrases[l_phrase]) / longest_phrases[l_phrase]
                if difference < 0.25:
                    found = True
                    break
        if not found:
            longest_phrases[phrase] = phrases[phrase]
    return longest_phrases


def sorted_common_phrases(title_only, max_phrase_len, min_repeat):
    """
      Description of the function and its arguments.

      Parameters:
      param1 (type): Description of the first parameter.
      param2 (type): Description of the second parameter.

      Returns:
      return_type: Description of the return value.
    """
    info = generate_data(title_only)
    ignored_words_setup()
    ignored_words = nltk.corpus.stopwords.words('english')
    sorted_phrases = {}
    for week in range(0, MAX_WEEKS):
        sorted_phrases[week] = get_common_phrases(
            info[week], ignored_words, max_phrase_len, min_repeat)
        sorted_phrases[week] = dict(
            sorted(sorted_phrases[week].items(), key=lambda item: item[1], reverse=True))
        sorted_phrases[week] = dict(
            sorted(sorted_phrases[week].items(), key=lambda l: len(l[0]), reverse=True))
    return sorted_phrases

# TODO: make it able to choose between text or title
# print to text file?


'''
Formatting text files with choosen number of spaces
  num_occurences: (int) occurences of a word
  return: (int) how many spaces to between the num and phrase
'''


def number_of_spaces(num_occurences):
    """
      Description of the function and its arguments.

      Parameters:
      param1 (type): Description of the first parameter.
      param2 (type): Description of the second parameter.

      Returns:
      return_type: Description of the return value.
    """
    digits_occurences = len(str(num_occurences))
    if (digits_occurences > 2):
        return 1
    return 4 if digits_occurences == 1 else 3


def export_phrases(phrases):
    """
      Exports everything into a md file

      Parameters:
      phrases (dict): key is the week, value is a list of common phrases
    """
    for week in range(0, MAX_WEEKS):
        f = open(f'week{week}.txt', "w")
        for tupl, occurences in phrases[week].items():
            phrase = ' '.join(tupl)
            num_spaces = number_of_spaces(occurences)
            spaces = ' ' * num_spaces
            f.write(f'({occurences}){spaces}{phrase}\n')
        f.close()


if __name__ == "__main__":
    # Instructions/Recommendations:
    #   Set title_only == True/False
    #   -> for title only: max_phrase_len == 5, min_repeat == 2
    #   -> otherwise     : max_phrase_len == 4, min_repeat == 3
    title_only = True
    max_phrase_len = 5  # maximum words in a phrase
    min_repeat = 2      # minimum times a phrase has to repeat

    export_phrases(sorted_common_phrases(
        title_only, max_phrase_len, min_repeat))
