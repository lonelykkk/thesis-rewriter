# 论文降重降AI助手

为大学生毕业论文设计的智能降重与降AI检测工具。支持 **本地规则引擎 + AI增强** 双引擎模式，内置用户认证、历史记录管理、自定义改写Skill等完整功能。

---

## 功能特色

- **智能降重**：同义词替换 + 句式变换 + 词语调整，有效降低查重率
- **去AI味处理**：打破AI生成文本的规整结构，添加人性化表达，降低AI检测率
- **三种处理模式**：全面优化 / 仅降重 / 仅降AI，灵活覆盖不同场景
- **本地规则引擎**：内置 110+ 组学术同义词库与4类规则策略，无需网络即可使用
- **AI增强改写**：可选配置 DeepSeek / OpenAI 等兼容 API，获得更高质量的改写效果
- **自定义 Skill Prompt**：自由注入 System Prompt，最高优先级覆盖内置提示词
- **用户认证系统**：注册登录、独立配置存储、用户级历史记录
- **改写历史管理**：自动保存每次改写记录，支持分页浏览、重命名、删除
- **双栏对比预览**：原文与改写后左右对照，改动条目逐条高亮显示
- **数据安全**：密码 Werkzeug 哈希加密，API Key 仅存数据库不暴露

---

## 快速开始

### 1. 安装依赖

```bash
cd thesis-rewriter
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

访问 http://localhost:5000

### 3. （可选）配置 AI API

复制 `.env.example` 为 `.env`，填写全局 API 密钥（也可登录后在 `/settings` 页面单独配置）：

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
AI_API_KEY=your-api-key
AI_API_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat
DATABASE_URL=sqlite:///thesis_rewriter.db
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML + Tailwind CSS (CDN) + 原生 JavaScript |
| 后端 | Python Flask 3.1.0 |
| 数据库 | SQLite + Flask-SQLAlchemy 3.1.1 |
| 用户认证 | Flask-Login 0.6.3 + Werkzeug 密码加密 |
| 文本处理 | jieba 0.42.1 分词 + 自定义同义词词典 |
| AI 增强 | OpenAI 协议兼容 API（openai 1.68.0，支持 DeepSeek 等） |
| 配置管理 | python-dotenv 1.1.0 |

---

## 处理模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 全面优化 | 降重 + 降AI 同时进行 | 通用推荐 |
| 仅降重 | 同义词替换 + 句式变换 + 词语调整 | 查重率较高时 |
| 仅降AI | 添加过渡词、限定表达、研究者视角等 | AI 检测率较高时 |

---

## 双引擎架构

```
用户请求 (text + mode)
        │
   ┌────┴────┐
   │         │
有 API Key  无 API Key
   │         │
   ▼         ▼
 AI 引擎    本地引擎
 (API改写)  (规则改写)
   │         │
   └────┬────┘
        │
        ▼
   返回结果
 (original + rewritten + changes)
```

### AI 引擎

- **触发条件**：用户配置了 `api_key`（优先级：用户设置 > 全局环境变量 > 无 Key 走本地）
- 使用 `openai` SDK 调用兼容接口
- 按 mode 选择 system prompt，**如果用户配置了 `custom_skill_prompt`，则完全取代内置 prompt**
- API 调用失败时自动降级到本地引擎

### 本地引擎

无 API Key 时自动启用，依次对每个句子应用以下策略：

1. **同义词替换** — jieba 分词后在 110+ 组学术同义词中随机替换（70% 概率，跳过核心术语）
2. **句式变换** — "是...的" 句式变体、把/被字句转换、"对...进行..." 合并
3. **词语调整** — 删除冗余副词、概率添加 "该/相关/本文" 等修饰
4. **降 AI 人性化** — 插入过渡词、打破规整并列（第一→首先）、添加限定表达（是→通常是）、插入研究者视角（本研究认为等）

---

## 路由一览

### 认证（无需登录）

| 方法 | 路由 | 说明 |
|------|------|------|
| GET/POST | `/login` | 登录 |
| GET/POST | `/register` | 注册（用户名≥2、邮箱含@、密码≥6位） |
| GET | `/logout` | 注销 |

### 核心功能（需登录）

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/` | 首页 — 文本输入区 |
| POST | `/rewrite` | 核心改写 API — 接收 `{text, mode}` JSON，返回结果 |
| GET | `/compare` | 结果双栏对比页（支持 `record_id` 或 URL 参数） |
| GET/POST | `/settings` | 设置页 — API 配置 + 自定义 Skill Prompt |

### 历史记录 API（需登录，返回 JSON）

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/history` | 历史列表（分页，参数：`page`、`per_page`） |
| GET | `/api/history/<id>` | 单条历史详情 |
| POST | `/api/history/<id>/rename` | 重命名记录 |
| DELETE | `/api/history/<id>` | 删除记录 |

---

## 设置与自定义 Skill

### AI 模型配置（`/settings`）

- **API Key** — 支持 DeepSeek / OpenAI 等任意兼容接口
- **API 地址** — 默认为 `https://api.deepseek.com/v1`
- **模型名称** — 默认为 `deepseek-chat`

### 自定义改写 Skill（Prompt）

- 自由编辑 System Prompt，AI 改写时作为 system 消息
- 配置优先级：**自定义 prompt > 内置 mode prompt**
- 内置快捷模板：
  - **深度降重** — 同义替换 + 句式变换 + 语序调整 + 术语保护
  - **专注降AI** — 打破规整结构 + 过渡词 + 限定表达 + 研究者视角
  - **学术润色** — 用词精准 + 逻辑连贯 + 简洁凝练 + 语气客观

---

## 项目结构

```
thesis-rewriter/
├── app.py                    # Flask 应用主入口（路由、认证、数据库迁移）
├── config.py                 # 应用配置
├── models.py                 # 数据库模型（User、RewriteRecord）
├── requirements.txt          # Python 依赖
├── .env.example              # 环境变量模板
├── .gitignore
├── README.md
│
├── templates/                # Jinja2 模板
│   ├── base.html             # 基础布局（导航栏 + 页脚）
│   ├── login.html            # 登录页
│   ├── register.html         # 注册页
│   ├── index.html            # 首页（文本输入 + 历史记录）
│   ├── result.html           # 结果页（双栏对比 + 改动详情）
│   └── settings.html         # 设置页（API 配置 + 自定义 Skill）
│
├── static/
│   ├── css/
│   │   └── style.css         # 自定义样式
│   └── js/
│       └── main.js           # 前端交互逻辑（字数统计、Ctrl+Enter、历史管理等）
│
├── services/
│   ├── __init__.py
│   ├── rewriter.py           # 核心改写引擎（AI + 本地双引擎）
│   └── synonym_dict.py       # 同义词词典（110+ 组学术词汇 + 4类句式模板）
│
└── docs/
    └── api.md                # API 参考文档
```

---

## 使用建议

1. 建议每次处理一个章节（摘要、引言、方法论等），效果更佳
2. 处理后请逐句核实，确保专业术语和核心论点未被改变
3. 本工具仅作为辅助参考，最终文稿请自行审校
4. 请遵守所在院校的学术规范与道德准则

---

## 注意事项

- 本工具仅用于学术辅助，请遵守所在院校的学术规范
- 建议在使用后进行人工校对
- 请勿将改写后的文本直接提交为原创内容

---

## License

MIT
