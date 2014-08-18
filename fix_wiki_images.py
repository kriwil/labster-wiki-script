import os.path
import re
import shelve

from fix_wiki_links import fetch_wiki_files


BASE_LINK_PATH = '/wiki/'

DUMP_BASE_PATH = '../labster-wiki-dump'
DUMP_MARKDOWN_PATH = os.path.join(DUMP_BASE_PATH, 'markdown')
WIKI_IMAGES_FILE = os.path.join(DUMP_BASE_PATH, 'wiki_images.shelve')

IMAGE_PREFIX = 'https://s3-us-west-2.amazonaws.com/labster/wiki/media/'


def fix_wiki_images():
    for each in fetch_wiki_files():
        path = os.path.join(DUMP_MARKDOWN_PATH, each)
        # fix_wiki_image(path)
        fix_image_slug(path)


def fix_wiki_image(path):
    with open(path, 'r+') as f:
        content = f.read()

        re_str = r'\]\(\s*(.+)(jpg|jpeg|gif|png)'
        re_compile = re.compile(re_str, re.IGNORECASE)
        content = re_compile.sub(']({}\\1\\2'.format(IMAGE_PREFIX), content)

        content = content.replace('wiki/media//wiki', 'wiki/media')

        f.seek(0)
        f.write(content)
        f.truncate()


def fix_image_slug(path):
    with open(path, 'r+') as f:
        content = f.read()

        db = shelve.open(WIKI_IMAGES_FILE)

        compiled = re.compile("(https:\/\/s3-us-west-2.amazonaws.com\/labster\/wiki\/media\/[^\.]+\.[^\s]+)", re.IGNORECASE)
        found = compiled.findall(content)
        for each in found:
            file_name = each.split('/')[-1]
            if file_name.endswith(')'):
                file_name = file_name.replace(')', '')

            file_name = file_name.replace('FIle:_', '')
            file_name = file_name.strip()

            try:
                data = db[file_name]
            except KeyError:
                continue

            old_name = each
            new_name = "{}{}".format(IMAGE_PREFIX, data['file_name'])
            content = content.replace(old_name, new_name)

            f.seek(0)
            f.write(content)
            f.truncate()

        db.close()


if __name__ == "__main__":
    fix_wiki_images()
