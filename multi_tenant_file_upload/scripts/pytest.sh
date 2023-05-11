#!/bin/bash

reset

docker-compose run --rm mtfu_backend pytest mtfu/ -s
