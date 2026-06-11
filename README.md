# 微信公众号机器人

对接MiMo Code的微信公众号机器人。

## 功能

- 自然语言对话
- 任务管理（记录、查看、完成）
- JARVIS风格对话

## 快速开始

### 1. 注册微信公众号

访问 https://mp.weixin.qq.com 注册公众号（个人就行）

### 2. 获取配置信息

在公众号后台：
- 开发 → 基本配置 → 获取AppID和AppSecret
- 设置 → 开发 → 基本配置 → 设置Token

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 设置环境变量

```bash
# Windows PowerShell
$env:WECHAT_TOKEN="你的token"
$env:WECHAT_APPID="你的AppID"
$env:WECHAT_APPSECRET="你的AppSecret"
$env:MIMO_API_KEY="你的MiMo API Key"

# Linux/Mac
export WECHAT_TOKEN="你的token"
export WECHAT_APPID="你的AppID"
export WECHAT_APPSECRET="你的AppSecret"
export MIMO_API_KEY="你的MiMo API Key"
```

### 5. 运行

```bash
python app.py
```

### 6. 配置公众号

在公众号后台：
- 开发 → 基本配置 → 服务器配置
- URL: http://你的域名/wechat
- Token: 你设置的token
- EncodingAESKey: 随机生成
- 消息加解密方式: 明文模式

## 本地测试

使用ngrok暴露本地服务：

```bash
# 安装ngrok
# https://ngrok.com/download

# 启动ngrok
ngrok http 8080

# 获取公网URL，如：https://xxxx.ngrok.io
# 配置到公众号后台
```

## 对话示例

```
用户：我叫小明
JARVIS：记住了，小明。

用户：我要写代码
JARVIS：记下了。写代码。

用户：今天有什么任务
JARVIS：今日任务：
○ 写代码

用户：完成写代码
JARVIS：搞定。写代码 ✓
```
