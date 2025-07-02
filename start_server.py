#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器启动脚本
配置uvicorn忽略日志文件的监控
"""

import uvicorn
from config import config

if __name__ == "__main__":
    # 配置uvicorn，忽略logs目录
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        reload_excludes=[
            "logs/*",
            "*.log",
            "__pycache__/*",
            ".git/*",
            "*.pyc"
        ],
        log_level="info" if not config.DEBUG else "debug"
    )