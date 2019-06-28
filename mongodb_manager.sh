#!/usr/bin/env bash

BLACK=`tput setaf 0`
RED=`tput setaf 1`
GREEN=`tput setaf 2`
YELLOW=`tput setaf 3`
BLUE=`tput setaf 4`
MAGENTA=`tput setaf 5`
CYAN=`tput setaf 6`
WHITE=`tput setaf 7`
BOLD=`tput bold`
RESET=`tput sgr0`

BACKUP_DIR="/mnt/NAS_BACKUP/mongodb"

if [ ! -d $BACKUP_DIR ]; then
    mkdir -p -v $BACKUP_DIR
fi

# https://docs.mongodb.com/manual/tutorial/backup-and-restore-tools/
/usr/bin/mongodump --host localhost --port 27017 --out "$BACKUP_DIR/`date +"%Y-%m-%d"`" --db autopial-cardb --gzip -vv -oplog


