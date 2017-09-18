#!/bin/bash

rsync -avz --progress -e "ssh -i $1" $2@$3:$4 $5