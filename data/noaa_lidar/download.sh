#!/bin/bash
mkdir dist
cd dist
cat ../url_list.txt | xargs wget



