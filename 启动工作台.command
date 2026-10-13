#!/bin/bash
# 优康宝贝 · 母婴数据工作台 启动器
# 双击本文件即可用 Chrome 打开工作台（绕开 html 被豆包/千问劫持的问题）

DIR="$(cd "$(dirname "$0")" && pwd)"
HTML="$DIR/youkang-mom-workbench.html"

if [ -d "/Applications/Google Chrome.app" ]; then
    open -a "Google Chrome" "$HTML"
elif [ -d "/Applications/Safari.app" ]; then
    open -a "Safari" "$HTML"
else
    open "$HTML"
fi
