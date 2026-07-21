# 搞钱雷达 V2

## 安装

```bash
# 从 ClawHub 安装
clawhub install money-radar

# 或从本地安装
cp -r /opt/clawhub-skill/money-radar ~/.openclaw/skills/money-radar
```

## 快速开始

```bash
# 预览 24 小时内的搞钱信号
python3 scripts/radar.py --dry-run --no-app-store

# 全量运行
python3 scripts/radar.py

# 自定义参数
python3 scripts/radar.py --hours 48 --no-biz-intel
```

## 环境变量

```bash
export DEEPSEEK_API_KEY=sk-xxx
```

## 输出

报告保存在 `~/workspace/knowledge-base/daily-brief/money-radar-YYYY-MM-DD.md`

## 目录

```
money-radar/
├── SKILL.md          # 技能描述
├── claw.json         # ClawHub 清单
└── scripts/
    └── radar.py      # 主程序 (1100 行, 零 pip 依赖)
```
