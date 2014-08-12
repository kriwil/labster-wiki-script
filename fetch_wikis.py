#! /bin/env python

from lxml import etree
import requests
import shelve
import time

ALL_FILE = 'all.txt'

ALL_IMAGES_URL = 'http://learn.labster.com/index.php?limit=1000&ilsearch=&user=&title=Special%3AListFiles'
BASE_DETAIL_URL = 'http://learn.labster.com{}'
BASE_EDIT_URL = 'http://learn.labster.com/index.php?title={}&action=edit'
BASE_IMAGE_URL = 'http://learn.labster.com{}'
BASE_XML_URL = 'http://learn.labster.com/index.php/Special:Export/{}'

WIKI_DB_FILE = 'wiki_data.shelve'
WIKI_HTML_DB_FILE = 'wiki_html.shelve'
WIKI_IMAGES_FILE = 'wiki_images.shelve'


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
        url = BASE_XML_URL.format(title)
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

    parser = etree.XMLParser(ns_clean=True)
    tree = etree.fromstring(resp.content, parser=parser)
    ns = '{http://www.mediawiki.org/xml/export-0.5/}'
    page = tree.find('{}page'.format(ns))
    revision = page.find('{}revision'.format(ns))
    text = revision.find('{}text'.format(ns))
    if text.text:
        return text.text

    # for element in tree.iter():
    #     if element.tag == 'textarea':
    #         if element.attrib.get('id') == 'wpTextbox1':
    #             return element.text

    return ''


def fetch_images():
    resp = requests.get(ALL_IMAGES_URL)
    tree = etree.fromstring(resp.content)

    db = shelve.open(WIKI_IMAGES_FILE)

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
            print(title),
            db[title] = {
                'file_name': file_name,
                'title': title,
                'image_url': image_url,
                'description': description,
            }

            download_image(image_url, file_name)
            _end = time.time()
            print("... {}").format(_end - _start)

    db.close()


def download_image(url, file_name):
    resp = requests.get(url, stream=True)
    path = 'images/{}'.format(file_name)

    if resp.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)


if __name__ == '__main__':
    _start = time.time()
    fetch_wikis()
    # fetch_images()
    _end = time.time()
    print "total: {}".format(_end - _start)
