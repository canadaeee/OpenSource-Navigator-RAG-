import os
# ==========================================
# 🛡️ 关键修复：防止 VPN/代理 拦截本地流量
# ==========================================
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
# ==========================================

import time
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

load_dotenv()

def test_cloud_brain():
    """测试云端大脑 (Kimi)"""
    print("🌐 [1/3] 正在呼叫云端大脑 (Kimi)...")
    try:
        llm = ChatOpenAI(
            model="moonshot-v1-8k",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE")
        )
        response = llm.invoke([HumanMessage(content="Hello Kimi.")])
        print(f"✅ Kimi 响应成功: {response.content}")
        return True
    except Exception as e:
        print(f"❌ Kimi 连接失败: {e}")
        return False

def debug_ollama_raw():
    """底层接口诊断"""
    print("\n🔍 [2/3] 正在进行 Ollama 底层接口诊断...")
    try:
        url = "http://127.0.0.1:11434/api/generate"
        payload = {"model": "qwen2.5:7b", "prompt": "hi", "stream": False}
        # 保持 30秒 超时
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            print("✅ Ollama 底层接口通畅 (HTTP 200)")
            return True
        else:
            print(f"❌ Ollama 接口报错: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama 底层连接失败: {e}")
        return False

def test_local_worker():
    """测试本地工兵 (LangChain Wrapper)"""
    print("\n🏠 [3/3] 正在呼叫本地工兵 (LangChain Wrapper)...")
    try:
        # 这里依然保持显式指定 base_url
        llm = ChatOllama(
            model="qwen2.5:7b",
            temperature=0.1,
            base_url="http://127.0.0.1:11434"
        )
        
        t0 = time.time()
        response = llm.invoke([HumanMessage(content="Ready?")])
        t1 = time.time()
        
        print(f"✅ Local Worker 响应成功: {response.content}")
        print(f"⚡ 耗时: {t1-t0:.2f}秒")
        return True
    except Exception as e:
        print(f"❌ Local Worker (LangChain) 失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 OpenSource Navigator - 最终连通性测试")
    print("="*50)
    
    cloud_ok = test_cloud_brain()
    raw_ok = debug_ollama_raw()
    
    if raw_ok:
        local_ok = test_local_worker()
    else:
        local_ok = False
    
    print("\n" + "="*50)
    if cloud_ok and local_ok:
        print("🎉 Phase 1 完美通关！混合架构已就绪。")
    else:
        print("⚠️ 仍有故障，请继续反馈。")