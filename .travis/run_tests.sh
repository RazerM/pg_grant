#!/usr/bin/env bash

if [ -z ${TOXENV+x} ]; then
    tox
else
    tox --no-container
fi
