#!/usr/bin/env python3

#<https://docs.python.org/3/howto/regex.html>

import glob
import magic
import os
import re
import sys

def insert_images_to_markdown(images, markdown, basedir):

    images = glob.glob(images)
    images.sort(key=os.path.getctime)
    file_extension_pattern = re.compile('\.[^.]*$')
    split_pattern = re.compile('_')
    with open(markdown, 'a') as f:
        for image in images:
            image = os.path.abspath(image)
            image_url = "{{site.url}}/" + os.path.relpath(image, start=basedir)
            image_basename = os.path.basename(image)
            image_md = "<img alt=\"" + image_basename + "\" src=\"" + image_url + "\" width=\"100%\" align=\"center\" style=\"margin: 0px 15px\">"
            notes_for_image = file_extension_pattern.sub("", image_basename)
            notes_for_image = split_pattern.sub(" ", notes_for_image)
            print("1. " + notes_for_image, file=f)
            # Add one more empty line after the picture
            print(image_md + "\n", file=f)

def main():
    if len(sys.argv) < 3:
        print("Usage: " + sys.argv[0] + " \"public/images/misc/putty_*\" _posts/2018/2018-02-23-how-to-transfer-file-through-putty.md")
        raise Exception("missing images and or markdown")

    images = sys.argv[1]
    markdown = sys.argv[2]
    print("images: " + images)
    print("markdown: " + markdown)
    print("WARNING: fix basedir in non-os x system!")
    basedir = "/Users/bamvor/works/source/bjzhang.github.io"
    insert_images_to_markdown(images, markdown, basedir)

if __name__ == "__main__":
    main()
