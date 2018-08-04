#!/bin/bash

function abort {
        echo "Abort from $0."
}

set -e
trap abort ERR

path=~/works/source/miscs
mkdir -p $path
cd $path
git clone https://github.com/bjzhang/small_tools_collection.git
