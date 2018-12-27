#!/bin/bash

for ipynb in $(ls ./examples/*.ipynb)
do
  jupyter nbconvert --execute $ipynb
done