import nonebot
from pathlib import Path

from nonebot import init, on_message
from nonebot.adapters.feishu import Adapter as FeishuAdapter, Bot as FeishuBot
from nonebot import get_driver

# 初始化NoneBot
init()
driver = get_driver()
# 注册适配器
driver.register_adapter(FeishuAdapter)

@driver.on_bot_connect
async def handle_connect(bot: FeishuBot):
    print(f"✅ 真实连接建立 Bot ID: {bot.self_id}")
    print(f"连接协议: {bot.adapter.config.feishu_connection_type}")
    # 测试API调用验证连接有效性
    try:
        me = await bot.get_me()
        print(f"机器人信息: {me}")
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")


async def check_connection():
    bot = nonebot.get_bot()
    if hasattr(bot, "connected") and bot.connected:
        print("✅ 连接状态: 活跃")
    else:
        print("未知状态")

if __name__ == "__main__":
    # 加载插件
    nonebot.load_plugin(Path("./src/plugins/svn_search.py"))
    nonebot.run()