#!/bin/bash
rm -rf ~/.aws/.backup_program/config.json
rm -rf ~/.aws/.backup_program/stat_cache
rm -rf ~/.aws/.backup_program/objects.db
rm -rf ~/.aws/.backup_program/__version__.txt
rm -rf ~/.aws/.backup_program/metadata
python cloudsec.py
