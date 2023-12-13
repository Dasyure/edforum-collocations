# edforum-collocations
This script finds the most common issues students face on the [Ed Discussion forum](https://edstem.org/), on a week by week basis. It searches for the most common phrases in either:
- the title only (recommended)
- the title and the content of the post

You will need to have admin access on Ed Discussion for your relevant course. Export all data for that term into a `json` file. 

## Instructions
At the top of `edforum-issues.py`, change these constants:
- `FILE_NAME`: a json file in the same directory with the Ed Discussion data stored into a json file.
- `START_DATE`: the first Monday of Week 1 in the form "dd-mm-yyyy".
- `TERM`: the current term, e.g. "23T3".  

Optionally, you may change these constants as well:
- `MAX_RESULTS_PER_WEEK`: the number of results you want to see for each week.
- `SEARCH_TITLE_ONLY`: True or False *(recommendation: set to true)*
  - True: only searches through the post's titles (suggested values: `MAX_PHRASE_LEN` == 5, `MIN_REPEAT` == 2)
  - False: searches through titles and text (suggested values: `MAX_PHRASE_LEN` == 4, `MIN_REPEAT` == 3)

Running `python3 edforum-issues.py` will generate a markdown file with the results.  
A binary file `ignored-words` will also be generated but you may ignore it. 

## File Structure
```
generate_data
  -> get_week
  -> ignored_words_setup
sorted_common_phrases
  -> get_common_phrases
export_phrases
  -> export_one_list
```
