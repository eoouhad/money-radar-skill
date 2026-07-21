#!/usr/bin/env python3
"""
搞钱雷达 V2 — 融入 industry-intelligence-radar 多源扫描

V1: 只采集 Gitee 精选 + AI 分析
V2: Gitee + Hacker News + V2EX + RSS 多源并行 → 关键词过滤 → 信号分级 → 每日简报

用法：
    python3 gitee_daily_report.py              # 跑全链路 + 自动 enrich
    python3 gitee_daily_report.py --dry-run    # 预览不写入

零 pip 依赖(仅 Python 标准库 + DeepSeek API)
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import hashlib
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime


def _load_key():
    """加载 DeepSeek API Key"""
    key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    # 尝试从 .env 文件读取
    for env_path in ["/opt/publish-platform/.env", os.path.expanduser("~/.openclaw/.env"), ".env"]:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DEEPSEEK_API_KEY=") or line.startswith("DEEPSEEK_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 wangcai-radar-v2"

# ═══════════════════════════════════════════
#  关键词矩阵
# ═══════════════════════════════════════════

KEYWORD_MAP = {
    "AI/Agent": ["AI agent", "LLM", "大模型", "Claude", "GPT", "DeepSeek", "MCP", "function calling",
                 "OpenClaw", "Skill", "AI coding", "AI编程", "Agent"],
    "独立开发/变现": ["独立开发者", "独立开发", "indie", "solo founder", "MRR", "ARR", "$K",
                "收入", "变现", "副业", "side project", "micro SaaS", "一人公司"],
    "内容/SEO": ["内容创作", "SEO", "博客", "blog", "写作", "writing", "content",
               "公众号", "Substack", "newsletter", "自媒体"],
    "创业/投资": ["创业", "融资", "投资", "YC", "a16z", "红杉", "天使", "估值",
               "startup", "raise", "funding"],
    "跨境电商": ["跨境电商", "TikTok Shop", "SHEIN", "独立站", "DTC", "Shopify",
               "Amazon", "亚马逊"],
    "工具/效率": ["工具", "tool", "效率", "自动化", "automation", "workflow",
               "生产力", "productivity", "编程", "Codex", "Cursor", "开源项目",
               "前端", "后端", "面试", "架构"],
    "知识库/AI搜索": ["知识库", "knowledge base", "RAG", "AI搜索", "AI search",
                   "向量", "embedding", "第二大脑"],
    # ── 新增四赛道 ──
    "AI图片/视频": ["AI image", "AI video", "AI 图片", "AI 视频", "AI生图", "AI绘图",
                  "Seedream", "Seedance", "Sora", "Midjourney", "Stable Diffusion", "SD",
                  "Flux", "ComfyUI", "视频生成", "image generation", "video generation",
                  "AI photography", "AI摄影", "AI修图", "AI剪辑", "AI短视频",
                  "text-to-image", "text-to-video", "图生视频", "文生图", "文生视频"],
    "AI写作技术": ["AI写作", "AI writing", "AI 写作", "AI生成文章", "AI content",
                  "AI文案", "AI编剧", "AI故事", "AI小说", "AI写书", "novel", "story",
                  "长篇", "网文", "claude writing", "续写", "小说生成", "故事生成",
                  "narrative AI", "creative writing AI", "chapter", "plot",
                  "deep writing", "prompt engineering写作", "写作prompt",
                  "角色", "世界观", "world building", "大纲生成", "plot generation",
                  "AI代写", "AI撰稿", "自动写作",  "写作工具", "writing tool",
                  "AI ghostwriter", "AI content generator", "写作workflow"],
    "AI进化": ["new model", "新模型", "benchmark", "基准", "GPT-5", "Claude 4", "Gemini",
              "LLaMA", "Qwen", "DeepSeek", "Mixtral", "突破", "breakthrough", "SOTA",
              "state of the art", "reasoning", "推理", "multimodal", "多模态",
              "AI benchmark", "MMLU", "HumanEval", "参数", "parameters", "token"],
    "AI前沿技术": ["transformer", "attention", "diffusion", "RLHF", "fine-tuning",
                  "微调", "LoRA", "quantization", "量化", "RAG", "retrieval",
                  "embeddings", "vector database", "向量数据库", "AI safety", "alignment",
                  "对齐", "论文", "paper", "arxiv", "conference", "ICML", "NeurIPS",
                  "CVPR", "ICLR", "open source AI", "开源模型", "AI research"],
    "AI创业案例": ["AI创业", "AI startup", "how I built", "how we built", "收入", "revenue",
                  "增长", "growth", "从0到1", "zero to one", "创始人", "founder story",
                  "创业故事", "成功案例", "case study", "案例分析", "AI产品", "AI product",
                  "launched", "上线", "用户", "users", "DAU", "MAU", "profit", "盈利",
                  "build in public", "公开构建", "复盘", "postmortem", "lessons learned",
                  "经验分享", "年入", "月入", "ARR", "MRR", "付费用户", "paying users",
                  "退出", "exit", "收购", "acquired", "acquihire"],
    # ── 业务情报赛道 ──
    "📡 业务情报": ["抖音运营", "抖音短视频技巧", "小红书运营", "情感赛道", "公众号写作",
                  "GEO搜索", "微信公众号", "今日头条运营", "微头条爆款", "番茄小说",
                  "AI写作技巧", "网文写作", "微信小店", "社交电商", "AI agent技能",
                  "AI工具", "自动化工作流"],
}

HIGH_SIGNAL = ["融资", "发布", "开源", "月入", "MRR", "ARR", "$K", "突破",
               "raise", "funding", "launch", "release", "开卖", "上线"]


# ═══════════════════════════════════════════
#  多源采集
# ═══════════════════════════════════════════

def http_get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_gitee_explore():
    """Gitee 精选 — 抓取 Gitee Explore Atom Feed（或降级到 GitHub Search）"""
    # 优先尝试 Gitee 官方 Atom Feed
    try:
        raw = http_get("https://gitee.com/explore.atom", timeout=10)
        root = ET.fromstring(raw.decode("utf-8"))
        items = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title")
            link = entry.find("{http://www.w3.org/2005/Atom}link")
            if title is not None and link is not None:
                items.append({
                    "title": title.text.strip() if title.text else "",
                    "url": link.get("href", ""),
                    "source": "Gitee", "ts": 0, "points": 0,
                })
        return items[:15]
    except Exception as e:
        print(f"  ⚠️  Gitee Feed 不可达: {e}", file=sys.stderr)

    # 降级：GitHub Search API（未经认证限 10次/分钟，只做1次）
    try:
        data = json.loads(http_get(
            "https://api.github.com/search/repositories?q=AI+chinese+language:zh&sort=stars&order=desc&per_page=10",
            timeout=10
        ))
        items = []
        for repo in (data.get("items", []) or [])[:10]:
            name = repo.get("full_name", "")
            desc = (repo.get("description") or "")[:60]
            stars = repo.get("stargazers_count", 0)
            items.append({
                "title": f"{name} ⭐{stars} — {desc}" if desc else f"{name} ⭐{stars}",
                "url": repo.get("html_url", ""),
                "source": "Gitee", "ts": 0, "points": stars,
            })
        return items
    except Exception as e:
        print(f"  ⚠️  Gitee 数据源全部不可用: {e}", file=sys.stderr)
    return []


def fetch_hackernews(keywords, since_ts):
    """Hacker News via Algolia API"""
    items, seen = [], set()
    for kw in keywords[:6]:  # 限制 API 调用次数
        q = urllib.parse.quote(kw)
        url = (f"https://hn.algolia.com/api/v1/search_by_date?query={q}"
               f"&tags=story&numericFilters=created_at_i>{since_ts}&hitsPerPage=10")
        try:
            data = json.loads(http_get(url))
        except Exception:
            continue
        for hit in data.get("hits", []):
            oid = hit.get("objectID")
            if not oid or oid in seen:
                continue
            seen.add(oid)
            title = hit.get("title") or ""
            if not title:
                continue
            link = hit.get("url") or f"https://news.ycombinator.com/item?id={oid}"
            items.append({
                "title": title, "url": link, "source": "Hacker News",
                "ts": hit.get("created_at_i", 0),
                "points": hit.get("points", 0),
            })
    return items


def fetch_show_hn(since_ts):
    """Show HN — 独立开发者新产品展示(Starter Story 平替)"""
    items, seen = [], set()
    url = (f"https://hn.algolia.com/api/v1/search_by_date?query=Show+HN"
           f"&tags=show_hn&numericFilters=created_at_i>{since_ts}&hitsPerPage=30")
    try:
        data = json.loads(http_get(url, timeout=25))
    except Exception as e:
        print(f"  ⚠️  Show HN 抓取失败: {e}", file=sys.stderr)
        return []
    for hit in data.get("hits", []):
        oid = hit.get("objectID")
        if not oid or oid in seen:
            continue
        seen.add(oid)
        title = (hit.get("title") or "").replace("Show HN: ", "").replace("Show HN:", "")
        if not title:
            continue
        link = hit.get("url") or f"https://news.ycombinator.com/item?id={oid}"
        points = hit.get("points", 0)
        comments = hit.get("num_comments", 0)
        items.append({
            "title": title, "url": link, "source": "Show HN",
            "ts": hit.get("created_at_i", 0),
            "points": points,
            "comments": comments,
            "_raw": {"points": points, "comments": comments},
        })
    # 按热度排序
    items.sort(key=lambda x: (x["points"] or 0), reverse=True)
    return items


def fetch_hn_ai_indie(since_ts):
    """HN 关键词搜索: AI + indie/startup/saas/mrr 组合"""
    queries = [
        "AI startup", "AI SaaS", "AI agent",
        "indie hacker", "micro SaaS", "MRR",
        "AI video generation", "AI image generation",
        "AI writing", "AI novel", "AI workflow",
        "new AI model", "AI benchmark", "open source AI",
        "how I built AI", "AI startup story", "AI revenue",
    ]
    items, seen = [], set()
    for q in queries:
        if len(items) >= 25:
            break
        url = (f"https://hn.algolia.com/api/v1/search_by_date?query={urllib.parse.quote(q)}"
               f"&tags=story&numericFilters=created_at_i>{since_ts}&hitsPerPage=5")
        try:
            data = json.loads(http_get(url, timeout=8))
        except Exception:
            continue
        for hit in data.get("hits", []):
            oid = hit.get("objectID")
            if not oid or oid in seen:
                continue
            seen.add(oid)
            title = hit.get("title") or ""
            if not title:
                continue
            link = hit.get("url") or f"https://news.ycombinator.com/item?id={oid}"
            items.append({
                "title": title, "url": link, "source": "HN·AI创业",
                "ts": hit.get("created_at_i", 0),
                "points": hit.get("points", 0),
            })
    items.sort(key=lambda x: (x["points"] or 0), reverse=True)
    return items[:25]


def fetch_v2ex():
    """V2EX + 国内替代源(掘金/CSDN)三路回退"""
    # 方案1: V2EX API(被墙时自动跳过)
    try:
        data = json.loads(http_get("https://www.v2ex.com/api/topics/hot.json", timeout=10))
        return [{
            "title": t.get("title", ""), "url": t.get("url", ""),
            "source": "V2EX", "ts": t.get("created", 0),
            "points": t.get("replies", 0),
        } for t in data]
    except Exception:
        pass

    items = []
    # 方案2: 掘金推荐流(POST，国内直连)
    try:
        body = json.dumps({"id_type": 2, "sort_type": 200, "cursor": "0", "limit": 15}).encode()
        req = urllib.request.Request(
            "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed",
            data=body,
            headers={"User-Agent": UA, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            jj = json.loads(resp.read())
        for item in (jj.get("data", []) or [])[:10]:
            # 掘金返回结构: item_info.article_info.{title, article_id, ctime, digg_count}
            item_info = item.get("item_info", {}) or {}
            info = item_info.get("article_info", {}) or {}
            title = (info.get("title") or "").strip()
            article_id = info.get("article_id", "")
            digg = info.get("digg_count", 0) or info.get("collect_count", 0) or 0
            if title:
                # ts=0 跳过时区过滤(掘金热榜文章可能几周前的)
                items.append({
                    "title": f"[掘金] {title}",
                    "url": f"https://juejin.cn/post/{article_id}" if article_id else "",
                    "source": "V2EX", "ts": 0,
                    "points": digg,
                })
    except Exception as e:
        print(f"  ⚠️  掘金抓取失败: {e}", file=sys.stderr)

    # 方案3: CSDN 热榜
    if not items:
        try:
            csdn = json.loads(http_get(
                "https://blog.csdn.net/api/ranking/list?type=hot", timeout=10
            ))
            for art in (csdn.get("data", []) or [])[:10]:
                items.append({
                    "title": f"[CSDN] {art.get('title','')}",
                    "url": art.get("url", ""),
                    "source": "V2EX", "ts": 0,
                    "points": art.get("view_count", 0) or art.get("hot", 0),
                })
        except Exception:
            pass

    return items


def fetch_36kr():
    """36kr 快讯 (RSS via standard lib)"""
    try:
        raw = http_get("https://www.36kr.com/feed")
        root = ET.fromstring(raw)
    except Exception:
        return []
    items = []
    for n in root.findall(".//item"):
        title = ""
        link = ""
        for child in n:
            if child.tag == "title":
                title = (child.text or "").strip()
            elif child.tag == "link":
                link = (child.text or "").strip()
        if title and link:
            items.append({"title": title, "url": link, "source": "36kr", "ts": 0, "points": 0})
    return items


def fetch_huggingface_papers():
    """HuggingFace 论文 — 直连，失败跳过(GitHub AI + HN 已覆盖 AI 前沿)"""
    try:
        data = json.loads(http_get("https://huggingface.co/api/daily_papers", timeout=15))
        items = []
        for p in (data or [])[:10]:
            title = (p.get("title") or "").strip()
            paper_id = p.get("paper", {}).get("id", "")
            url = f"https://huggingface.co/papers/{paper_id}" if paper_id else ""
            if title:
                items.append({
                    "title": f"📄 {title}", "url": url,
                    "source": "HF Papers", "ts": 0,
                    "points": p.get("upvotes", 0) or p.get("numComments", 0),
                })
        return items
    except Exception:
        # HF 间歇被墙 / ModelScope+PWC 均不可达 — 跳过
        # GitHub AI 和 HN·AI创业 已覆盖 AI 前沿论文/模型信息
        pass
    return []


def fetch_github_trending_ai():
    """GitHub Trending — AI 全赛道宽覆盖(去重合并到 GitHub AI 源)"""
    # 扩张 topic 覆盖(原 7→30 个，覆盖 AI 全赛道)
    ai_topics = [
        # 图片/视频/音频
        "ai-image-generation", "text-to-video", "image-to-video",
        "stable-diffusion", "text-to-image", "music-generation",
        "ai-video", "video-generation",
        # 模型/框架
        "llm", "large-language-models", "transformers", "deep-learning",
        "machine-learning", "nlp", "computer-vision",
        # Agent / 工具链
        "ai-agent", "llm-agent", "agent-framework", "mcp-server",
        "ai-tools", "ai-platform",
        # 写作/内容
        "ai-writing", "text-generation", "rag",
        # 新赛道
        "ai-voice", "text-to-speech", "ai-assisted-coding",
        "coding-agent", "openai-api",
    ]
    items = []
    for topic in ai_topics:
        url = (f"https://api.github.com/search/repositories?q=topic:{topic}"
               f"&sort=stars&order=desc&per_page=3")
        try:
            data = json.loads(http_get(url, timeout=15))
        except Exception:
            continue
        for repo in (data.get("items", []) or []):
            name = repo.get("full_name", "")
            stars = repo.get("stargazers_count", 0)
            lang = (repo.get("language") or "")
            desc = (repo.get("description") or "")[:80]
            title = f"{name} ⭐{stars}"
            if lang:
                title += f" [{lang}]"
            items.append({
                "title": f"{title} — {desc}" if desc else title,
                "url": repo.get("html_url", ""),
                "source": "GitHub AI",  # 合并到 GitHub AI，与 github search 统一
                "ts": 0,
                "points": stars,
            })
    # 去重 + 按 stars 降序
    seen = set()
    unique = []
    for it in sorted(items, key=lambda x: -(x["points"] or 0)):
        key = it["title"][:60]
        if key not in seen:
            seen.add(key)
            unique.append(it)
    if not unique:
        print(f"  ⚠️  GitHub Trending: 0 条，API 可能限流或网络问题", file=sys.stderr)
    return unique[:20]


# ═══════════════════════════════════════════
#  业务情报采集
# ═══════════════════════════════════════════

# 业务情报搜索关键词映射(每个业务取1-2个高频搜索词)
BUSINESS_INTEL_QUERIES = {
    "🎵 抖音": ["抖音短视频创作新技巧 AI工具 2025 2026",
                "抖音中老年健康视频运营 AI视频工具"],
    "📕 小红书": ["小红书图文运营技巧 情感赛道 2025 2026",
                 "小红书AI工具 图文运营 起号攻略"],
    "💚 公众号": ["微信公众号GEO搜索优化 写作方法 2025 2026",
                "微信公众号AI辅助写作 爆文方法"],
    "📰 头条/微头条": ["今日头条运营 微头条爆款文案 中老年赛道 2025 2026",
                    "头条AI写作限流 微头条收益提升"],
    "📖 番茄小说": ["番茄小说写作技巧 AI辅助写作 网文平台新政策 2025 2026",
                  "番茄小说AI写作工具 ranking 长篇连载技巧"],
    "🛒 微信小店": ["微信小店运营技巧 个体工商户 社交电商新玩法 2025 2026",
                  "微信小店带货攻略 达人合作 自然流"],
    "🛠️ AI Skills": ["AI Agent技能 MCP新工具 自动化工作流 2025 2026",
                   "AI写作出图剪辑新工具 2026 AI creative tools"],
}


def fetch_business_intel():
    """
    Phase 1 扩展：对每个业务赛道搜索 1-2 次，收集最新技能/工具/玩法情报。
    返回 list[dict]，格式与现有 items 一致(含 source='📡 业务情报')。
    """
    items, seen = [], set()
    for biz_tag, queries in BUSINESS_INTEL_QUERIES.items():
        for q in queries[:2]:  # 每赛道最多2次搜索
            if len(items) >= 40:
                break
            try:
                # 动态导入 web_search（仅运行时注入）
                import importlib
                pass
            except Exception:
                pass
    return items


def _search_business_intel_queries():
    """
    替函: web_search 不可直接在 Python 脚本中使用，
    改用 web_fetch 抓搜索结果页或直接调用 Tavily API。
    这里用 urllib + Tavily Search API 直接搜。
    """
    import urllib.request
    import urllib.parse
    import json as _json
    import time

    items, seen = [], set()

    try:
        # 尝试从环境变量或配置文件获取 TAVILY_API_KEY
        api_key = os.environ.get("TAVILY_API_KEY", "")
        if not api_key:
            # 尝试从 ~/.config/tavily.json 读取
            cfg_path = os.path.expanduser("~/.config/tavily.json")
            if os.path.exists(cfg_path):
                with open(cfg_path) as f:
                    cfg = _json.load(f)
                    api_key = cfg.get("api_key", "")
    except Exception:
        api_key = ""

    if not api_key:
        print("  ⚠️  TAVILY_API_KEY 未配置，跳过业务情报搜索", file=sys.stderr)
        return []

    tavily_url = "https://api.tavily.com/search"

    for biz_tag, queries in BUSINESS_INTEL_QUERIES.items():
        if len(items) >= 40:
            break
        for q in queries[:2]:
            if len(items) >= 40:
                break
            try:
                payload = _json.dumps({
                    "query": q,
                    "search_depth": "basic",
                    "max_results": 3,
                }).encode("utf-8")
                req = urllib.request.Request(
                    tavily_url,
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}",
                    },
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = _json.loads(resp.read())

                for r in data.get("results", []):
                    title = (r.get("title") or "").strip()
                    url = r.get("url", "")
                    if not title or not url:
                        continue
                    key = title[:80].lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    snippet = (r.get("snippet") or r.get("content") or "")[:120]
                    items.append({
                        "title": f"[{biz_tag}] {title}",
                        "url": url,
                        "source": "📡 业务情报",
                        "ts": 0,
                        "points": 0,
                        "snippet": snippet,
                        "biz_tag": biz_tag,
                    })

                # API 限流保护
                time.sleep(0.3)
            except Exception as e:
                print(f"  ⚠️  业务情报搜索失败 [{biz_tag}]: {e}", file=sys.stderr)
                continue

    # 按业务分组排序
    print(f"  📡 业务情报: {len(items)} 条 (7个业务赛道)", file=sys.stderr)
    return items[:40]


# ═══════════════════════════════════════════
#  信号处理
# ═══════════════════════════════════════════

def match_domains(title, keyword_map):
    low = title.lower()
    return [d for d, words in keyword_map.items()
            if any(w.lower() in low for w in words)]


def signal_level(title, high_signal):
    low = title.lower()
    return "🔴" if any(w.lower() in low for w in high_signal) else "🟡"


# ═══════════════════════════════════════════
#  AI 深度分析(继承 V1)
# ═══════════════════════════════════════════

def _load_yesterday_titles():
    """加载昨天的 TOP 信号标题，用于今日去重"""
    yesterday = (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).strftime("%Y-%m-%d")
    path = os.path.expanduser(
        f"~/.openclaw/workspace/knowledge-base/daily-brief/{yesterday}.md"
    )
    titles = set()
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
        # 提取表格中标注为 🔴 的标题
        import re
        for m in re.finditer(r'\|\s*\d+\s*\|\s*🔴\s*\|[^|]+\|\s*\[(.+?)\]', content):
            titles.add(m.group(1).lower().strip())
    return titles


def _dedupe_items(items):
    """去重：昨天 TOP 中出现的信号自动降级为 🟡"""
    yesterday_titles = _load_yesterday_titles()
    if not yesterday_titles:
        return items
    for it in items:
        title_lower = it["title"].lower().strip()
        if title_lower in yesterday_titles and it["level"] == "🔴":
            it["level"] = "🟡"
            it["deduped"] = True
    return items


def ai_deep_analysis(items, domain_count, api_key, biz_items=None):
    """
    深度分析：每个领域挑最新 2 条信号，做深度拆解。
    比旧版只挑 TOP3 更全面、更有深度。
    biz_items: 业务情报列表(可选)，用于生成独立业务情报板块
    """
    if not items:
        return "今日无高价值情报，可能是采集源暂时不可达或窗口内无关内容。", []

    # 按领域分组
    domains_sorted = sorted(domain_count.items(), key=lambda x: -x[1])
    domain_items = {}
    for d, _ in domains_sorted:
        domain_items[d] = [it for it in items if d in it["domains"]]

    # 每个领域取最新 2 条(优先 🔴 信号，避开昨天重复的)
    briefs = []
    seen_urls = set()
    for d, ditems in domain_items.items():
        # 先取 🔴 的信号
        reds = [it for it in ditems if it["level"] == "🔴" and it["url"] not in seen_urls]
        yellows = [it for it in ditems if it["url"] not in seen_urls and it not in reds]
        picks = (reds + yellows)[:2]
        for it in picks:
            seen_urls.add(it["url"])
            briefs.append({
                "domain": d,
                "source": it["source"],
                "title": it["title"],
                "url": it["url"],
                "level": it["level"],
            })

    if not briefs:
        return "今日无线索值得深度分析。", []

    # 构建 prompt
    domain_summary = "\n".join(
        f"**{d}** ({c} 条)" for d, c in domains_sorted[:8]
    )
    brief_lines = []
    for i, b in enumerate(briefs, 1):
        tag = "NEW" if b["level"] == "🔴" else ""
        brief_lines.append(
            f"{i}. [{b['source']}] {b['domain']} | {b['title']}{' 🔥'+tag if tag else ''}\n"
            f"   {b['url']}"
        )

    prompt = (
        "你是搞钱雷达首席分析师。以下是今日各领域的最新信号，请做深度拆解。\n\n"
        "## 今日领域热度\n"
        f"{domain_summary}\n\n"
        "## 各领域最新信号(每领域取最新2条)\n"
        f"{chr(10).join(brief_lines)}\n\n"
        "## 分析要求\n\n"
        "### 每领域至少拆解 2 条最新信号\n"
        "对每条信号给出:\n\n"
        "**项目名·一句话定性**\n"
        "- **做什么**: 核心技术/产品是什么(50字内)\n"
        "- **怎么赚钱**: 变现路径分析\n"
        "- **可借鉴什么**: 与大富翁的关联\n"
        "- **行动建议**: P0/P1/P2/P3优先级分层（每层≤2条；不需要每条都凑建议！不相关写「不追」）\n"
        "- **置信度**: ✅已验证 / ⚠️推测待验证 / ❓未知\n\n"
        "### 📡 业务情报(独立板块)\n"
        "如果下面是业务情报列表不为空，请在分析最后用「## 📡 业务情报简报」独立段落总结:\n"
        "- 格式: `[业务标签] | 技能/工具名称 | 一句话说明 | 适用业务 | 优先级(P0-P3)`\n"
        "- P0=今天可落地、P1=本周试用、P2=观察跟踪、P3=不适用\n"
        "- 每个业务最多2条，精选最可执行的\n"
        "- 优先推荐零成本/免费的工具和方法\n\n"
        "### 重点赛道必覆盖\n"
        "- AI 图片/视频生成 → 大富翁有 Seedream+Seedance 管线\n"
        "- AI 写作技术 → 大富翁有内容管线\n"
        "- AI 创业案例 → 大富翁可直接借鉴\n"
        "- 独立开发/变现 → 零成本启动方案优先\n\n"
        "### ⚠️ 务实分析铁律\n"
        "- GitHub ⭐<500 → 「微型项目暂不追」\n"
        "- GPU 方案 → 自动标注「❌ 不可行: 4核CPU无GPU」\n"
        "- 本地大模型 → 「❌ 不可行: deepseek API 已近免费」\n"
        "- 每个结论必须标注置信度\n"
        "- 如果某领域信号都为旧/不相关，直接写「本领域今日无新信号」\n\n"
        "### 🚫 行动建议铁律（07/15新增）\n"
        "- P0=今天必做(影响收入) / P1=本周可做 / P2=观察调研 / P3=不适合/不追\n"
        "- 每层最多2条，总建议不超过6条！不相关信号写「❌ 不追」\n"
        "- 禁止「今天XXX」句式— 大富翁孤身创业者，一天做不了13件事\n"
        "- 禁止给 OpenClaw Agent 加功能— OpenClaw 是运维工具不是产品\n"
        "- 禁止「安装/部署新项目」建议— 零成本优先，每个新依赖=长期维护负担\n"
        "- 内容管线建议等数据反馈后再提，别急着加新东西\n\n"
        "### 输出格式\n"
        "用 Markdown，以领域为二级标题，每个领域 2-3 条拆解。结尾给「今日搞钱洞察」+ 「🚀 优先级行动清单」(P0/P1/P2/P3)。\n\n"
        "## 👤 大富翁画像\n"
        "| 项目 | 状态 |\n"
        "|------|------|\n"
        "| 心情小札 APP | 已上线，待应用商店审核 |\n"
        "| 知宅风水 APP | 6/6功能完成，待上线运营 |\n"
        "| 查订阅 小程序 | 审核中 |\n"
        "| 沐信健康 抖音 | 运营中，刚优化prompt |\n"
        "| 头条撒汤 | 运营中，刚优化prompt |\n"
        "| 小红书 心情小札 | 运营中，情感赛道转型 |\n"
        "| 公众号 沐信国学 | 运营中，国学情感内容 |\n"
        "| 蔷薇旧雨 番茄小说 | 连载中(94/152回) |\n"
        "\n"
        "资源: 轻量云(4核CPU/7.5GB RAM/无GPU)。API: DeepSeek/火山Seedream+Seedance。\n"
        "原则: 零成本优先，不引新依赖，孤身创业一天只能做1-2件事。"
    )

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是搞钱雷达首席分析师。只输出结构化分析，不废话。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6, "max_tokens": 4096,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read())
    analysis = data["choices"][0]["message"]["content"].strip()

    refs = [{"title": b["title"], "url": b["url"], "source": b.get("source", ""),
             "domain": b.get("domain", "")} for b in briefs]
    return analysis, refs


# ═══════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════

def _generate_radar_charts(domain_count, src_count, date_str, out_dir):
    """
    Phase 6: 用 Flint 生成搞钱雷达图表(领域热度 + 来源分布)
    输出 HTML 到简报目录，可直接浏览器预览或截图。
    """
    try:
        from flint_chart import flint_chart, flint_chart_render_html, flint_chart_to_png
    except ImportError:
        print("  ⚠️  flint_chart 模块不可用，跳过图表生成", file=sys.stderr)
        return []
    
    out_dir = os.path.join(out_dir, "charts")
    os.makedirs(out_dir, exist_ok=True)
    charts = []
    
    # 1. 领域热度柱状图
    data = [{"领域": d, "热度": c} for d, c in sorted(domain_count.items(), key=lambda x: -x[1])[:8]]
    if data:
        spec = flint_chart(
            data=data,
            chart_type="Bar Chart",
            x_field="领域", y_field="热度",
            title=f"搞钱雷达 · 领域热度 ({date_str})",
            width=700, height=400,
        )
        if spec:
            path = os.path.join(out_dir, f"radar_domains_{date_str}.html")
            flint_chart_render_html(spec, path)
            # 也生成 PNG 用于直接配图
            png_path = os.path.join(out_dir, f"radar_domains_{date_str}.png")
            flint_chart_to_png(spec, png_path)
            charts.append(path)
            charts.append(png_path)
            print(f"    📊 领域热度: {os.path.basename(path)} + PNG", file=sys.stderr)
    
    # 2. 来源分布饼图
    data2 = [{"来源": s, "条数": c} for s, c in sorted(src_count.items(), key=lambda x: -x[1])[:6]]
    if len(data2) >= 2:
        spec2 = flint_chart(
            data=data2,
            chart_type="Pie Chart",
            x_field="来源", y_field="条数",
            title=f"搞钱雷达 · 来源分布 ({date_str})",
            width=650, height=420,
        )
        if spec2:
            path2 = os.path.join(out_dir, f"radar_sources_{date_str}.html")
            flint_chart_render_html(spec2, path2)
            png2 = os.path.join(out_dir, f"radar_sources_{date_str}.png")
            flint_chart_to_png(spec2, png2)
            charts.append(path2)
            charts.append(png2)
            print(f"    📊 来源分布: {os.path.basename(path2)} + PNG", file=sys.stderr)
    
    return charts


def main():
    parser = argparse.ArgumentParser(description="搞钱雷达 V2")
    parser.add_argument("--hours", type=int, default=24, help="时效窗口(小时)")
    parser.add_argument("--dry-run", action="store_true", help="预览不写入文件")
    parser.add_argument("--no-enrich", action="store_true", help="不自动 content-enrich")
    parser.add_argument("--no-app-store", action="store_true", help="跳过应用商店扫描")
    parser.add_argument("--no-biz-intel", action="store_true", help="跳过业务情报采集")
    args = parser.parse_args()

    api_key = _load_key()
    if not api_key:
        print("❌ DEEPSEEK_API_KEY 未设置", file=sys.stderr)
        sys.exit(1)

    all_keywords = sorted({w for words in KEYWORD_MAP.values() for w in words})
    since = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    since_ts = int(since.timestamp())

    print("=" * 60, file=sys.stderr)
    print(f"📡 搞钱雷达 V2 — 多源扫描 (最近 {args.hours}h)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Phase 1: 多源采集
    raw = []
    print("  🔍 Gitee 精选...", file=sys.stderr)
    raw += fetch_gitee_explore()
    print("  🔍 Hacker News (关键词)...", file=sys.stderr)
    raw += fetch_hackernews(all_keywords, since_ts)
    print("  🔍 Show HN (独立开发者新品)...", file=sys.stderr)
    raw += fetch_show_hn(since_ts)
    print("  🔍 HN AI创业扫描...", file=sys.stderr)
    raw += fetch_hn_ai_indie(since_ts)
    print("  🔍 V2EX 热门...", file=sys.stderr)
    raw += fetch_v2ex()
    print("  🔍 36kr RSS...", file=sys.stderr)
    raw += fetch_36kr()
    print("  🔍 HuggingFace 论文...", file=sys.stderr)
    raw += fetch_huggingface_papers()
    print("  🔍 GitHub AI 趋势...", file=sys.stderr)
    raw += fetch_github_trending_ai()
    print("  🔍 业务情报 (7赛道)...", file=sys.stderr)
    biz_items = [] if args.no_biz_intel else _search_business_intel_queries()
    if args.no_biz_intel:
        print("  ⏭️  已跳过业务情报", file=sys.stderr)
    print(f"  原始条目: {len(raw)}" +
          (f" + {len(biz_items)} 情报" if biz_items else ""), file=sys.stderr)

    # Phase 2: 过滤
    print("Phase 2: 信号过滤...", file=sys.stderr)
    seen, items = set(), []
    for it in raw:
        title = it["title"].strip()
        if not title or title.lower() in seen:
            continue
        if it["ts"] and it["ts"] < since_ts:
            continue
        domains = match_domains(title, KEYWORD_MAP)
        if not domains:
            continue
        seen.add(title.lower())
        items.append({**it, "domains": domains, "level": signal_level(title, HIGH_SIGNAL)})

    items.sort(key=lambda x: (x["level"] != "🔴", -(x["points"] or 0), -(x["ts"] or 0)))
    print(f"  筛选后: {len(items)} 条 (🔴{sum(1 for i in items if i['level']=='🔴')} "
          f"🟡{sum(1 for i in items if i['level']=='🟡')})", file=sys.stderr)

    if args.dry_run:
        print("\n📊 搞钱信号预览:\n")
        for i, it in enumerate(items[:20], 1):
            print(f"{i}. {it['level']} [{it['source']}] {it['title']}")
            print(f"   领域: {', '.join(it['domains'])} | {it['url']}")
        if biz_items:
            print(f"\n📡 业务情报预览 ({len(biz_items)} 条):\n")
            for i, bi in enumerate(biz_items[:20], 1):
                tag = bi.get("biz_tag", "")
                title = bi["title"].replace(f"[{tag}] ", "")
                print(f"{i}. [{tag}] {title[:60]}")
                print(f"   {bi['url']}")
        return

    # Phase 2.5: 应用商店扫描 (轻量，不阻塞)
    app_store_report = ""
    if not args.no_app_store:
        print("Phase 2.5: 应用商店扫描...", file=sys.stderr)
        try:
            import subprocess as sp
            import os as _os
            scanner = _os.path.join(_os.path.dirname(__file__), "app_store_scanner.py")
            result = sp.run(
                ["python3", scanner, "--markets", "cn", "--limit", "10", "--zombie-days", "180"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                # 读取生成的报告
                cache_path = _os.path.expanduser(
                    f"~/.openclaw/workspace/knowledge-base/daily-brief/app_store_{now.strftime("%Y-%m-%d")}.md"
                )
                if os.path.exists(cache_path):
                    with open(cache_path) as f:
                        app_store_report = f.read()
                    print(f"  📱 应用商店: {len(app_store_report)} bytes", file=sys.stderr)
                else:
                    print(f"  ⚠️ 报告未生成", file=sys.stderr)
            else:
                print(f"  ⚠️ 扫描失败: {result.stderr[:100]}", file=sys.stderr)
        except Exception as e:
            print(f"  ⚠️ 扫描异常: {e}", file=sys.stderr)

    # Phase 3: AI 深度分析(新：按领域分组，每领域取最新2条，昨日去重)
    print("Phase 3: 去重 + AI 深度分析...", file=sys.stderr)
    items = _dedupe_items(items)
    new_items = [it for it in items if it.get("deduped")]
    if new_items:
        print(f"  🧹 与昨日去重: {len(new_items)} 条降级为 🟡", file=sys.stderr)

    # 重新排序(去重后 red 可能变 yellow)
    items.sort(key=lambda x: (x["level"] != "🔴", -(x["points"] or 0), -(x["ts"] or 0)))

    # 提前计算 domain_count，供 AI 分析和报告使用
    domain_count = {}
    for it in items:
        for d in it["domains"]:
            domain_count[d] = domain_count.get(d, 0) + 1

    analysis, refs = ai_deep_analysis(items, domain_count, api_key, biz_items=biz_items)

    # Phase 4: 统一报告(搞钱雷达 + 捡尸金矿 + 热榜全整合到一个文件)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    weekday = "星期一星期二星期三星期四星期五星期六星期日"[now.weekday()]

    src_count = {}
    for it in items:
        s = it["source"]
        src_count[s] = src_count.get(s, 0) + 1
    src_summary = " + ".join(f"{s}×{c}" for s, c in sorted(src_count.items(), key=lambda x: -x[1]))

    new_count = sum(1 for it in items if not it.get("deduped") and it["level"] == "🔴")
    old_count = sum(1 for it in items if it.get("deduped"))

    report = f"""---
summary: "{date_str} 搞钱军情：{len(items)}条信号，{len(domain_count)}个领域深度拆解。"
domain: "AI创业与投资"
auto_tags: [{', '.join(f'"{d.replace(" ", "").replace("/", "")}"' for d in sorted(domain_count, key=lambda x: -domain_count[x])[:8])}]
new_signals: {new_count}
duplicated_from_yesterday: {old_count}
enriched: true
---

# 🧭 搞钱军情 · {date_str} {weekday}

> **一句话**：{len(items)} 条信号 · {len(domain_count)} 个领域 · {new_count} 条新信号{'(去重' + str(old_count) + '条昨日重复)' if old_count > 0 else ''}

**来源**: {src_summary}

---

## 📊 今日军情概览

| # | 信号 | 来源 | 标题 | 领域 |
|---|---|---|---|---|
"""
    if items:
        for i, it in enumerate(items, 1):
            doms = ", ".join(it["domains"][:2])
            dedup_tag = " 🔁" if it.get("deduped") else ""
            title_short = it["title"][:40] + ("…" if len(it["title"]) > 40 else "")
            report += f"| {i} | {it['level']}{dedup_tag} | {it['source']} | [{title_short}]({it['url']}) | {doms} |\n"

    # ── 深度分析 ──
    report += f"""
---

## 🔬 领域深度拆解

{analysis}

---

## 📈 领域热度

"""
    for d, c in sorted(domain_count.items(), key=lambda x: -x[1]):
        bar = "█" * min(c, 10)
        report += f"- **{d}** {bar} {c} 条\n"

    # ── 📡 业务情报板块(独立于搞钱信号) ──
    if biz_items:
        report += f"""---

## 📡 业务情报

> 专为 7 个业务赛道搜集的最新技能/工具/玩法 (共 {len(biz_items)} 条)

"""
        # 按业务分组
        biz_by_tag = {}
        for bi in biz_items:
            tag = bi.get("biz_tag", "其他")
            biz_by_tag.setdefault(tag, []).append(bi)
        for tag in ["🎵 抖音", "📕 小红书", "💚 公众号", "📰 头条/微头条",
                     "📖 番茄小说", "🛒 微信小店", "🛠️ AI Skills"]:
            blist = biz_by_tag.get(tag, [])
            if not blist:
                continue
            report += f"### {tag} ({len(blist)} 条)\n\n"
            report += "| 技能/工具 | 说明 | 优先级 | 来源 |\n"
            report += "|---|---|---|---|\n"
            for bi in blist[:3]:
                title = bi["title"].replace(f"[{tag}] ", "")
                title_short = title[:40] + ("…" if len(title) > 40 else "")
                snippet = bi.get("snippet", "")[:60]
                # 自动判级：强信号→P1，一般→P2
                priority = "P1" if any(w in title.lower() for w in ["新功能","上线","发布","突破","爆发","红利"]) else "P2"
                report += f"| [{title_short}]({bi['url']}) | {snippet} | {priority} | {tag} |\n"
            report += "\n"

    # ── 各领域列表 ──
    for d, c in sorted(domain_count.items(), key=lambda x: -x[1]):
        matched = [it for it in items if d in it["domains"]]
        if not matched:
            continue
        report += f"\n### {d}({len(matched)} 条)\n\n"
        report += "| # | 信号 | 来源 | 标题 |\n"
        report += "|---|---|---|---|\n"
        for j, it in enumerate(matched[:20], 1):
            dedup_tag = " 🔁" if it.get("deduped") else ""
            title_short = it["title"][:50] + ("…" if len(it["title"]) > 50 else "")
            report += f"| {j} | {it['level']}{dedup_tag} | {it['source']} | [{title_short}]({it['url']}) |\n"

    # ── 应用商店捡尸金矿 ──
    if app_store_report:
        report += f"\n\n---\n\n{app_store_report}"

    # ── 引用 ──
    report += f"""

---

## 🔗 引用来源

"""
    for ref in refs[:30]:
        dm = f" [{ref.get('domain','')}]" if ref.get('domain') else ""
        report += f"- [{ref['source']}{dm}] {ref['title']}: {ref['url']}\n"

    report += f"""

---
*搞钱雷达 V3 · {now.strftime('%Y-%m-%d %H:%M')} · 领域级深度分析 · 昨日去重*
"""

    # 保存
    out_dir = os.path.expanduser("~/.openclaw/workspace/knowledge-base/daily-brief")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"money-radar-{date_str}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ 统一报告: {out_path} ({len(report)} chars)", file=sys.stderr)























































if __name__ == "__main__":
    main()
