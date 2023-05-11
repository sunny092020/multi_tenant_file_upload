#!/bin/bash

set -e

docker-compose -f docker-compose.yml run --rm mtfu_backend ./scripts/migrate.sh
