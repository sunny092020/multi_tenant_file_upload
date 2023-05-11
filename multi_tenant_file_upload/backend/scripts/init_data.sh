#!/bin/bash

set -e;
python3 manage.py shell < ./scripts/init_data.py
