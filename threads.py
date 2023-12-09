"""
  PURPOSE: find the most common issues each week on EdForum.
  HOW: look for the most common phrases in either:
    -> the title of the post & the post itself
    -> only the title (recommended)

  INSTRUCTIONS:
    -> Set FILE_NAME for a json file in the same directory
    -> Set START_DATE to be the first Monday of Week 1 in the form "dd-mm-yyyy"
    -> Set TERM to the current term
    -> Set TITLE_ONLY == True/False (recommendation: set to true)
       -> for title only : MAX_PHRASE_LEN == 5, MIN_REPEAT == 2
       -> otherwise      : MAX_PHRASE_LEN == 4, MIN_REPEAT == 3
"""
import json
import re
import nltk
import ssl
import os
import pickle
from datetime import datetime, timedelta

# CHANGE BELOW
FILE_NAME = "discussion-threads.json"
START_DATE = "11-09-2023"
TERM = "23T3"
TITLE_ONLY = True
MAX_PHRASE_LEN = 5
MIN_REPEAT = 2
# ------------
WEEK1_DATE = datetime.strptime(START_DATE, '%d-%m-%Y').date()
DATE_LEN = 10  # str len of "11-09-2023" is 10
MAX_WEEKS = 14
IGNORED_WORDS_FILE = "ignored-words"


def ignored_words_setup(info):
    """
      Disables ssl checking to download 'stopwords', probably not the safest thing to do
    """
    if not os.path.exists(IGNORED_WORDS_FILE):
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context
        nltk.download('stopwords')
        ignored_words = nltk.corpus.stopwords.words('english')
        info["ignored_words"] = ignored_words
        with open(IGNORED_WORDS_FILE, "wb") as ignored_file:
            pickle.dump(ignored_words, ignored_file)
    else:
        with open(IGNORED_WORDS_FILE, "rb") as ignored_file:
            info["ignored_words"] = pickle.load(ignored_file)


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


def generate_data():
    """
      Loads the json file and stores the info in a dictionary organised by week.

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
            if TITLE_ONLY:
                info[week].append(post["title"])
            else:
                info[week].append(f'{post["title"]} {post["text"]}')
    ignored_words_setup(info)
    return info


def get_common_phrases(texts, ignored_words, maximum_length=MAX_PHRASE_LEN, minimum_repeat=MIN_REPEAT) -> dict:
    """
      Finds the common phrases given a list of strings, reference:
      -> https://dev.to/mattschwartz/quickly-find-common-phrases-in-a-large-list-of-strings-9in

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


def sorted_common_phrases():
    """
      Sorts list of common phrases by word length and then frequency. 

      Returns:
      return_type (dict): sorted dictionary of common phrases.
    """
    info = generate_data()
    sorted_phrases = {}
    for week in range(0, MAX_WEEKS):
        sorted_phrases[week] = get_common_phrases(info[week], info["ignored_words"])
        sorted_phrases[week] = dict(
            sorted(sorted_phrases[week].items(), key=lambda item: item[1], reverse=True))
        sorted_phrases[week] = dict(
            sorted(sorted_phrases[week].items(), key=lambda l: len(l[0]), reverse=True))
    return sorted_phrases

# def sorted_common_phrases_overall():
#     """
#       Sorts list of common phrases by word length and then frequency. 

#       Returns:
#       return_type (dict): sorted dictionary of common phrases. 
#     """
#     info = generate_data()
#     ignored_words_setup()
#     ignored_words = nltk.corpus.stopwords.words('english')
#     sorted_phrases = {}
#     for week in range(0, MAX_WEEKS):
#         sorted_phrases[week] = get_common_phrases(info[week], ignored_words)
#         sorted_phrases[week] = dict(
#             sorted(sorted_phrases[week].items(), key=lambda item: item[1], reverse=True))
#         sorted_phrases[week] = dict(
#             sorted(sorted_phrases[week].items(), key=lambda l: len(l[0]), reverse=True))
#     return sorted_phrases

def export_phrases(phrases):
    """
      Exports everything into a md file

      Parameters:
      phrases (dict): key is the week, value is a list of common phrases
    """
    f = open(f"edforum-issues-{TERM.lower()}.md", "w")
    f.write(f"# EdForum: Most Common Issues ({TERM})\n")
    f.write("This is done by searching for the most common phrases each week. <br>The ranking \
            gives preference to phrases with more words, then to frequency \
            of occurence. ")
    for week in range(0, MAX_WEEKS):
        rank = 1
        f.write("<details>")
        f.write(f"<summary><b>&nbsp; Week {week} </b></summary>\n")
        f.write("\n| Rank | Occurences | Phrase |\n")
        f.write("| :-----------: | :-----------: | ----------- |\n")
        for tupl, occurences in phrases[week].items():
            phrase = " ".join(tupl)
            f.write(f"| {rank} | {occurences} | {phrase} |\n")
            rank += 1
        f.write("</details>")
    f.close()


if __name__ == "__main__":
    export_phrases(sorted_common_phrases())
