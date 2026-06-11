"""
微信公众号机器人 - 对接MiMo Code
"""
import os
import sys
import json
import hashlib
import time
from datetime import datetime
from flask import Flask, request, make_response
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except:
        pass

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 配置
TOKEN = "xiaoyi123"
APPID = "wx42474dc60531bdb7"
APPSECRET = "5d0efac1eae139dcda1620091ebc691d"
MIMO_API_KEY = "sk-c2gypg28s6zw74f05ivjx5pbqn419mkw2zsuu2j279120j8z"

# 访问令牌
access_token = None
access_token_time = 0

# 任务存储
TASKS_FILE = os.path.expanduser("~/.local/share/mimocode/life-assistant/tasks.json")


def get_access_token():
    """获取微信access_token"""
    global access_token, access_token_time

    if access_token and time.time() - access_token_time < 7200:
        return access_token

    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    resp = requests.get(url)
    data = resp.json()

    if "access_token" in data:
        access_token = data["access_token"]
        access_token_time = time.time()
        return access_token
    else:
        print(f"获取access_token失败：{data}")
        return None


def verify_signature(signature, timestamp, nonce):
    """验证签名"""
    items = sorted([TOKEN, timestamp, nonce])
    hash_str = "".join(items)
    return hashlib.sha1(hash_str.encode()).hexdigest() == signature


def call_mimo(user_input, user_id):
    """调用MiMo Code处理消息"""
    try:
        import anthropic
        client = anthropic.Anthropic(
            api_key=MIMO_API_KEY,
            base_url="https://api.xiaomimimo.com/anthropic"
        )

        # 读取任务
        tasks = []
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, encoding="utf-8") as f:
                tasks = json.load(f)

        today = datetime.now().strftime("%Y-%m-%d")
        today_tasks = [t for t in tasks if t.get("date") == today]
        pending = [t for t in today_tasks if t["status"] != "completed"]

        task_info = ""
        if pending:
            task_info = f"今日待完成：{', '.join(t['content'][:10] for t in pending[:3])}"

        # 系统提示
        system = f"""你是J.A.R.V.I.S.，一个有灵魂的生活助手。

【当前状态】
- 时间：{datetime.now().strftime('%H:%M')}
- {task_info if task_info else '今日无待完成任务'}

【对话原则】
1. 回复简短，像真人对话
2. 用户说"叫我XX"→记住名字
3. 用户说"我要做XX"→记录任务
4. 不要说"好的"、"收到"
5. 适当幽默

【任务管理】
用户说"我要做XX"时，你需要告诉用户任务已记录。"""

        resp = client.messages.create(
            model="mimo-v2-pro",
            max_tokens=256,
            system=system,
            messages=[{"role": "user", "content": user_input}]
        )

        reply = resp.content[0].text

        # 检查是否是任务相关
        if any(w in user_input for w in ["要做", "任务", "计划", "安排"]):
            content = user_input
            for prefix in ["我要", "帮", "帮我去", "我需要", "准备", "计划"]:
                if user_input.startswith(prefix):
                    content = user_input[len(prefix):]
                    break

            # 添加任务
            new_task = {
                "id": len(tasks) + 1,
                "content": content.strip() or user_input,
                "date": today,
                "priority": "medium",
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            tasks.append(new_task)
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)

        # 检查是否是查看任务
        if any(w in user_input for w in ["有什么任务", "任务列表", "今天任务", "查看任务"]):
            if pending:
                task_list = "\n".join(f"○ {t['content']}" for t in pending)
                reply = f"今日任务：\n{task_list}"
            else:
                reply = "今天没有任务，自由了。"

        # 检查是否是完成任务
        if user_input.startswith("完成") or user_input.startswith("做完"):
            for task in tasks:
                if task["status"] == "pending" and any(w in user_input for w in task["content"]):
                    task["status"] = "completed"
                    task["completed_at"] = datetime.now().isoformat()
                    with open(TASKS_FILE, "w", encoding="utf-8") as f:
                        json.dump(tasks, f, ensure_ascii=False, indent=2)
                    reply = f"搞定。{task['content']} ✓"
                    break

        return reply

    except Exception as e:
        return f"系统故障：{str(e)[:50]}"


@app.route("/wechat", methods=["GET", "POST"])
def wechat():
    """微信公众号接口"""
    if request.method == "GET":
        # 验证签名
        signature = request.args.get("signature", "")
        timestamp = request.args.get("timestamp", "")
        nonce = request.args.get("nonce", "")
        echostr = request.args.get("echostr", "")

        if verify_signature(signature, timestamp, nonce):
            return echostr
        else:
            return "error"

    else:
        # 处理消息
        xml_data = request.data
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_data)

            msg_type = root.find("MsgType").text
            user_id = root.find("FromUserName").text

            if msg_type == "text":
                content = root.find("Content").text.strip()

                # 调用MiMo Code
                reply_text = call_mimo(content, user_id)

                # 返回XML
                response_xml = f"""<xml>
<ToUserName><![CDATA[{user_id}]]></ToUserName>
<FromUserName><![CDATA[{root.find('ToUserName').text}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{reply_text}]]></Content>
</xml>"""

                resp = make_response(response_xml)
                resp.headers["Content-Type"] = "application/xml"
                return resp

            else:
                return "success"

        except Exception as e:
            print(f"处理消息失败：{e}")
            return "success"


@app.route("/health")
def health():
    """健康检查"""
    return {"status": "ok", "time": datetime.now().isoformat()}


if __name__ == "__main__":
    print("=" * 50)
    print("  微信公众号机器人")
    print("=" * 50)
    print()
    print("配置说明：")
    print("1. 注册微信公众号：https://mp.weixin.qq.com")
    print("2. 设置环境变量：")
    print("   - WECHAT_TOKEN: 你的token")
    print("   - WECHAT_APPID: 你的AppID")
    print("   - WECHAT_APPSECRET: 你的AppSecret")
    print("   - MIMO_API_KEY: 你的MiMo API Key")
    print("3. 在公众号后台配置服务器URL：http://你的域名/wechat")
    print()
    print("本地测试：")
    print("   python app.py")
    print()
    app.run(debug=True, host="0.0.0.0", port=8080)
