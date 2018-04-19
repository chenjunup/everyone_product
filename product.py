import json
import re
from multiprocessing.pool import Pool
from urllib.parse import urlencode

import numpy as np
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from requests import RequestException

USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit"
    + "/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit"
    + "/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit"
    + "/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit"
    + "/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit"
    + "/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit"
    + "/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit"
    + "/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit"
    + "/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit"
    + "/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
]
client = MongoClient()
db = client.product


def get_index_page(page):
    headers = {
        'User-Agent': np.random.choice(USER_AGENT_LIST)
    }
    data = {
        'paged': page,
        'action': 'laodpost'
    }
    url = 'http://www.woshipm.com/__api/v1/stream-list?' + urlencode(data)
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.text
        return None
    except RequestException:
        print('请求初始页出错')
        return None


def parse_index_page(html):
    json_dict = json.loads(html)
    if json_dict and 'payload' in json_dict.keys():
        for item in json_dict.get('payload'):
            yield item.get('permalink')


def get_detail_page(url):
    headers = {
        'User-Agent': np.random.choice(USER_AGENT_LIST)
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.text
        return None
    except RequestException:
        print('请求详情页出错')
        return None


def parse_detail_page(html):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.select('.article-header h2')
    if title:
        title = title[0].text
    post_time = soup.select('.fa-clock-o')
    if post_time:
        post_time = post_time[0].parent.text
    watch = soup.select('.fa-eye')
    if watch:
        watch = watch[0].parent.text
    star = soup.select('.fa-star')
    if star:
        star = star[0].parent.text
    good = soup.select('.fa-thumbs-up')
    if good:
        good = good[0].parent.text
    articles = soup.select('.grap p')
    art_list = []
    if articles[:-4]:
        for art in articles[:-4]:
            art_list.append(art.text)
    article = str(art_list).replace(
        "['", '').replace("']", '').replace('\n', '').strip()
    article = re.sub("', '", '', article)
    tags = soup.select('.taglist a')
    tag_list = []
    for tag in tags:
        tag_list.append(tag.text)
    author = soup.select('.u-overflowHidden a')
    if author:
        author = author[0].text
    author_info = soup.select('.authorInfo-item i')
    if author_info:
        total_article = author_info[0].text
        total_watch = author_info[1].text
    else:
        total_article = None
        total_watch = None
    comment = soup.select('.comment-content p')
    if comment:
        comment = len(comment)
    return {
        'title': title,
        'time': post_time,
        'watch': watch,
        'star': star,
        'good': good,
        'article': article,
        'tag': tag_list,
        'author': author,
        'total_article': total_article,
        'total_watch': total_watch,
        'comment': comment
    }


def main(offset):
    html = get_index_page(offset)
    for url in parse_index_page(html):
        html = get_detail_page(url)
        infos = parse_detail_page(html)
        if db.everyone_product_more.insert_one(infos):
            print('文章{0}存入MongoDB成功'.format(infos.get('title')))


if __name__ == '__main__':
    pool = Pool()
    pool.map(main, [i for i in range(3000)])
    pool.close()
    pool.join()
