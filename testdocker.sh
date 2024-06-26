#!/usr/bin/env bash

docker run -it --entrypoint bash --mount type=bind,src=$(pwd -P),dst=/wkdir pennlinc/xcp_d:0.7.4

