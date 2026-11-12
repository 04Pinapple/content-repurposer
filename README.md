# content-repurposer

把一篇原始素材，一键改写成小红书 / 公众号 / 微博 / 短视频口播四个平台的稿子。

Turn one source article into ready-to-edit drafts for four platforms: Xiaohongshu, WeChat Official Account, Weibo, and short-video scripts.

---

## 为什么做这个 | Why

做新媒体运营时，同一篇素材要按平台重复改四遍：删字数、换标题、改语气、拆口播。每次都靠手感判断，一稿改到两小时。

> Writing for one platform is easy. Rewriting the same material four ways — trimming to 140 characters, re-titling, changing tone, splitting into a storyboard — is where the hours go.

这个项目把重复的判断固化成规则：平台规范写进 `prompts.py`，素材和规范一起交给模型，人工只做最后一轮判断。

> This project turns the repetitive judgement into explicit rules: platform specs live in `prompts.py`, the model does the first draft, and the human keeps the final call.

## 特点 | Features

- **四个平台的规范是可读的代码**，不是藏在提示词里的口头要求
- **`--mock` 离线模式**：不需要 API Key 也能跑通完整流程，方便看结构和做演示
- **`--dry-run` 看 prompt**：调提示词不用花钱
- **支持任何 OpenAI 兼容接口**：DeepSeek、Moonshot、智谱（BigModel）等只需改 `OPENAI_BASE_URL`
- **硬性约束写进 prompt**：只用素材里出现的事实，不虚构数据

## 快速开始 | Quick start

```bash
pip install -r requirements.txt

# 1. 不花钱先看结构
python repurpose.py -i examples/sample_article.md --mock

# 2. 只看发给模型的 prompt
python repurpose.py -i examples/sample_article.md -p xiaohongshu --dry-run

# 3. 真正调用模型
set OPENAI_API_KEY=sk-xxx        # PowerShell: $env:OPENAI_API_KEY="sk-xxx"
python repurpose.py -i examples/sample_article.md -t "真诚、克制、有信息量"
```

输出会写到 `output/xiaohongshu.md`、`output/wechat.md`、`output/weibo.md`、`output/script.md` 和合并稿 `output/all.md`。

## 参数 | Options

| 参数 | 说明 |
| --- | --- |
| `-i, --input` | 原始素材文件（Markdown 或纯文本） |
| `-p, --platforms` | 目标平台，逗号分隔：`xiaohongshu,wechat,weibo,script` |
| `-t, --tone` | 语气要求，默认「真诚、克制、有信息量」 |
| `-b, --brand` | 账号人设 / 品牌语气说明 |
| `-o, --out` | 输出目录，默认 `output` |
| `--model` / `--base-url` | 模型名与 OpenAI 兼容接口地址 |
| `--mock` | 离线生成示例稿，不调用模型 |
| `--dry-run` | 只打印 prompt |

## 平台规范写在哪 | Where the rules live

`prompts.py` 里的 `PLATFORMS` 是一份可读的规范表，改这里就能改输出风格：

| 平台 | 目标 | 关键约束（节选） |
| --- | --- | --- |
| 小红书 | 让人点开、读完、收藏 | 标题 ≤20 字；正文 300-600 字；每段 1-3 行；末尾 3-6 个话题标签 |
| 公众号 | 把一个观点讲透 | 800-1500 字；3-5 个二级小标题；每个观点跟例子或数据 |
| 微博 | 在信息流里被读完并转发 | ≤140 字；第一句最有信息量；emoji ≤2 |
| 短视频口播 | 前 3 秒留住人 | 3 秒钩子；60-90 秒；每 15 秒一个新信息点；分镜输出 |

## 项目结构 | Layout

```
content-repurposer/
├── repurpose.py              # CLI 入口：读素材 → 组 prompt → 调模型 → 落盘
├── prompts.py                # 平台规范 + prompt 模板（核心可迭代部分）
├── examples/sample_article.md
├── tests/test_repurpose.py   # 单元测试（含 mock 全流程）
├── requirements.txt
└── .env.example
```

## 测试 | Tests

```bash
python -m unittest discover -s tests
```

测试覆盖 prompt 组装、离线输出结构、参数校验和 `--mock` 的端到端落盘。

## 设计取舍 | Trade-offs

- **不做前端**：这类需求的实际使用场景是本地批量跑，CLI 足够；加界面只会增加维护成本。
- **`--mock` 保留**：没有它，任何人克隆下来都要先准备 Key 才能看到效果，验证成本太高。
- **规范与代码分离**：平台风格变化比代码快，把规范放在一个字典里，改文案不用动逻辑。

## Roadmap

- [ ] 支持从 URL 抓取原文（去掉正文噪声）
- [ ] 增加「历史爆款样本」作为 few-shot 参考
- [ ] 输出前做一次事实一致性检查（数字、专有名词是否都在原文出现）

## License

MIT
