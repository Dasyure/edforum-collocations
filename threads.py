import json
import re
import nltk
import ssl
from datetime import datetime, timedelta
FILE_NAME = "discussion-threads.json"
START_DATE = "11-09-2023"
DATE_LEN = 10
MAX_WEEKS = 15
MAX_PHRASE_LEN = 4
MIN_REPEAT = 3
WEEK1_DATE = datetime.strptime(START_DATE, '%d-%m-%Y').date()

# Global variables
# info = {} # information by week, includes either title and/or text
data = json.load(open(FILE_NAME))

def setup():
  # Disable ssl checking to download 'stopwords', probably not the safest thing to do
  try:
      _create_unverified_https_context = ssl._create_unverified_context
  except AttributeError:
      pass
  else:
      ssl._create_default_https_context = _create_unverified_https_context
  nltk.download('stopwords')
setup()
ignored_words = nltk.corpus.stopwords.words('english')

def generate_info_structure():
  for week in range(0, MAX_WEEKS):
    info[week] = []

def check_week(week, date):
  date_to_check = datetime.strptime(date[:DATE_LEN], '%Y-%m-%d').date()

  days_to_add = (week - 1) * 7 #if week 1, then no change
  start_week = WEEK1_DATE + timedelta(days=days_to_add)
  end_week = start_week + timedelta(days=7)
  if (start_week <= date_to_check < end_week):
    return week
  elif (date_to_check < start_week):
    return week - 1
  elif (end_week <= date_to_check):
    return week + 1
  return None

'''
Assumes json file is in ascending order by date
'''
def generate_data(title_only):
  # generate_info_structure()
  info = {}
  for week in range(0, MAX_WEEKS):
    info[week] = []
  week = 0
  for post in data:
    week = check_week(week, post["created_at"])
    if post["user"]["role"] == "student":
      if title_only: 
        info[week].append(post["title"])
      else:
        info[week].append(f'{post["title"]} {post["text"]}')
  return info

# https://dev.to/mattschwartz/quickly-find-common-phrases-in-a-large-list-of-strings-9in
def get_common_phrases(texts, maximum_length=3, minimum_repeat=2) -> dict:
  phrases = {}
  #break down the texts into phrases
  for t in texts:
    # Replace separators and punctuation with spaces
    text = re.sub(r'[.!?,:;/\-\s]', ' ', t)
    # Remove extraneous chars
    text = re.sub(r'[\\|@#$&~%\(\)*\"]', '', text)

    words = text.split(' ')
    # Remove stop words and empty strings
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
            difference = (phrases[phrase] - longest_phrases[l_phrase]) / longest_phrases[l_phrase]
            if difference < 0.25:
                found = True
                break
    if not found:
        longest_phrases[phrase] = phrases[phrase]
  return longest_phrases

def sorted_common_phrases(title_only, max_phrase_len, min_repeat):
  info = generate_data(title_only)
  sorted_phrases = {}
  for week in range(0, MAX_WEEKS):
    sorted_phrases[week] = get_common_phrases(info[week], max_phrase_len, min_repeat)
    sorted_phrases[week] = dict(sorted(sorted_phrases[week].items(), key=lambda item: item[1], reverse=True))
    sorted_phrases[week] = dict(sorted(sorted_phrases[week].items(), key=lambda l: len(l[0]), reverse=True))
  return sorted_phrases

# TODO: make it able to choose between text or title
# print to text file?

if __name__ == "__main__":
  # Instructions/Recommendations:
  #   Set title_only == True/False
  #   -> for title only: max_phrase_len == 5, min_repeat == 2
  #   -> otherwise     : max_phrase_len == 4, min_repeat == 3
  title_only = True
  max_phrase_len = 5  # maximum words in a phrase
  min_repeat = 2      # minimum times a phrase has to repeat
  week = 1            # which week to find common phrases for
  # sorted_common_phrases(max_phrase_len, min_repeat)
  for k, v in sorted_common_phrases(title_only, max_phrase_len, min_repeat)[week].items():
   print(f'{k}: {v}')