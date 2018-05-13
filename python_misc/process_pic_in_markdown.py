#!/usr/bin/env python3
""" This script process pictures in markdown files
1.  replace the absolute path of pictures to img url
    "<img alt="education_montessori__slide__ages_of_children__small.jpg" src="{{site.url}}/public/images/life_food_growup/education_montessori__slide__ages_of_children__small.jpg" width="100%" align="center" style="margin: 0px 15px">"
2.  check the accessiable of picture of such url
"""

import glob
import magic
import os
import re
import sys

def convert_abs_path_to_url(markdown, basedir):
    """convert absolute path of pictures in markdown to markdown supportable
    img url.

    Args:
        param1 (str): The name of destination markdown file
        param2 (str): The base directory of images. This varible is needed to
        get the correct url of images
    """

    if not re.match('^/.*/$', basedir):
        basedir += '/'

    print(basedir)
    picture_pattern = re.compile('^<' + basedir + '(.*((jpg)|(jpeg)|(png)|(gif)|(mp4)))>$')
    file_extension_pattern = re.compile('\.[^.]*$')
    split_pattern = re.compile('_')
    file_new = markdown + ".new"
    with open(markdown, 'r') as f:
        with open(file_new, 'w') as fout:
            for line in f:
                new_line = picture_pattern.sub(r'<img alt="\1" src="{{site.url}}/\1" width="100%" align="center" style="margin: 0px 15px">', line)
                fout.write(new_line)
    print("DONE: output to " + file_new)

def check_accessiable_of_pic(markdown, basedir):
    """check accessiable of pictures in markdown

    Args:
        param1 (str): The name of destination markdown file
        param2 (str): The base directory of images. This varible is needed to
        get the correct url of images
    """

def main():
    if len(sys.argv) < 2:
        print("Usage: " + sys.argv[0] + " _posts/2018/2018-02-23-how-to-transfer-file-through-putty.md")
        raise Exception("missing markdown")

    markdown = sys.argv[1]
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

    print("markdown: " + markdown)
    print("WARNING: fix basedir in non-os x system!")
    basedir = "/Users/bamvor/works/source/bjzhang.github.io"
    convert_abs_path_to_url(markdown, basedir)
    check_accessiable_of_pic(markdown, basedir)

if __name__ == "__main__":
    main()

