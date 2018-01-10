from json import JSONDecodeError
import pandas as pd
import json

with open('article.json', 'r', errors='ignore', encoding='utf-8') as f:
    lines = f.readlines()
lis = []
for line in lines:
    try:
        dic = json.loads(line)
        lis.append(dic)
    except JSONDecodeError:
        print(line)
df = pd.DataFrame(lis)
df.to_excel('article.xlsx')
