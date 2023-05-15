#!/bin/bash

reset

# Define API endpoints and user credentials as variables
API_BASE_URL="<API_BASE_URL>"
TOKEN_ENDPOINT="{$API_BASE_URL}/token/"
UPLOAD_ENDPOINT="{$API_BASE_URL}/upload"
FILES_ENDPOINT="{$API_BASE_URL}/files"
LIST_FILES_ENDPOINT="{$API_BASE_URL}/list_files"

USERNAME="john1"
PASSWORD="test"

# Get the JWT token for john1
ACCESS_TOKEN=$(curl --location --request POST $TOKEN_ENDPOINT \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "username": "'"$USERNAME"'",
    "password": "'"$PASSWORD"'"
  }' | jq -r '.access')

# Use the token to upload files on behalf of john1
curl --location --request POST $UPLOAD_ENDPOINT \
  --header 'Authorization: Bearer '"$ACCESS_TOKEN"'' \
  --form 'file=@my_file' \
  --form 'resource=product' \
  --form 'resource_id=1'

curl --location --request POST $UPLOAD_ENDPOINT \
  --header 'Authorization: Bearer '"$ACCESS_TOKEN"'' \
  --form 'file=@my_file' \
  --form 'resource=avatar' \
  --form 'resource_id=1'

# Use the token to retrieve files on behalf of john1
curl --location --request GET $FILES_ENDPOINT/product/1 \
  --header 'Authorization: Bearer '"$ACCESS_TOKEN"''

curl --location --request GET $FILES_ENDPOINT/product/10 \
  --header 'Authorization: Bearer '"$ACCESS_TOKEN"''

curl --location --request GET $FILES_ENDPOINT/product/2 \
  --header 'Authorization: Bearer '"$ACCESS_TOKEN"''

curl --location --request GET $FILES_ENDPOINT/avatar/1 \
  --header 'Authorization: Bearer '"$ACCESS_TOKEN"''

# LIST_FILES_ENDPOINT
curl --location --request GET "$LIST_FILES_ENDPOINT?username=john1&resource=avatar&resource_id=1" \
  --header 'Authorization: Bearer '"$ACCESS_TOKEN"''

# Get the JWT token for john2
USERNAME="john2"
ACCESS_TOKEN=$(curl --location --request POST $TOKEN_ENDPOINT \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "username": "'"$USERNAME"'",
    "password": "'"$PASSWORD"'"
  }' | jq -r '.access')

# Use the token to retrieve files on behalf of john2
curl --location --request GET $FILES_ENDPOINT/product/1 \
  --header 'Authorization: Bearer '"$ACCESS_TOKEN"''
