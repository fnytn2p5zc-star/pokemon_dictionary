# Pokemon Dictionary

Pokemon 数据爬虫 + CLI 查看器 + 聊天机器人 + Web 图鉴。

从 [PokeAPI](https://pokeapi.co/) 抓取全部 1025 只 Pokemon 的中/英/日文名称、属性、种族值、特性、官方插图等数据，存入 SQLite，并提供多种方式浏览和查询。

## 功能

- **数据爬虫** — 异步抓取 PokeAPI，支持限速、断点续爬、图片下载
- **特性爬虫** — 抓取特性的中文描述文本
- **CLI 查看器** — 浏览、搜索、按属性/世代/种族值筛选、查看详情
- **聊天机器人** — 自然语言问答，支持中英文提问
- **Web 图鉴** — Flask Web 界面，卡片网格、搜索、筛选、详情页
- **数据导出** — JSON / CSV 格式导出

## 安装

```bash
# 需要 Python >= 3.11
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 使用

### 1. 爬取数据

```bash
# 爬取全部 Pokemon 数据和图片
pokemon-scraper scrape

# 指定范围
pokemon-scraper scrape --start 1 --end 151

# 跳过图片下载
pokemon-scraper scrape --skip-images

# 调整请求速率 (默认 2.0 次/秒)
pokemon-scraper scrape --rate 5.0

# 爬取特性描述
pokemon-scraper scrape-abilities
```

爬取过程支持 `Ctrl+C` 优雅中断，进度自动保存，下次运行时续爬。

### 2. 查看进度

```bash
pokemon-scraper status
```

### 3. CLI 浏览

```bash
# 交互式浏览
pokemon-scraper browse

# 搜索 (支持中/英/日文)
pokemon-scraper search 皮卡丘
pokemon-scraper search pikachu

# 查看详情
pokemon-scraper info 25
pokemon-scraper info pikachu

# 按条件筛选
pokemon-scraper filter --type fire
pokemon-scraper filter --gen 1 --sort total
pokemon-scraper filter --min-total 500 --sort speed --limit 10
```

### 4. 聊天机器人

```bash
pokemon-scraper chat
```

支持自然语言提问，例如：
- "最强的火系 Pokemon 是哪个？"
- "皮卡丘的种族值是多少？"
- "第一世代有哪些水系 Pokemon？"

### 5. Web 图鉴

```bash
pokemon-scraper web

# 自定义端口
pokemon-scraper web --port 8080 --debug
```

浏览器打开 `http://127.0.0.1:5000` 即可使用。

### 6. 导出数据

```bash
pokemon-scraper export-json --output pokemon.json
pokemon-scraper export-csv --output pokemon.csv
```

## 项目结构

```
src/
├── config.py              # 配置
├── models.py              # 数据模型
├── main.py                # CLI 入口
├── api/                   # PokeAPI 客户端
│   ├── client.py          # HTTP 客户端 (httpx async)
│   ├── endpoints.py       # API 端点
│   └── parsers.py         # 响应解析
├── db/                    # 数据库
│   ├── connection.py      # 连接管理
│   ├── schema.py          # 建表 / 迁移
│   ├── repository.py      # 写入操作
│   └── queries.py         # 查询操作
├── scraper/               # 爬虫
│   ├── pokemon_scraper.py # Pokemon 数据爬虫
│   ├── ability_scraper.py # 特性爬虫
│   ├── image_downloader.py# 图片下载器
│   └── progress.py        # 进度追踪
├── export/                # 数据导出
│   ├── json_export.py
│   └── csv_export.py
├── cli/                   # 命令行界面
│   ├── display.py         # 格式化输出
│   └── viewer.py          # 交互式浏览
├── chatbot/               # 聊天机器人
│   ├── rules.py           # 规则定义
│   ├── query_parser.py    # 查询解析
│   ├── query_handler.py   # 查询处理
│   ├── response_formatter.py # 回复格式化
│   └── chat_session.py    # 会话管理
└── web/                   # Web 图鉴
    ├── app.py             # Flask 应用
    ├── routes.py          # 路由
    ├── filters.py         # Jinja2 过滤器
    ├── helpers.py         # 分页等工具
    └── templates/         # HTML 模板
        ├── base.html
        ├── index.html
        └── detail.html
```

## 运行时数据

运行后会在 `data/` 目录下生成：

```
data/
├── pokemon.db             # SQLite 数据库
└── images/
    ├── artwork/           # 官方插图 (475x475)
    └── sprites/           # 像素图标 (96x96)
```

`data/` 目录不纳入版本控制，首次使用需运行 `pokemon-scraper scrape` 生成。

## 技术栈

- **Python 3.11+**
- **httpx** — 异步 HTTP 客户端 (HTTP/2)
- **SQLite** — 本地数据库
- **Flask** — Web 框架
- **tqdm** — 进度条

## License

MIT
