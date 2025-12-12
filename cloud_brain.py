import os
# 继续保持代理白名单，防止 Kimi 连接受阻
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# --- 配置 ---
# 使用 Kimi (Moonshot)
CLOUD_LLM_MODEL = "moonshot-v1-8k" 

def build_generator_chain():
    """
    构建生成器链：Context + Question -> Answer
    """
    print("🧠 初始化云端大脑 (Kimi Generator)...")
    
    llm = ChatOpenAI(
        model=CLOUD_LLM_MODEL,
        temperature=0.3, # 稍微有点温度，让回答自然些
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE")
    )

    prompt = ChatPromptTemplate.from_template(
        """你是一个精通 Python 和开源项目的 AI 架构师。
        你将根据提供的【上下文代码】来回答用户的【问题】。
        
        如果在上下文中找不到答案，请直接诚实地说“我在提供的代码中找不到相关信息”，不要编造。
        请用专业、简洁的中文回答，并尽可能引用代码中的函数名或变量名。

        ---
        【上下文代码】:
        {context}
        ---
        【用户问题】:
        {question}
        ---
        【你的回答】:
        """
    )

    # 构造链: Prompt -> LLM -> String输出
    chain = prompt | llm | StrOutputParser()
    return chain

# 实例化
generator_chain = build_generator_chain()

if __name__ == "__main__":
    print("🚀 Cloud Brain 独立测试")
    
    # --- 模拟一个测试场景 ---
    # 假设 Local Worker 已经找到了这两个片段传给我们
    mock_context = """
    File: config.py
    class Config:
        def __init__(self):
            # 用户需要在这里填入 API Key
            self.api_key = os.getenv("GLM_API_KEY", "")
            self.base_url = "https://open.bigmodel.cn/api/paas/v4/"
    """
    
    mock_question = "我应该在环境变量里叫什么名字来配置 API Key？"
    
    print(f"\n❓ 模拟提问: {mock_question}")
    print(f"📄 模拟上下文: (包含 Config 类和 GLM_API_KEY)")
    print("-" * 30)
    
    try:
        print("💡 Kimi 正在思考...")
        response = generator_chain.invoke({
            "context": mock_context,
            "question": mock_question
        })
        print(f"\n✅ Kimi 回答:\n{response}")
    except Exception as e:
        print(f"❌ Kimi 调用失败: {e}")
        