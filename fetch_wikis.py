#! /bin/env python

from lxml import etree
import requests
import shelve
import time

ALL_FILE = 'all.txt'
BASE_DETAIL_URL = 'http://learn.labster.com{}'
BASE_EDIT_URL = 'http://learn.labster.com/index.php?title={}&action=edit'
WIKI_DB_FILE = 'wiki_data.shelve'
WIKI_HTML_DB_FILE = 'wiki_html.shelve'


def fetch_wikis():
    tree = etree.parse(ALL_FILE)
    db = shelve.open(WIKI_DB_FILE)
    html_db = shelve.open(WIKI_HTML_DB_FILE)

    index = 1
    for element in tree.iter():
        if element.tag != 'a':
            continue

        _start = time.time()

        href = element.attrib.get('href')
        title = href.split('/')[2]
        print("{}: fetching {}".format(index, title)),

        # html
        detail_url = BASE_DETAIL_URL.format(href)
        html_content = get_wiki_html(detail_url)
        html_db[title] = html_content

        # mediawiki
        url = BASE_EDIT_URL.format(title)
        content = get_wiki_content(url).encode('utf-8')
        db[title] = content

        index = index + 1

        _end = time.time()
        print("... {}".format(_end - _start))

    db.close()


def get_wiki_html(url):
    resp = requests.get(url)

    tree = etree.fromstring(resp.content)
    for element in tree.iter():
        if element.tag == 'div':
            if element.attrib.get('id') == 'content':
                for children in element.getchildren():
                    return etree.tostring(children)

    return ''


def get_wiki_content(url):
    resp = requests.get(url)

    tree = etree.fromstring(resp.content)
    for element in tree.iter():
        if element.tag == 'textarea':
            if element.attrib.get('id') == 'wpTextbox1':
                return element.text

    return ''


if __name__ == '__main__':
    _start = time.time()
    fetch_wikis()
    _end = time.time()
    print "total: {}".format(_end - _start)
