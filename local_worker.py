import os
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 配置：支持从环境变量读取 Ollama 地址 (Docker 部署时使用)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBED_MODEL = "nomic-embed-text"
LOCAL_LLM = "qwen2.5:7b"

def get_retriever(db_path):
    """
    工厂函数：根据数据库路径，返回一个新的检索器
    """
    print(f"🔌 [Local Worker] 正在连接知识库: {db_path}")
    embeddings = OllamaEmbeddings(
        model=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL
    )
    vectorstore = Chroma(
        persist_directory=db_path, 
        embedding_function=embeddings
    )
    # 扩大搜索范围到 10
    return vectorstore.as_retriever(search_kwargs={"k": 10})

def get_grader_chain():
    """返回评分链对象 (无状态，可复用)"""
    llm = ChatOllama(
        model=LOCAL_LLM, 
        temperature=0, 
        format="json",
        base_url=OLLAMA_BASE_URL
    )

    prompt = ChatPromptTemplate.from_template(
        """你是一个严谨的文档评分员。
        请评估检索到的文档片段是否与用户的问题相关。
        如果文档包含相关关键词或语义，评分为 'yes'，否则为 'no'。
        必须输出严格的 JSON 格式：
        {{ "score": "yes" }} 或 {{ "score": "no" }}

        问题: {question}
        文档: {document}
        JSON 输出:
        """
    )
    return prompt | llm | JsonOutputParser()