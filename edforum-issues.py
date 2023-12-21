"""
  PURPOSE: find the most common issues each week on EdForum by looking for the
    most common phrases in either:
    -> the title of the post & the post itself
    -> only the title (recommended)

  INSTRUCTIONS:
    Set these constants:
    -> FILE_NAME: a json file in the same directory with EdForum data.
    -> START_DATE: the first Monday of Week 1 in the form "dd-mm-yyyy".
    -> TERM: current term.
    -> MAX_RESULTS_PER_WEEK: however many results you want to see each week.
    -> SEARCH_TITLE_ONLY: == True/False (recommendation: set to true)
       -> (True): only searches through the post's titles
                  Suggested values: MAX_PHRASE_LEN == 5, MIN_REPEAT == 2
       -> (False): searches through titles and text
                  Suggested values: MAX_PHRASE_LEN == 4, MIN_REPEAT == 3
"""
import json
import re
import nltk
import ssl
import os
import pickle
from datetime import datetime, timedelta

# MUST CHANGE BELOW:
FILE_NAME = "discussion-threads.json"
START_DATE = "11-09-2023"
TERM = "23T3"
# OPTIONAL TO CHANGE:
MAX_RESULTS_PER_WEEK = 50
SEARCH_TITLE_ONLY = True
MAX_PHRASE_LEN = 5
MIN_PHRASE_LEN = 1
MIN_REPEAT = 2  # minimum times a phrase has to occur to be logged
# ------------
WEEK1_DATE = datetime.strptime(START_DATE, '%d-%m-%Y').date()
DATE_LEN = 10  # str len of "11-09-2023" is 10
MAX_WEEKS = 14  # students usually stop posting by week 12, but just in case...
IGNORED_WORDS_FILE = "ignored-words" # reduces need to download list of stopwords


def ignored_words_setup(info):
    """
      Disables ssl checking to download 'stopwords', probably not the safest thing to do

      Parameters:
      info (dict): holds the list of phrases for each week.
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
      week (int): current week.
      date (str): new date, need to find its week.

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
    info = {week: [] for week in range(0, MAX_WEEKS)}
    week = 0
    data = json.load(open(FILE_NAME))
    # Sorts data in ascending order by date.
    data.sort(key=lambda post: datetime.strptime(
        post["created_at"][:DATE_LEN], '%Y-%m-%d').date())
    for post in data:
        week = get_week(week, post["created_at"])
        if post["user"]["role"] == "student":
            if SEARCH_TITLE_ONLY:
                info[week].append(post["title"])
            else:
                info[week].append(f'{post["title"]} {post["text"]}')
    ignored_words_setup(info)
    return info


def get_common_phrases(texts, ignored_words, maximum_length=MAX_PHRASE_LEN, minimum_repeat=MIN_REPEAT):
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
        print(words)
        print("######")
        # Look at phrases no longer than maximum_length words long
        size = length if length <= maximum_length else maximum_length
        while size > 0 and size >= MIN_PHRASE_LEN:
            pos = 0
            # Walk over all sets of words
            while pos + size <= length:
                phrase = words[pos:pos+size]
                print(f'size: {size}, pos: {pos}')
                print(phrase)
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


def sort_one_list(k, phrase_list, sorted_phrases):
    """
      Sorts common phrases by word length and then frequency, for each week.

      Parameters:
      k (int/str): either the number of the week or the word 'overall'
      phrase_list (list of str): list of string to find common phrases from
      sorted_phrases (dict): store results into a key of this dict

      Returns:
      sorted_phrases (dict): sorted dictionary of common phrases.
    """
    sorted_phrases[k] = get_common_phrases(phrase_list, info["ignored_words"])
    sorted_phrases[k] = dict(
        sorted(sorted_phrases[k].items(), key=lambda post: post[1], reverse=True))
    return dict(
        sorted(sorted_phrases[k].items(), key=lambda post: len(post[0]), reverse=True))


def sorted_common_phrases(info):
    """
      Sorts common phrases by word length and then frequency, for each week.

      Parameters:
      info (dict): holds the list of phrases for each week.

      Returns:
      return_type (dict): sorted dictionary of common phrases.
    """
    sorted_phrases = {}
    all_phrases = []
    for week in range(0, MAX_WEEKS):
        all_phrases += info[week]
        sorted_phrases[week] = sort_one_list(week, info[week], sorted_phrases)
    sorted_phrases["overall"] = sort_one_list(
        "overall", all_phrases, sorted_phrases)
    return sorted_phrases


def export_one_list(f, k, phrase_list):
    """
      Exports one week into md file.

      Parameters:
      f (file): file to write to.
      k (int/str): either the number of the week, or the word "overall".
      phrases (dict): key is the week, value is a list of common phrases
    """
    heading = f"Week {k}" if type(
        k) == int else f"OVERALL: Top {MAX_RESULTS_PER_WEEK} issues this term."
    rank = 1
    f.write("<details>")
    f.write(f"<summary><b>&nbsp; {heading} </b></summary>\n")
    f.write("\n| Rank | Occurences | Phrase |\n")
    f.write("| :-----------: | :-----------: | ----------- |\n")
    for tupl, occurences in phrase_list.items():
        phrase = " ".join(tupl)
        f.write(f"| {rank} | {occurences} | {phrase} |\n")
        if rank == MAX_RESULTS_PER_WEEK:
            break
        rank += 1
    f.write("</details>")


def export_phrases(phrases):
    """
      Exports everything into a md file

      Parameters:
      phrases (dict): key is the week, value is a list of common phrases
    """
    f = open(f"edforum-issues-{TERM.lower()}.md", "w")
    f.write(f"# EdForum: Most Common Issues ({TERM})\n")
    f.write("This is done by searching for the most common phrases each week. \
            <br>The list is sorted by the number of words in a phrase, then by \
            frequency with which they occur. ")
    for week in range(0, MAX_WEEKS):
        export_one_list(f, week, phrases[week])
    export_one_list(f, "overall", phrases["overall"])
    f.close()


if __name__ == "__main__":
    """
      FILE STRUCTURE:
        generate_data
          -> get_week
          -> ignored_words_setup
        sorted_common_phrases
          -> get_common_phrases
        export_phrases
          -> export_one_list
    """
    info = generate_data()
    export_phrases(sorted_common_phrases(info))
