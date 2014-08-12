#! /bin/env python

from lxml import etree
import requests
import shelve

ALL_FILE = 'all.txt'
BASE_EDIT_URL = 'http://learn.labster.com/index.php?title={}&action=edit'
DB_FILE = 'wiki_data.shelve'


def fetch_wikis():
    tree = etree.parse(ALL_FILE)
    db = shelve.open(DB_FILE)

    index = 1
    for element in tree.iter():
        if element.tag != 'a':
            continue

        href = element.attrib.get('href')
        title = href.split('/')[2]
        url = BASE_EDIT_URL.format(title)

        print "{}: fetching {} ...".format(index, title)
        content = get_wiki_content(url).encode('utf-8')
        db[title] = content

        index = index + 1

    db.close()


def get_wiki_content(url):
    resp = requests.get(url)

    tree = etree.fromstring(resp.content)
    for element in tree.iter():
        if element.tag == 'textarea':
            if element.attrib.get('id') == 'wpTextbox1':
                return element.text
    return ''


if __name__ == '__main__':
    fetch_wikis()
