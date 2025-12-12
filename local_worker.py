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
    # 扩大搜索范围到 50
    return vectorstore.as_retriever(search_kwargs={"k": 50})

def get_grader_chain():
    """返回评分链对象 (无状态，可复用)"""
    llm = ChatOllama(
        model=LOCAL_LLM, 
        temperature=0, 
        format="json",
        base_url=OLLAMA_BASE_URL
    )

    # 优化后的 Prompt：更宽容的评分策略 + 三级评分
    prompt = ChatPromptTemplate.from_template(
        """你是一个宽容的文档相关性评分员。你的任务是判断文档是否可能对回答问题有帮助。

评分标准（请倾向于保留文档）：
- "yes": 文档**直接相关**，包含能回答问题的关键信息
- "partial": 文档**间接相关**，包含背景信息、相关概念、或可能有用的上下文
- "no": 文档**完全无关**，与问题毫无关联

重要提示：
1. 如果文档来自同一项目/代码库，倾向于评为 "partial" 而非 "no"
2. 代码文件中的函数名、类名、变量名如果与问题相关，应评为 "yes" 或 "partial"
3. README、配置文件、注释通常包含有用上下文，倾向于保留

必须输出严格的 JSON 格式：
{{ "score": "yes" }} 或 {{ "score": "partial" }} 或 {{ "score": "no" }}

问题: {question}
文档: {document}
JSON 输出:
"""
    )
    return prompt | llm | JsonOutputParser()