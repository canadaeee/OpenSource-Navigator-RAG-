import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 保持代理白名单
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

load_dotenv()

# 项目根目录配置
SOURCE_ROOT = "source_code"
DB_ROOT = "chroma_db_store"

def get_readme_content(project_name):
    """
    尝试读取项目的 README 文件
    """
    project_path = os.path.join(SOURCE_ROOT, project_name)
    
    # 常见的 README 文件名
    possible_names = ["README.md", "readme.md", "README.rst", "README.txt", "README_en.md"]
    
    for name in possible_names:
        file_path = os.path.join(project_path, name)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    # 只读取前 3000 字符，既省钱又能覆盖核心介绍
                    return f.read()[:3000]
            except Exception:
                continue
    return None

def generate_suggestions(project_name):
    """
    核心功能：生成建议问题
    1. 先检查有没有缓存的 questions.json
    2. 如果没有，读取 README 并调用 Kimi 生成
    3. 保存缓存并返回
    """
    
    # 1. 检查缓存
    cache_path = os.path.join(DB_ROOT, project_name, "questions.json")
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                print(f"⚡ [Profiler] 加载缓存的建议问题: {project_name}")
                return json.load(f)
        except Exception as e:
            print(f"⚠️ [Profiler] 缓存读取失败，将重新生成: {e}")

    # 2. 获取 README 内容
    print(f"🧠 [Profiler] 正在分析项目文档以生成建议...")
    readme_content = get_readme_content(project_name)
    
    if not readme_content:
        # 如果连 README 都没有，返回通用问题
        return ["如何安装依赖？", "项目的主入口文件是哪个？", "如何运行测试？"]

    # 3. 调用 Cloud Brain (Kimi)
    try:
        llm = ChatOpenAI(
            model="moonshot-v1-8k",
            temperature=0.5, # 稍微高一点，增加创造性
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE")
        )

        prompt = ChatPromptTemplate.from_template(
            """你是一个资深的开源项目分析师。
            请根据以下的项目 README 内容，为开发者提出 4 个最有价值的入门技术问题。
            
            问题应该关注：安装配置、核心功能使用、架构逻辑或部署方式。
            请直接输出问题列表，每行一个问题，不要带序号，不要带其他废话。
            
            ---
            README 摘要:
            {context}
            ---
            建议问题列表:
            """
        )

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"context": readme_content})
        
        # 处理结果：按行分割，过滤空行
        questions = [q.strip().replace("- ", "").replace("1. ", "") for q in result.split("\n") if q.strip()]
        # 取前 4 个
        questions = questions[:4]

        # 4. 写入缓存
        # 确保存储目录存在
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False)
            
        return questions

    except Exception as e:
        print(f"❌ [Profiler] 生成建议失败: {e}")
        return ["这个项目的主要功能是什么？", "如何快速开始？"]
        