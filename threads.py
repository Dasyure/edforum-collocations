import json
FILE_NAME = "discussion-threads.json"

data = json.load(open(FILE_NAME))
# print(data[0])
for k, v in data[0].items():
  print(f'{k}:', v)
  print()

# print(data[0].items)