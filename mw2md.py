#!/bin/evn python

import envoy
import os
import os.path

DUMP_BASE_PATH = '../labster-wiki-dump'
DUMP_MEDIAWIKI_PATH = os.path.join(DUMP_BASE_PATH, 'mediawiki')
DUMP_MARKDOWN_PATH = os.path.join(DUMP_BASE_PATH, 'markdown')


def mw2md(path, slug, index):
    proc = envoy.run("pandoc -f mediawiki -t markdown {}".format(path))
    store_wiki_markdown(proc.std_out, slug, index)


def store_wiki_markdown(content, slug, prefix=''):
    if prefix:
        prefix = str(prefix).zfill(4)

    slug = "{}_{}".format(prefix, slug)
    path = '{}.md'.format(slug)
    path = os.path.join(DUMP_MARKDOWN_PATH, path)

    with open(path, 'wb') as f:
        f.write(content.decode('utf-8').encode('utf-8'))

    return path


def main():
    if not os.path.exists(DUMP_MARKDOWN_PATH):
        os.mkdir(DUMP_MARKDOWN_PATH)

    for root, dirs, files in os.walk(DUMP_MEDIAWIKI_PATH):
        for each in files:
            if not each.endswith('mediawiki'):
                continue

            index, slug = each.split('_', 1)
            slug, _ = slug.split('.')

            path = os.path.join(DUMP_MEDIAWIKI_PATH, each)
            mw2md(path, slug, int(index))


if __name__ == '__main__':
    main()
