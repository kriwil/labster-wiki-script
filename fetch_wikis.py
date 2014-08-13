#! /bin/env python

import os
import os.path
import shelve
import time

from lxml import etree
from requests_futures.sessions import FuturesSession
import requests


ALL_FILE = 'all.txt'

ALL_IMAGES_URL = 'http://learn.labster.com/index.php?limit=1000&ilsearch=&user=&title=Special%3AListFiles'
BASE_DETAIL_URL = 'http://learn.labster.com{}'
BASE_EDIT_URL = 'http://learn.labster.com/index.php?title={}&action=edit'
BASE_IMAGE_URL = 'http://learn.labster.com{}'
BASE_XML_URL = 'http://learn.labster.com/index.php/Special:Export/{}'

DUMP_BASE_PATH = '../labster-wiki-dump'
DUMP_IMAGES_PATH = os.path.join(DUMP_BASE_PATH, 'images')
DUMP_HTML_PATH = os.path.join(DUMP_BASE_PATH, 'html')

WIKI_DB_FILE = os.path.join(DUMP_BASE_PATH, 'wiki_data.shelve')
WIKI_IMAGES_FILE = os.path.join(DUMP_BASE_PATH, 'wiki_images.shelve')

BANNED_SLUGS = []


session = FuturesSession()


def fetch_wiki_urls():
    banned_slugs = fetch_banned_slugs()
    tree = etree.parse(ALL_FILE)
    for element in tree.iter():
        if element.tag != 'a':
            continue

        href = element.attrib.get('href')
        slug = href.split('/')[2]

        if slug in banned_slugs:
            continue

        yield href, slug


def fetch_wikis():
    if not os.path.exists(DUMP_HTML_PATH):
        os.mkdir(DUMP_HTML_PATH)

    db = shelve.open(WIKI_DB_FILE)
    wiki_urls = fetch_wiki_urls()

    for index, urls in enumerate(wiki_urls, start=1):
        href, slug = urls

        _start = time.time()
        print("{}: {}".format(index, slug))

        detail_url = BASE_DETAIL_URL.format(href)
        xml_url = BASE_XML_URL.format(slug)

        detail_instance = session.get(detail_url)
        xml_instance = session.get(xml_url)

        future = {
            'db': db,
            'index': index,
            'slug': slug,
            'detail_instance': detail_instance,
            'xml_instance': xml_instance,
        }

        process_requests(**future)

        _end = time.time()
        print("... {}".format(_end - _start))

    db.close()


def process_requests(db, index, slug, detail_instance, xml_instance):

    detail_response = detail_instance.result()
    html_content, title = parse_wiki_html(detail_response.content)

    xml_response = xml_instance.result()
    xml_content = parse_wiki_xml(xml_response.content)

    db[slug] = {
        'title': title,
        'html': html_content,
        'mediawiki': xml_content,
    }

    store_wiki_html(html_content, slug, index)


def parse_wiki_html(content):
    html = title = ''

    tree = etree.fromstring(content)
    for element in tree.iter():
        if element.tag == 'div' and element.attrib.get('id') == 'firstHeading':
            title = element.text
        if element.tag == 'div' and element.attrib.get('class') == 'mw-content-ltr':
            html = etree.tostring(element)

    return html, title


def store_wiki_html(content, slug, prefix=''):
    if prefix:
        prefix = str(prefix).zfill(4)

    slug = "{}_{}".format(prefix, slug)
    path = '{}.html'.format(slug)
    path = os.path.join(DUMP_HTML_PATH, path)

    header = "<html><head></head><body>"
    footer = "</body></html>"

    with open(path, 'w') as f:
        f.write(header)
        f.write(content)
        f.write(footer)

    return path


def parse_wiki_xml(content):
    parser = etree.XMLParser(ns_clean=True)
    tree = etree.fromstring(content, parser=parser)
    ns = '{http://www.mediawiki.org/xml/export-0.5/}'
    page = tree.find('{}page'.format(ns))
    revision = page.find('{}revision'.format(ns))
    text = revision.find('{}text'.format(ns))
    if text.text:
        return text.text

    return ''


def fetch_images():
    if not os.path.exists(DUMP_IMAGES_PATH):
        os.mkdir(DUMP_IMAGES_PATH)

    resp = requests.get(ALL_IMAGES_URL)
    tree = etree.fromstring(resp.content)

    db = shelve.open(WIKI_IMAGES_FILE)

    index = 1
    for element in tree.iter():

        if element.tag != 'table':
            continue
        if element.attrib.get('class') != 'listfiles TablePager':
            continue

        tbody = element.find('tbody')
        for tr in tbody.findall('tr'):
            _start = time.time()

            description = ''
            title = ''
            image_link = ''
            file_name = ''

            for td in tr.findall('td'):
                css_class = td.attrib.get('class')
                if css_class == 'TablePager_col_img_name':
                    els = td.findall('a')
                    for each in els:
                        if each.text == 'file':
                            image_link = each.attrib.get('href')
                            file_name = image_link.split('/')[-1]
                        else:
                            title = each.text.encode('utf-8')

                elif css_class == 'TablePager_col_img_description':
                    text_list = [text.encode('utf-8') for text in td.itertext()]
                    description = ''.join(text_list)

            image_url = BASE_IMAGE_URL.format(image_link)
            print("{}: {}".format(index, title)),
            db[title] = {
                'file_name': file_name,
                'title': title,
                'image_url': image_url,
                'description': description,
            }

            download_image(image_url, file_name)
            _end = time.time()
            print("... {}").format(_end - _start)
            index = index + 1

    db.close()


def download_image(url, file_name):
    resp = requests.get(url, stream=True)
    path = '{}'.format(file_name)
    path = os.path.join(DUMP_IMAGES_PATH, path)

    if resp.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)


def fetch_banned_slugs():
    banned_slugs = []
    with open('banned.txt', 'r') as f:
        banned_slugs = f.readlines()

    return [each.strip() for each in banned_slugs]


if __name__ == '__main__':
    _start = time.time()
    fetch_wikis()
    fetch_images()
    _end = time.time()
    print "total: {}".format(_end - _start)
