#!/bin/sh

rm data/server.db -f
sqlite3 data/server.db < server.sql

rm data/client.db -f
