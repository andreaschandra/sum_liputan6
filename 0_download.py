#!/usr/bin/env python
# coding: utf-8

import requests
import time
import json, os
import glob
from bs4 import BeautifulSoup
import threading
from tqdm import tqdm


def get_id(url):
    return url.split('/')[-2]

def get_summary(text):
    target = ''
    for line in text.split('\n'):
        if 'window.kmklabs.channel =' in line:
            target = line
            break
    temp=target.split('window.kmklabs.article = ')[1]
    temp=temp.split(';')[0]
    data = json.loads(temp)
    return data['shortDescription']

def extract_data(text):
    soup = BeautifulSoup(text, "lxml")
    try:
        title = soup.findAll('title')[0].getText().replace(' - News Liputan6.com', '')
        date = soup.findAll('time', {'class': 'read-page--header--author__datetime updated'})[0].getText()
        article = []
        contents = soup.findAll('div', {'class': 'article-content-body__item-content'})
        for content in contents:
            article.append(content.getText())
        summary = get_summary(text)
    except:
        return (None, None, None, None)
    
    return title, date, article, summary

def write_file(id, url, title, date, content, summary, target_path):
    json_dict = {}
    json_dict['id']=id
    json_dict['url']=url
    json_dict['title']=title
    json_dict['date']=date
    json_dict['content']='\n'.join(content)
    json_dict['summary']=summary

    with open(f"{target_path}/{id}.json", 'w') as json_file:
        json.dump(json_dict, json_file)

def proceed_one(url, path):
    response = requests.get(url)
    url = response.url
    id = get_id(url)
    title, date, article, summary = extract_data(response.text)
    
    if title is not None:
        write_file(id, url, title, date, article, summary, path)

def proceed(urls, path, bar):
    for url in urls:
        proceed_one(url, path)
        bar.update(n=1)

def thread_func(urls, path, bar, num_thread=1):
    os.makedirs(path,exist_ok=True)
    threads = []
    for i in range(num_thread):
        cur_idx = int(i*len(urls)/num_thread)
        cur_urls = urls[cur_idx:cur_idx+int(len(urls)/num_thread)]
        t = threading.Thread(target=proceed, args=(cur_urls, path, bar))
        threads.append(t)
        t.start()

if __name__ == "__main__":
    
    THREAD = 10
    urls = json.load(open('url.json'))
    
    dev_bar = tqdm(total=len(urls['dev_urls']))
    thread_func(urls['dev_urls'], 'data/raw/dev', dev_bar, THREAD)
    
    test_bar = tqdm(total=len(urls['test_urls']))
    thread_func(urls['test_urls'], 'data/raw/test', test_bar, THREAD)
    
    train_bar = tqdm(total=len(urls['train_urls']))
    thread_func(urls['train_urls'], 'data/raw/train', train_bar, THREAD)
