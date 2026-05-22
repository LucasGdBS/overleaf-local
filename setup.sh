#! /bin/bash

docker compose up -d

sleep 5

docker compose logs -f sharelatex