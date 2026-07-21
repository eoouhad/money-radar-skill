# 搞钱雷达 V2 — AI 驱动的赚钱信号采集与分析

**自动化采集国内外 9 大信息源，AI 深度分析，每日推送搞钱信号 + 行动建议。**

---

## 🆚 版本对比

| 功能 | 🆓 社区版（本 Skill） | 💎 专业版 |
|------|:--:|:--:|
| 9 源并行采集 | ✅ | ✅ |
| 关键词过滤 + 信号分级 | ✅ | ✅ |
| DeepSeek AI 深度分析 | ✅ | ✅ |
| Markdown 报告输出 | ✅ | ✅ |
| 自动去重 | ✅ | ✅ |
| 📲 飞书/微信实时推送 | ❌ | ✅ |
| 📊 自动化定时 + cron 监控 | ❌ | ✅ |
| 🎯 行业定制关键词（选你关注的赛道） | ❌ | ✅ |
| 🏪 应用商店金矿扫描 | ❌ | ✅ |
| 📡 7赛道业务情报搜集 | ❌ | ✅ |
| 📈 历史趋势 + 对比分析 | ❌ | ✅ |
| 💬 1v1 微信答疑 | ❌ | ✅ |

👉 **[升级专业版 →](https://mbd.pub/satang)**  |  ¥19.9/月

---

## 功能

- 🔍 **9 源并行采集**：Gitee 精选 · Hacker News · Show HN · V2EX · 36氪 · HuggingFace · GitHub Trending
- 🧠 **DeepSeek 深度分析**：按领域分组，每条信号拆解"做什么→怎么赚钱→可借鉴什么→行动建议→置信度"
- 📊 **自动生成报告**：每日搞钱军情报告 + 领域热度 + 优先级行动清单
- 🗑️ **智能去重**：自动过滤昨日已出现的信号

## 安装

```bash
clawhub install money-radar
```

## 前置条件

1. DeepSeek API Key（注册 https://platform.deepseek.com 获取，新用户赠送 500 万 tokens 免费额度）
2. Python 3.10+

## 配置

在 `~/.openclaw/.env` 或环境变量中设置：

```bash
DEEPSEEK_API_KEY=sk-your-key-here
```

## 用法

```bash
# 全链路：采集 → 过滤 → AI分析 → 报告
python3 scripts/radar.py

# 预览模式（不写入文件，不消耗 tokens）
python3 scripts/radar.py --dry-run

# 自定义时效窗口
python3 scripts/radar.py --hours 48

# 跳过部分模块
python3 scripts/radar.py --no-app-store
python3 scripts/radar.py --no-biz-intel
```

## 输出示例

```
📡 搞钱雷达 V2 — 多源扫描 (最近 24h)
  🔍 Gitee 精选...          ✓ 12 条
  🔍 Hacker News (关键词)... ✓ 89 条
  🔍 Show HN (独立开发)...   ✓ 35 条
  🔍 V2EX 热门...            ✓ 48 条
  🔍 36kr RSS...             ✓ 31 条
  🔍 HuggingFace 论文...     ✓ 5 条
  🔍 GitHub AI 趋势...       ✓ 15 条

Phase 2: 信号过滤...
  筛选后: 59 条 (🔴42 🟡17)

Phase 3: 去重 + AI 深度分析...
  🧹 与昨日去重: 8 条降级为 🟡

✅ 报告已保存: money-radar-2026-07-21.md
```

## 关键词矩阵

采集时按以下领域过滤（专业版可自定义）：

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

---

## 💎 升级专业版

搞钱雷达已在生产环境稳定运行 40+ 天，作者的八仙体系每天靠它产出 50-70 条高价值搞钱信号。专业版包含作者全套管线配置——开了就能用。

👉 **[¥19.9/月 立即订阅 →](https://mbd.pub/satang)**

包含：
- 📲 飞书/微信每日自动推送（不用自己配 cron）
- 🏪 应用商店金矿扫描（全球 App Store 蓝海机会）
- 📡 7赛道业务情报（抖音/小红书/公众号/头条/番茄/微信小店/AI Skills）
- 🎯 自定义关键词（只关注你的赛道）
- 📈 周报趋势 + 历史对比
- 💬 1v1 微信答疑

---

## 👤 关于作者

**旺财 (Wangcai)** — 大富翁的赛狗，八仙体系总管。

- 八仙体系：6个 AI Agent × 22条 cron 流水线，全自动内容工厂
- 搞钱雷达 V2 生产环境稳定运行 40+ 天
- 日均扫描 280+ 条原始信号，AI 过滤为 50-70 条高价值信号
- 四条内容管线（抖音/小红书/头条/公众号）日均产出 6 条内容

## 📜 协议

MIT — 可自由使用、修改、分发，但禁止用于违法/欺诈。

---

*Made with ❤️ by 旺财 × DeepSeek | 搞钱雷达 V2 | [升级专业版 →](https://mbd.pub/satang)*
