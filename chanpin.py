import json
from multiprocessing.pool import Pool
from urllib.parse import urlencode
import os
import requests
from bs4 import BeautifulSoup
from requests import RequestException
import re


def get_index_page(page):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      + 'Chrome/55.0.2883.87 Safari/537.36',
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      + 'Chrome/55.0.2883.87 Safari/537.36',
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
    titles = soup.select('.article-header h2')
    if titles:
        title = titles[0].text
    else:
        title = 'NaN'
    infos = soup.select('.post-meta-item')
    if len(infos) > 3:
        post_time = infos[0].text
        watch = infos[1].text
        collect = infos[2].text
        good = infos[3].text
    elif len(infos) > 2:
        post_time = infos[0].text
        watch = infos[1].text
        collect = infos[2].text
        good = 'NaN'
    elif len(infos) > 1:
        post_time = infos[0].text
        watch = infos[1].text
        collect = 'NaN'
        good = 'NaN'
    elif len(infos) > 0:
        post_time = infos[0].text
        watch = 'NaN'
        collect = 'NaN'
        good = 'NaN'
    else:
        post_time = 'NaN'
        watch = 'NaN'
        collect = 'NaN'
        good = 'NaN'
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
    if len(soup.select('.u-overflowHidden a')) > 0:
        author = soup.select('.u-overflowHidden a')[0].text
    else:
        author = "NaN"
    if len(soup.select('.authorInfo-item i')) > 0:
        total_article = soup.select('.authorInfo-item i')[0].text
    else:
        total_article = 'NaN'
    comment = soup.select('.comment-content p')
    if comment:
        comments = len(comment)
    else:
        comments = 0
    return {
        'title': title,
        'time': post_time,
        'watch': watch,
        'collect': collect,
        'good': good,
        'article': article,
        'tag': tag_list,
        'author': author,
        'total_article': total_article,
        'comments': comments
    }


def write_to_file(dic):
    with open('article.json', 'a', encoding='utf-8') as f:
        f.write(json.dumps(dic, ensure_ascii=False) + '\n')
        f.close()


def main(offset):
    html = get_index_page(offset)
    for url in parse_index_page(html):
        html = get_detail_page(url)
        dic = parse_detail_page(html)
        print('正在写入' + dic['author'] + '的文章')
        write_to_file(dic)


if __name__ == '__main__':
    if os.path.exists('article.json'):
        os.remove('article.json')
    pool = Pool()
    pool.map(main, [i * 10 for i in range(701)])
    pool.close()
    pool.join()
