#!/usr/bin/env bash
# 每日备份:打包 /var/www/zhansai/data,保留 14 天
# crontab: 0 3 * * * /var/www/zhansai/deploy/backup.sh >> /var/log/zhansai-backup.log 2>&1
set -euo pipefail

DATA_DIR=/var/www/zhansai/data
BACKUP_DIR=/backup/zhansai
mkdir -p "$BACKUP_DIR"

STAMP=$(date +%Y%m%d_%H%M%S)
OUT="$BACKUP_DIR/data-$STAMP.tar.gz"

tar -czf "$OUT" -C "$DATA_DIR" .
# 清理 14 天前的备份
find "$BACKUP_DIR" -name 'data-*.tar.gz' -mtime +14 -delete

echo "[$STAMP] 备份完成: $OUT ($(du -h "$OUT" | cut -f1))"
