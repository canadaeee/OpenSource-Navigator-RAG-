import os
import re
import shutil
import subprocess
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

# 代理配置
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 配置：支持从环境变量读取 Ollama 地址 (Docker 部署时使用)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBED_MODEL = "nomic-embed-text"
# 根存储目录
DB_ROOT = "chroma_db_store"
SOURCE_ROOT = "source_code"

# ==========================================
# 🛡️ 安全：GitHub URL 验证
# ==========================================
def is_valid_git_url(url):
    """
    验证 Git 仓库 URL 格式，防止命令注入
    支持 GitHub, GitLab, Gitee 等主流平台
    """
    # 允许的 Git URL 模式
    patterns = [
        r'^https?://github\.com/[\w\-\.]+/[\w\-\.]+/?$',
        r'^https?://gitlab\.com/[\w\-\.]+/[\w\-\.]+/?$',
        r'^https?://gitee\.com/[\w\-\.]+/[\w\-\.]+/?$',
        r'^https?://bitbucket\.org/[\w\-\.]+/[\w\-\.]+/?$',
        r'^git@github\.com:[\w\-\.]+/[\w\-\.]+\.git$',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url.strip()):
            return True
    return False

def get_project_name(url):
    """从 GitHub URL 提取项目名称"""
    return url.split("/")[-1].replace(".git", "")

def clone_repo(url, target_dir):
    """克隆或更新代码库"""
    # 如果目录存在，先删除（确保干净的克隆）
    if os.path.exists(target_dir):
        print(f"⚠️ 正在清理旧目录 {target_dir} 以进行重新克隆...")
        try:
            shutil.rmtree(target_dir)
        except Exception as e:
            print(f"⚠️ 删除失败 (可能被占用): {e}")

    print(f"⬇️ 正在克隆 {url}...")
    try:
        subprocess.run(["git", "clone", url, target_dir], check=True)
        return True
    except Exception as e:
        print(f"❌ 克隆失败: {e}")
        return False

def ingest_project(project_url, force_update=False):
    """
    主入口
    :param project_url: GitHub 地址
    :param force_update: 是否强制重新下载并向量化
    """
    # 🛡️ 安全检查：验证 URL 格式
    if not is_valid_git_url(project_url):
        print(f"❌ 无效的 Git URL: {project_url}")
        return None, "Invalid URL: Only GitHub/GitLab/Gitee/Bitbucket URLs are allowed"
    
    project_name = get_project_name(project_url)
    
    source_path = os.path.join(SOURCE_ROOT, project_name)
    db_path = os.path.join(DB_ROOT, project_name)
    
    print(f"🚀 开始处理项目: {project_name}")

    # --- [关键优化] 智能缓存检查 ---
    # 如果数据库存在，且用户没有要求强制更新，直接返回现有数据库
    if os.path.exists(db_path) and not force_update:
        print(f"✅ 发现现有向量库: {db_path}")
        print(f"⏩ 跳过下载与计算，直接加载缓存。")
        return db_path, "Cached: Loaded existing database"

    # --- 以下是原有逻辑 (下载 + 计算) ---
    
    # 1. 下载代码
    if not clone_repo(project_url, source_path):
        return None, "Clone Failed"

    # 2. 加载文件
    print("📂 正在扫描文件...")
    documents = []
    # 增加了一些常见后缀
    file_patterns = ["**/*.py", "**/*.md", "**/*.js", "**/*.ts", "**/*.java", "**/*.go", "**/*.txt", "**/*.yaml"]
    
    for pattern in file_patterns:
        try:
            loader = DirectoryLoader(
                source_path, glob=pattern, loader_cls=TextLoader,
                silent_errors=True,
                loader_kwargs={'encoding': 'utf-8', 'autodetect_encoding': True}
            )
            documents.extend(loader.load())
        except Exception:
            pass
            
    if not documents:
        return None, "No Documents Found"

    # 3. 切分
    print("✂️ 正在切分...")
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON, chunk_size=1500, chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)
    
    # 4. 向量化 (如果有旧库，先清理，防止数据重复叠加)
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    print(f"💾 正在计算向量并存入: {db_path}...")
    embeddings = OllamaEmbeddings(
        model=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL
    )
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=db_path
    )
    
    return db_path, f"Success: Processed {len(chunks)} new chunks"

def list_existing_projects():
    """列出已经存在的项目数据库"""
    if not os.path.exists(DB_ROOT):
        os.makedirs(DB_ROOT)
        return []
    # 扫描文件夹，只返回目录名
    projects = [d for d in os.listdir(DB_ROOT) if os.path.isdir(os.path.join(DB_ROOT, d))]
    return projects