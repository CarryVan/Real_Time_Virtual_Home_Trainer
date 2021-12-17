#!/bin/bash
git pull origin master
PWD=`pwd`
. $PWD/venv/bin/activate
pip install -r requirements.txt