#!/usr/bin/env python3
""" This script insert pictures(globs) to markdown files
What I learn when writing this script:
1.  abspath and relpath in os.path modules
2.  using sub to replace for regular expression: ref: <https://docs.python.org/3/howto/regex.html>
3.  misc
    1.  using quotation mark to protect the glob symbol(*) in command.
    2.  open file in append mode.
    3.  try to follow the [Google Style Python Docstrings](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)

TODO:
1.  get correct basedir on Linux system by using the current directory by
default. User could input basedir in argument.
"""

import glob
import magic
import os
import re
import sys

def remove_duplicated_images(images_glob, markdown):
    """Remove duplicated images in existing markdown file
    Args:
        param1 (str): The image name or the glob of image name.
        param2 (str): The name of destination markdown file
    """
    images =glob.glob(images_glob)
    images.sort(key=os.path.getctime)
    clean_images = []
    with open(markdown, "r") as file:
        file_content = file.read()
        for image in images:
            image_basename = os.path.basename(image)
            print(image_basename)
            result = re.search(image_basename, file_content)
            if result:
                print("duplicated " + image)
            else:
                # call image.remove() here will remote the item and cause
                # the items of list move ahead. If I remove in the current
                # loop, then the for statement will "skip" item after the
                # removed item.
                clean_images.append(image)

    return clean_images

def insert_images_to_markdown(images_array, markdown, basedir):
    """Insert images to markdown file

    Args:
        param1 (str): The array of image name
        param2 (str): The name of destination markdown file
        param3 (str): The base directory of images. This varible is needed to
        get the correct url of images
    """

    file_extension_pattern = re.compile('\.[^.]*$')
    split_pattern = re.compile('_')
    with open(markdown, 'a') as f:
        for image in images_array:
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
    file_extension = re.sub(r'^.+(\.(.+)?)$', r'\2', markdown)
    if file_extension == markdown:
        print("Error: extersion of markdown file<" + markdown + "> is not found")
        return
    else:
        print("file_extension: " + file_extension)
        if file_extension != "md" and file_extension != "markdown":
            print("Error: extersion of markdown file<" + markdown + ": " +
                    file_extension + "> should be md or markdown")
            return

    print("images: " + images)
    print("markdown: " + markdown)
    print("WARNING: fix basedir in non-os x system!")
    basedir = "/Users/bamvor/works/source/bjzhang.github.io"
    new_images = remove_duplicated_images(images, markdown)
    if new_images and len(new_images) != 0:
        insert_images_to_markdown(new_images, markdown, basedir)
    else:
        print("There is no new images")

if __name__ == "__main__":
    main()

