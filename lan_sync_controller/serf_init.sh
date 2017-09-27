#!/bin/bash

serf agent -log-level debug -node=$1 -bind=$2 -rpc-addr $2:7373 -event-handler $3 2>&1 > /tmp/serf.log &