#!/usr/bin/env bash
# #!/bin/sh

# Sanity
echo 'HELLO'
docker -h

## Get container ID
#CONTAINER_ID="$(docker-compose ps -q genesippr)"
#
## Send command to container with name genesipprv2
##docker exec genesipprv2 python3 geneSipprV2/sipprverse/method.py -s /sequences -t /targets /sequences
#
#docker exec genesipprv2 "$CONTAINER_ID" python3 geneSipprV2/sipprverse/method.py -h
