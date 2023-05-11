#!/bin/bash

reset

docker-compose run --rm mtfu_backend pytest mtfu/tests/test_upload.py -s
