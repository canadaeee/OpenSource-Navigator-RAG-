# 🧭 OpenSource Navigator (Project Synapse)

> **基于混合 RAG 架构的开源项目智能部署助手**
>
> _Hybrid RAG Agent for Analyzing Open Source Repositories_

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![Models](https://img.shields.io/badge/Models-Kimi%20%2B%20Qwen-green)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**OpenSource Navigator** 是一个高性能的本地化代码分析与问答系统。它采用独特的 **"Local Worker + Cloud Brain"** 混合架构，旨在帮助开发者快速理解、部署和调试复杂的 GitHub 开源项目。

---

## ✨ 核心特性 (Key Features)

- **🧠 混合双脑架构 (Hybrid Brain Architecture)**
  - **☁️ Cloud Brain (Kimi/Moonshot):** 负责最终的复杂逻辑推理、代码解释和答案生成。
  - **🏠 Local Worker (Ollama + Qwen 2.5):** 负责隐私敏感的检索、文档分级 (Grading) 和无关内容过滤。
- **🛡️ 智能过滤与省钱模式**
  - 本地模型充当“守门员”，自动过滤掉检索到的无关代码片段，确保只有高质量上下文被发送到云端，大幅节省 API Token 成本。
- **🕸️ LangGraph 神经编排**
  - 基于图 (Graph) 的工作流：`Retrieve` -> `Grade` -> `Decide` -> `Generate`。
  - UI 实时展示思维链，你可以看到系统是“决定生成回答”还是“因无据可查而保持沉默”。
- **🗂️ 多项目动态管理**
  - 支持输入任意 GitHub URL 自动克隆、切分并向量化。
  - 支持在多个已处理的项目间秒级切换。
- **💡 智能画像师 (Auto Profiler)**
  - 加载项目时，系统会自动阅读 `README`，并为你生成 4 个最具价值的建议提问（如安装配置、核心功能等）。

---

## 🛠️ 技术栈 (Tech Stack)

- **Orchestration:** LangGraph, LangChain
- **Frontend:** Streamlit (Web UI)
- **Local LLM:** Ollama (运行 `qwen2.5:7b` 和 `nomic-embed-text`)
- **Cloud LLM:** Kimi (Moonshot AI) / OpenAI Compatible API
- **Vector DB:** ChromaDB (Local Persisted)
- **OS:** Windows 11 / Linux / Mac (针对 Windows 代理做了特别优化)

---

## 🚀 快速开始 (Quick Start)

### 1. 环境准备

确保你已安装 Python 3.10+，并已安装 [Ollama](https://ollama.com/)。

**拉取本地模型：**

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

_(注：如果还没有 requirements.txt，请安装以下库)_

```bash
pip install streamlit langchain langchain-community langchain-openai langchain-ollama langchain-chroma langgraph python-dotenv
```

### 3. 配置密钥

在项目根目录下 `.env` 文件，填入你的云端 API Key：

```env
# .env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_BASE=https://api.moonshot.cn/v1
```

### 4. 启动系统

使用我们内置的启动器，一键运行 Web 界面：

```bash
python main.py
```

---

## 📖 使用指南

1.  **启动界面：** 浏览器会自动打开 `http://localhost:8501`。
2.  **导入项目：**
    - 点击侧边栏的 **"➕ 导入新项目"**。
    - 粘贴 GitHub 仓库地址（例如 `https://github.com/zai-org/Open-AutoGLM`）。
    - 点击 **"📥 开始导入"**。系统会自动下载代码并构建本地知识库。
3.  **智能提问：**
    - 导入成功后，主界面上方会出现 **"欢迎使用 Github 部署智能顾问"** 的按钮列表。
    - 点击任意按钮，或在下方输入框自由提问。
4.  **观察思考过程：**
    - 点击聊天框中的 `🧠 正在思考...` 折叠面板，查看 Local Worker 如何检索和评分。

---

## 📂 项目结构

```text
OpenSource-Navigator/
├── main.py              # 🚀 统一启动入口
├── app.py               # 🖥️ Streamlit 前端界面
├── graph_brain.py       # 🧠 LangGraph 核心编排逻辑
├── local_worker.py      # 🏠 本地工兵 (Ollama 连接与评分)
├── cloud_brain.py       # ☁️ 云端大脑 (Kimi 连接与生成)
├── ingest.py            # 📥 数据摄取、切分与向量化
├── profiler.py          # 💡 智能画像师 (生成建议问题)
├── .env                 # 🔑 配置文件
├── source_code/         # 📂 存放克隆下来的源代码
└── chroma_db_store/     # 💾 本地向量数据库存储
```

---

## ⚠️ 常见问题 (Troubleshooting)

**Q: 报错 `WinError 10054` 或 `Connection refused`？**

- **A:** 请确保 Ollama 桌面端正在运行。代码中已内置 `NO_PROXY` 配置以解决 Windows 下的 localhost 代理冲突问题，无需手动关闭 VPN。

**Q: 为什么评分阶段显示 "🚫 无相关文档"？**

- **A:** 这说明本地模型认为检索到的片段与你的问题无关。为了节省 Token，系统自动终止了流程。你可以尝试换一种提问方式。

---

## 🐳 Docker 部署

### 方式一：Docker Compose (推荐)

一键启动 Navigator + Ollama 完整环境：

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 Moonshot API Key

# 2. 启动服务
docker-compose up -d

# 3. 拉取本地模型 (首次运行需要)
docker exec -it ollama ollama pull qwen2.5:7b
docker exec -it ollama ollama pull nomic-embed-text

# 4. 访问 Web 界面
# 打开浏览器访问 http://localhost:8501
```

### 方式二：仅构建应用镜像

如果你已有 Ollama 服务运行：

```bash
# 构建镜像
docker build -t opensource-navigator .

# 运行容器
docker run -d \
  -p 8501:8501 \
  -e OPENAI_API_KEY=your_key \
  -e OPENAI_API_BASE=https://api.moonshot.cn/v1 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v $(pwd)/chroma_db_store:/app/chroma_db_store \
  -v $(pwd)/source_code:/app/source_code \
  opensource-navigator
```

### 环境变量说明

| 变量名            | 必填 | 说明                                           |
| ----------------- | ---- | ---------------------------------------------- |
| `OPENAI_API_KEY`  | ✅   | Moonshot (Kimi) API 密钥                       |
| `OPENAI_API_BASE` | ✅   | API 地址，默认为 Moonshot                      |
| `OLLAMA_BASE_URL` | ❌   | Ollama 服务地址，默认 `http://127.0.0.1:11434` |
