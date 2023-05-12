#!/bin/bash
black . --line-length 95
pycodestyle --max-line-length=95 .
flake8 --max-line-length=95 .
