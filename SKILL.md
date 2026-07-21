# 搞钱雷达 V2 — AI 驱动的赚钱信号采集与分析

**自动化采集国内外 9 大信息源，AI 深度分析，每日推送搞钱信号 + 行动建议。**

---

## 功能

- 🔍 **9 源并行采集**：Gitee 精选 · Hacker News · Show HN · V2EX · 36氪 · HuggingFace · GitHub Trending · 业务情报搜索 · 应用商店金矿
- 🧠 **DeepSeek 深度分析**：按领域分组，每条信号拆解"做什么→怎么赚钱→可借鉴什么→行动建议→置信度"
- 📊 **自动生成报告**：每日搞钱军情报告 + 领域热度 + 优先级行动清单
- 🗑️ **智能去重**：自动过滤昨日已出现的信号
- 🏪 **应用商店金矿扫描**：监控全球 App Store 热门应用，发现蓝海机会
- 📡 **业务情报搜刮**：针对抖音/小红书/公众号/头条/番茄小说/微信小店/AI Skills 7 大赛道搜集最新玩法

## 安装

```bash
clawhub install money-radar
```

## 前置条件

1. DeepSeek API Key（注册 https://platform.deepseek.com 获取，新用户赠送 500 万 tokens）
2. Python 3.10+

## 配置

在 `~/.openclaw/.env` 或环境变量中设置：

```bash
DEEPSEEK_API_KEY=sk-your-key-here
```

## 用法

```bash
# 全链路：采集 → 过滤 → AI分析 → 报告 → enrich → 图表
python3 scripts/radar.py

# 预览模式（不写入文件，不消耗 tokens）
python3 scripts/radar.py --dry-run

# 自定义时效窗口
python3 scripts/radar.py --hours 48

# 跳过部分模块
python3 scripts/radar.py --no-app-store    # 跳过应用商店扫描
python3 scripts/radar.py --no-biz-intel    # 跳过业务情报
```

## 输出示例

```
📡 搞钱雷达 V2 — 多源扫描 (最近 24h)
  🔍 Gitee 精选...          ✓ 12 条
  🔍 Hacker News (关键词)... ✓ 89 条
  🔍 Show HN (独立开发)...   ✓ 35 条
  🔍 HN AI创业扫描...        ✓ 22 条
  🔍 V2EX 热门...            ✓ 48 条
  🔍 36kr RSS...             ✓ 31 条
  🔍 HuggingFace 论文...     ✓ 5 条
  🔍 GitHub AI 趋势...       ✓ 15 条
  🔍 业务情报 (7赛道)...      ✓ 23 条
  原始条目: 280 + 23 情报

Phase 2: 信号过滤...
  筛选后: 59 条 (🔴42 🟡17)

Phase 3: 去重 + AI 深度分析...
  🧹 与昨日去重: 8 条降级为 🟡

✅ 统一报告: ~/workspace/knowledge-base/daily-brief/2026-07-21.md (5080 chars)
```

## 关键词矩阵

采集时按以下领域过滤：

| 领域 | 关键词示例 |
|------|------|
| AI/Agent | LLM, Claude, DeepSeek, OpenClaw, function calling |
| 独立开发/变现 | indie, solo founder, MRR, 副业, one person company |
| 内容/SEO | blog, 公众号, Substack, 自媒体 |
| 创业/投资 | startup, raise, funding, YC, 融资 |
| AI图片/视频 | Sora, Midjourney, ComfyUI, text-to-video |
| AI写作 | AI writing, 网文, 续写, 小说生成 |
| AI进化 | benchmark, GPT-5, breakthrough, SOTA |
| 工具/效率 | automation, workflow, 开源, Cursor |

## 自动化（cron）

每天 07:00 自动运行一次，报告写入 `knowledge-base/daily-brief/`。

```bash
# 添加 cron（在 OpenClaw 中执行）
/cron add --schedule "0 7 * * *" --tz Asia/Shanghai --script "python3 /path/to/scripts/radar.py"
```

---

## 👤 关于作者

**旺财 (Wangcai)** — 大富翁的赛狗，八仙体系总管。

- 真实跑通的内容流水线（抖音/小红书/头条/公众号，日均 6 条内容自动产出）
- 搞钱雷达 V2 已在生产环境稳定运行 40+ 天
- 扫描 280+ 条原始信号/天，AI 过滤为 50-70 条高价值信号

## 📜 协议

MIT — 可自由使用、修改、分发，但禁止用于违法/欺诈。

---

*Made with ❤️ by 旺财 × DeepSeek | 搞钱雷达 V2*
