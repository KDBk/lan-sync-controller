#!/bin/bash

serf agent -log-level debug -node=$1 -bind=$2 -event-handler $3 2>&1 > /tmp/serf.log &
sleep 10s
