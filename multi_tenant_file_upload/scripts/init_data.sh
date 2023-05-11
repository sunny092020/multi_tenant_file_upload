#!/bin/bash

reset

docker-compose -f docker-compose.yml run --rm mtfu_backend ./scripts/init_data.sh
