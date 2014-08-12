#! /bin/env python

from lxml import etree
import os.path
import requests

ALL_FILE = 'all.txt'
BASE_EDIT_URL = 'http://learn.labster.com/index.php?title={}&action=edit'


def get_titles():
    tree = etree.parse(ALL_FILE)
    for element in tree.iter():
        if element.tag == 'a':
            href = element.attrib.get('href')
            title = href.split('/')[2]
            url = BASE_EDIT_URL.format(title)

            print "fetching {} ...".format(title)
            content = get_wiki_content(url).encode('utf-8')
            file_path = 'data/{}.txt'.format(title)
            print os.path.isfile(file_path)
            with open(file_path, 'w+') as f:
                f.write(content)


def get_wiki_content(url):
    resp = requests.get(url)

    tree = etree.fromstring(resp.content)
    for element in tree.iter():
        if element.tag == 'textarea':
            if element.attrib.get('id') == 'wpTextbox1':
                return element.text
    return ''


get_titles()
