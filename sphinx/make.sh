#!/bin/bash

rm -rf ../docs/*
make html
cp -rf _build/html/* ../docs/
