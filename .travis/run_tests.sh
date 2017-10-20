#!/usr/bin/env bash

if [ -z ${NOCONTAINER+x} ]; then
    tox
else
    tox -- --no-container
fi
