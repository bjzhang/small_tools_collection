#!/bin/bash

git checkout -f HEAD~1
git branch -D linux-next-master
git branch -D kselftest-next
git branch -D hikey-mainline-rebase
git pull 96boards; git pull origin ; git pull linux-next ; git pull linux-stable ; git pull linux-kselftest-shuah; git pull linux-gpio
git branch linux-next-master linux-next/master
git branch kselftest-next linux-kselftest-shuah/next
git branch hikey-mainline-rebase 96boards/hikey-mainline-rebase
git checkout -f master && git merge master origin/master || git checkout -f -b master origin/master

