#!/usr/bin/env bash

set -e

cd /home/gtytus/analysis/grace/python

source ~/.bashrc 

exec rye run python paddle_occupancy_from_root.py "$@"
