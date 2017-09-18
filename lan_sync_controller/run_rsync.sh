#!/bin/bash

rsync -avz --progress -e "ssh -o StrictHostKeyChecking=no -i $1" $2@$3:$4 $5