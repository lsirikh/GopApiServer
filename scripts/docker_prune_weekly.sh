#!/bin/bash
# Docker builder cache 주 1회 정리 — v6.0 후속 (A-7 관련)
# crontab -e:
#   0 3 * * 0 /path/to/scripts/docker_prune_weekly.sh > /var/log/docker_prune.log 2>&1

set -e
echo "[$(date -Iseconds)] Docker prune start"

# Builder cache 회수 (이미지/컨테이너 유지)
docker builder prune -af

# Dangling volumes (in-use 는 유지됨)
docker volume prune -f

# Dangling images
docker image prune -f

echo "[$(date -Iseconds)] Docker prune complete"
docker system df
