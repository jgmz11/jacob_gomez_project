#!/bin/bash
conda env create --name project_env --file covid_env.yml
source activate covid_env
python ./covid.py