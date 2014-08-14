import os.path
import re


BASE_LINK_PATH = '/wiki/'

DUMP_BASE_PATH = '../labster-wiki-dump'
DUMP_MARKDOWN_PATH = os.path.join(DUMP_BASE_PATH, 'markdown')


def fix_wiki_links():
    for each in fetch_wiki_files():
        path = os.path.join(DUMP_MARKDOWN_PATH, each)
        fix_wiki_link(path)


def fix_wiki_link(path):
    with open(path, 'r+') as f:
        content = f.read()

        re_add_prefix = re.compile(r'\]\(([^\s])', re.MULTILINE | re.DOTALL)
        content = re_add_prefix.sub('](/wiki/\\1'.format(BASE_LINK_PATH), content)

        content = content.replace('/wiki/http', 'http')
        content = content.replace('/wiki/ftp', 'ftp')

        re_link = re.compile(r'[^\!]\[[^\]]+\]\([^\)]+\)', re.MULTILINE | re.DOTALL)
        found = re_link.findall(content)
        for each in found:

            front, back = each.split('](')
            if back.startswith('http'):
                continue
            if back.startswith('ftp'):
                continue

            slug, text, temp_0 = back.split('"')
            temp_1, prefix, slug = slug.split('/')

            slug = slug.strip().replace(' ', '_')
            fixed = "{}/{}/{}".format(temp_1, prefix, slug)
            fixed = '{} "{}"{}'.format(fixed, text, temp_0)
            fixed = "{}]({}".format(front, fixed)

            content = content.replace(each, fixed)

        f.seek(0)
        f.write(content)
        f.truncate()


def fetch_wiki_files():
    for root, dirs, files in os.walk(DUMP_MARKDOWN_PATH):
        counter = 0
        for each in files:
            # if counter > 5:
            #     break

            if not each.endswith('.md'):
                continue

            yield each
            counter += 1


if __name__ == "__main__":
    fix_wiki_links()
