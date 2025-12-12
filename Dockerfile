# ===========================
# OpenSource Navigator Dockerfile
# 基于混合 RAG 架构的开源项目智能领航员
# ===========================

# 使用官方 Python 3.11 slim 镜像 (更轻量)
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Streamlit 配置
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    # 禁用本地代理干扰
    NO_PROXY=localhost,127.0.0.1

# 安装系统依赖
# - git: 用于克隆 GitHub 仓库
# - build-essential: 编译某些 Python 包可能需要
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY app.py .
COPY main.py .
COPY cloud_brain.py .
COPY graph_brain.py .
COPY ingest.py .
COPY local_worker.py .
COPY profiler.py .

# 可选：复制其他配置文件
COPY README.md .
COPY LICENSE .

# 创建必要的目录
RUN mkdir -p source_code chroma_db_store

# 暴露 Streamlit 端口
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 启动命令
# 使用 Streamlit 直接启动，而不是通过 main.py
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
