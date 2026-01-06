#!/bin/bash

cd /github/workspace || exit 1
pwd
ls -la
python3 /autodoc.py
