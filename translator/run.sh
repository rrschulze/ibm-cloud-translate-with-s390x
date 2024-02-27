#!/usr/bin/env bash
set -Eeuo pipefail

sudo docker build --tag translate -f translate.dockerfile .
sudo docker build --tag identify -f identify.dockerfile .
sudo docker build --tag app -f app.dockerfile .
sudo docker build --tag client -f client.dockerfile .

sudo docker compose up -d