#!/bin/bash

rm -rf ../docs
make html
mv _build/html ../docs
