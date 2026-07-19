# -*- coding: utf-8 -*-
"""独立 CLI 入口:定时任务调用,零常驻(不在 Flask 进程内开线程)。

用法(cwd=backend):
    python cli.py remind                       # 扫描逾期/临期/待审核,全部
    python cli.py remind --type overdue        # 仅逾期
    python cli.py remind --type due_soon       # 仅临期
    python cli.py remind --type pending_review # 仅待审核
    python cli.py remind --dry-run             # 只统计,不写入

部署:由 systemd timer / cron 每 2 小时调用一次。详见 DEVELOPMENT.md。
"""
import sys
import os
import json
import argparse

# 确保 cwd=backend 时能 import 同级模块(也兼容被外部调用)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(prog='cli.py', description='资环创实平台 CLI')
    sub = parser.add_subparsers(dest='cmd', required=True)

    rp = sub.add_parser('remind', help='扫描逾期/临期/待审核任务,推送站内提醒')
    rp.add_argument('--type', choices=['overdue', 'due_soon', 'pending_review'],
                    default=None, help='只跑某一类(默认全部)')
    rp.add_argument('--dry-run', action='store_true', help='只统计,不写入 notifications.json')

    args = parser.parse_args()

    if args.cmd == 'remind':
        # 延迟导入,避免 argparse --help 时也加载 Flask 相关模块
        from notify import scan_and_remind
        from datetime import datetime
        stats = scan_and_remind(now=datetime.now(), only_type=args.type, dry_run=args.dry_run)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0 if stats.get('sent', 0) >= 0 else 1

    return 0


if __name__ == '__main__':
    sys.exit(main())