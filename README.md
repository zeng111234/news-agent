# ? News Agent - 每日国际新闻简报自动化生成工具

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![DeepSeek](https://img.shields.io/badge/?-DeepSeek%20AI-green)](https://deepseek.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

基于 **AI Agent** 的每日国际新闻资讯抓取与智能简报生成系统。自动抓取央视网国际新闻，由 **DeepSeek AI** 进行内容筛选与摘要生成，并通过 **QQ邮箱** 自动推送每日简报，实现信息获取完整闭环。

---

## ? 项目概述

本项目演示了 AI Agent 在实际场景中的落地能力：

| 功能 | 说明 |
|------|------|
| ? 自动化工作流 | 定时抓取 → AI 处理 → 邮件推送，全自动运行 |
| ? AI 智能处理 | DeepSeek 大模型进行内容筛选、去重、摘要生成 |
| ? 邮件推送 | 通过 QQ邮箱 SMTP 发送精美 HTML 简报 |
| ? 自然语言指令 | 支持动态调整抓取源与筛选规则 |

## ?? 技术栈

- **核心语言**: Python 3.10+
- **AI 模型**: DeepSeek API (`deepseek-chat`)
- **网页抓取**: `httpx` + `BeautifulSoup4`
- **邮件服务**: QQ邮箱 SMTP (SSL)
- **任务调度**: GitHub Actions (Cron 定时触发)
- **配置管理**: YAML + `.env` 环境变量

## ? 快速开始

### 环境要求

- Python 3.10 或更高版本
- QQ邮箱（用于发送简报）
- DeepSeek API Key（可选，不配置则使用基础筛选模式）

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/news-agent.git
cd news-agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 DeepSeek API Key 和 QQ邮箱配置
```

### 配置 `.env`

```ini
# DeepSeek API 配置（获取地址: https://platform.deepseek.com/api_keys）
DEEPSEEK_API_KEY=sk-your_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# QQ邮箱 SMTP 配置（需开启 SMTP 服务获取授权码）
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your_email@qq.com
SMTP_PASSWORD=your_authorization_code_here
MAIL_TO=recipient@example.com

# 简报配置
BRIEFING_TIME=08:00
BRIEFING_TIMEZONE=Asia/Shanghai
```

> **? 获取 QQ邮箱授权码**: 登录 QQ邮箱 → 设置 → 账户 → POP3/SMTP 服务 → 开启 → 生成授权码

### 运行

```bash
# 直接运行，生成简报并保存到本地
python main.py

# 交互管理模式（支持动态调整规则）
python main.py i

# 或简写
python main.py interactive
```

### 交互模式示例

```bash
? News Agent - 交互管理模式
输入指令管理抓取源和筛选规则
输入 '运行' 立即执行一次完整简报流程

? > 列出源
? 已启用的抓取源:
  ? 央视国际
     URL: https://news.cctv.com/world

? > 过滤掉 广告
? 已添加排除关键词「广告」

? > 添加源 36氪 https://36kr.com/information
? 已添加抓取源「36氪」

? > 运行
? 开始执行简报生成流程...
```

## ? 项目结构

```
news-agent/
├── main.py                      # 程序入口
├── .env.example                 # 环境变量模板
├── requirements.txt             # Python 依赖
├── README.md                    # 项目文档
├── config/
│   ├── sources.yaml             # 抓取源配置
│   └── rules.yaml               # 筛选规则配置
├── src/
│   ├── config.py                # 配置管理模块
│   ├── scraper.py               # 网页抓取服务
│   ├── ai_processor.py          # DeepSeek AI 处理模块
│   ├── email_sender.py          # QQ邮箱推送服务
│   ├── rule_manager.py          # 规则管理（自然语言指令）
│   └── main.py                  # 主逻辑
├── templates/
│   └── daily_briefing.html      # 邮件模板
├── storage/
│   └── history/                 # 历史简报存档
└── .github/
    └── workflows/
        └── daily-briefing.yml   # GitHub Actions 定时任务
```

## ? 工作流程

```
┌─────────────────────────────────────────────────────┐
│                 Step 1: 定时触发                        │
│   GitHub Actions / 手动运行 → 启动简报生成流程           │
└────────────────────┬────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│                 Step 2: 抓取新闻                        │
│   httpx + BeautifulSoup → 抓取央视网国际新闻列表         │
│   支持多源并发抓取                                      │
└────────────────────┬────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│              Step 3: AI 智能处理                        │
│   DeepSeek API → 内容筛选（去重/排序） → 摘要生成        │
│   未配置 API 时自动降级为关键词基础筛选                   │
└────────────────────┬────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│              Step 4: 简报输出                           │
│   ├─ Markdown 本地存档                                 │
│   ├─ HTML 网页版（精美邮件模板）                         │
│   └─ 邮件推送（QQ邮箱 SMTP）                            │
└─────────────────────────────────────────────────────────┘
```

## ?? GitHub Actions 自动部署

本项目支持通过 **GitHub Actions** 实现完全自动化的每日简报推送。

### 配置步骤

1. 将代码推送到 GitHub 仓库
2. 在仓库 Settings → Secrets and variables → Actions 添加以下 Secrets：

| Secret | 说明 |
|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `SMTP_USER` | QQ邮箱地址 |
| `SMTP_PASSWORD` | QQ邮箱授权码 |
| `MAIL_TO` | 接收简报的邮箱地址 |

3. Actions 会自动在每天 **北京时间 8:00** 执行简报生成与推送

### 手动触发

在 GitHub Actions 页面选择 **Daily Briefing** 工作流 → **Run workflow** → 立即执行。

## ? 特色功能

### 1. 智能降级策略
当 DeepSeek API 不可用时，系统会自动降级为基于关键词的基础筛选模式，确保核心功能正常运行。

### 2. 自然语言管理
支持通过自然语言指令动态调整配置：
- `添加源 名字 https://...` - 增加抓取源
- `过滤掉 关键词` - 排除含关键词的新闻
- `列出源` / `列出规则` - 查看当前配置

### 3. 精美简报模板
邮件采用深蓝色渐变设计的 HTML 模板，适配移动端，支持 Markdown 转 HTML。

### 4. 完整的错误处理
每个步骤都有详细的错误提示，配置不完整时会清晰指出缺失项。

## ? 配置说明

### sources.yaml

```yaml
sources:
  央视国际:
    url: "https://news.cctv.com/world"
    type: cctv
    enabled: true
```

### rules.yaml

```yaml
filter_rules:
  exclude_keywords:
    - "广告"
    - "推广"
  include_keywords: []
priority_keywords: []

briefing:
  max_articles: 10
  include_source_link: true
```

## ? 测试

```bash
# 测试抓取（不发送邮件）
python -c "from src.scraper import scrape_all_sources; articles = scrape_all_sources(); print(f'获取 {len(articles)} 篇新闻')"

# 测试配置管理
python -c "from src.config import config; print('配置加载成功')"

# 测试规则管理
python -c "from src.rule_manager import RuleManager; m = RuleManager(); print(m.parse_and_execute('列出源'))"
```

## ? 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## ? License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**? News Agent** - 让 AI 帮你每日读新闻

*Powered by DeepSeek + GitHub Actions*