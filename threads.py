import json
import re
import nltk
import ssl
from datetime import datetime, timedelta
FILE_NAME = "discussion-threads.json"
START_DATE = "11-09-2023"
DATE_LEN = 10
WEEK1_DATE = datetime.strptime(START_DATE, '%d-%m-%Y').date()

# Global variables
info = {} # information by week, includes either title and/or text
data = json.load(open(FILE_NAME))
# for k, v in data[0].items():
#   print(f'{k}:', v)
#   print()

def setup():
  # Disable ssl checking to download 'stopwords'
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
  for week in range(0,15):
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
def generate_data():
  generate_info_structure()
  week = 0
  for post in data:
    week = check_week(week, post["created_at"])
    if post["user"]["role"] == "student":
      # print(f'{week}: {post["created_at"]}')
      info[week].append(post["title"])
  return info[week]

# https://dev.to/mattschwartz/quickly-find-common-phrases-in-a-large-list-of-strings-9in
def get_common_phrases(texts, maximum_length=3, minimum_repeat=2) -> dict:
  pass

generate_data()
print(info[0])

# print(posts)
# print(START_DATE)

# print(len(data[0]["comments"]))