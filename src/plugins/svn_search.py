import httpx
import pandas as pd
from datetime import datetime
from nonebot import on_command, on_message
from typing import Dict, List, Optional
from nonebot.adapters.feishu import (
    Bot as FeishuBot,
    MessageEvent,
    Message,
    MessageSegment,
)
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from pathlib import Path
import tempfile
import subprocess

from config import Config

__plugin_meta__ = PluginMetadata(
    name="SVN表格搜索",
    description="从SVN获取表格并搜索返回结果",
    usage="发送任意文本，机器人会在SVN表格中搜索并返回结果",
    config=Config,
)

config = Config()

# 创建消息处理器
svn_search = on_message(priority=10, block=True)

# 缓存SVN文件（避免重复下载）
svn_cache: Dict[str, Path] = {}
CACHE_EXPIRE_MINUTES = 30  # 缓存30分钟


async def download_svn_file(svn_url: str, username: str, password: str) -> Path:
    """从SVN下载文件到临时位置"""

    """从SVN下载文件到临时位置（带缓存）"""
    cache_key = f"{svn_url}_{username}"

    # 检查缓存是否有效
    if cache_key in svn_cache and svn_cache[cache_key].exists():
        file_mtime = datetime.fromtimestamp(svn_cache[cache_key].stat().st_mtime)
        if (datetime.now() - file_mtime).total_seconds() < CACHE_EXPIRE_MINUTES * 60:
            return svn_cache[cache_key]


    temp_dir = tempfile.mkdtemp()
    file_path = Path(temp_dir) / "HeroCostume.csv"
    print(file_path)
    # 使用svn命令导出文件（确保系统已安装svn命令行工具）
    try:
        cmd = f'svn export --username {username} --password {password} "{svn_url}" "{file_path}" --force'
        subprocess.run(cmd, shell=True, check=True)
        print(f"SVN 文件下载成功: {file_path}")
        svn_cache[cache_key] = file_path
        return file_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"SVN文件下载失败: {e}")


async def search_in_excel(file_path: Path, search_text: str, search_column: str, return_columns: List[str], max_results: int = 5) -> List[Dict[str, str]]:
    """在Excel文件中搜索文本并返回匹配的行数据"""
    # 读取Excel文件
    df = pd.read_excel(file_path)
    # 支持多关键词搜索（空格分隔）
    keywords = search_text.split()
    # 搜索指定列
    # 模糊匹配所有关键词
    mask = df[search_column].astype(str).str.lower().str.contains(
        '|'.join(keywords),
        case=False,
        regex=True
    )
    results = df[mask][return_columns].head(max_results)

    return results.to_dict('records')

def build_feishu_card(search_text: str, results: List[Dict[str, str]]) -> Dict:
    """构建飞书卡片消息（支持表格展示）"""
    if not results:
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "⚠️ 未找到结果"},
                "template": "red"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"未找到包含 `{search_text}` 的记录，请尝试其他关键词。"
                    }
                }
            ]
        }

    # 表格布局
    columns = list(results[0].keys())
    rows = [[str(item[col]) for col in columns] for item in results]

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "🔍 搜索结果"},
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**搜索词**: `{search_text}`\n**共找到 {len(results)} 条记录**"
                }
            },
            {
                "tag": "hr"
            },
            {
                "tag": "table",
                "width": "auto",
                "columns": [
                    {"text": col, "width": "auto"} for col in columns
                ],
                "rows": [
                    {"cells": [{"text": cell} for cell in row]} for row in rows
                ]
            }
        ]
    }


@svn_search.handle()
async def handle_svn_search(bot: FeishuBot, event: MessageEvent):
    # 获取用户发送的文本
    print(f"收到消息: {event.get_message()}")
    print(f"!!! 收到原始事件数据: {event.dict()}")  # 打印完整事件结构
    print(f"消息类型: {event.message_type}, 内容: {event.get_plaintext()}")
    # 先发送普通文本测试
    await bot.send(event, "正在搜索，请稍候...")
    search_text = event.get_plaintext().strip()
    print(search_text)
    if not search_text:
        await svn_search.finish("请输入搜索内容（例如：`英雄皮肤名称`）")

    try:
        # 1. 从SVN下载文件
        file_path = await download_svn_file(
            config.svn_url,
            config.svn_username,
            config.svn_password
        )

        # 2. 在表格中搜索
        result = await search_in_excel(
            file_path,
            search_text,
            config.search_column,
            config.return_columns
        )

        # 3. 发送飞书卡片
        card = build_feishu_card(search_text, result)
        await bot.send(event, MessageSegment.card(card))

    except Exception as e:
        error_card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "❌ 错误"},
                "template": "red"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"搜索失败：\n```\n{str(e)}\n```\n请联系管理员检查SVN配置。"
                    }
                }
            ]
        }
        await bot.send(event, MessageSegment.card(error_card))