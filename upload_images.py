#!/bin/evn python

from boto.s3.key import Key
import boto
import os


KEY = 'AKIAJZZQD5RIVBAFWP2Q'
SECRET = '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'

DUMP_BASE_PATH = '../labster-wiki-dump'
DUMP_IMAGES_PATH = os.path.join(DUMP_BASE_PATH, 'images')
PREFIX = 'wiki/media'


def get_images():
    images = []
    for root, dirs, files in os.walk(DUMP_IMAGES_PATH):
        for each in files:
            if each.startswith('.'):
                continue

            path = os.path.join(DUMP_IMAGES_PATH, each)
            images.append(path)

    return images


def get_image_name(path):
    file_name = os.path.basename(path)
    index, image_name = file_name.split('_', 1)
    return image_name


def upload_images():
    conn = boto.connect_s3(KEY, SECRET)
    bucket = conn.get_bucket('labster')

    images = get_images()
    for index, each in enumerate(images, start=1):
        image_name = get_image_name(each)
        key = "{}/{}".format(PREFIX, image_name)

        print("{}: {}").format(index, key)

        key_obj = Key(bucket)
        key_obj.key = key
        key_obj.set_contents_from_filename(each)


if __name__ == '__main__':
    upload_images()
