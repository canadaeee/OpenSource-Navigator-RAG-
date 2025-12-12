import os
from typing import TypedDict, List
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
from cloud_brain import generator_chain
from local_worker import get_grader_chain

os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 定义状态
class GraphState(TypedDict):
    question: str
    documents: List[Document]
    generation: str
    # 新增：将 retriever 放入 state 中传递不太合适（因为它不是数据），
    # 但为了简单，我们采用闭包方式构建 Graph

def build_graph(retriever):
    """
    工厂函数：接收一个特定的 retriever，构建并编译一个新的 Graph
    """
    grader_chain = get_grader_chain()

    # --- 节点定义 (闭包内部) ---
    def retrieve(state):
        print("--- RETRIEVE ---")
        question = state["question"]
        documents = retriever.invoke(question)
        return {"documents": documents, "question": question}

    def grade_documents(state):
        print("--- GRADE ---")
        question = state["question"]
        documents = state["documents"]
        original_docs = documents.copy()  # 保留原始文档用于兜底
        
        yes_docs = []      # 直接相关
        partial_docs = []  # 间接相关
        
        for d in documents:
            try:
                score = grader_chain.invoke({"question": question, "document": d.page_content})
                grade = score.get("score", "no").lower()
                if grade == "yes":
                    yes_docs.append(d)
                elif grade == "partial":
                    partial_docs.append(d)
                # "no" 的文档直接丢弃
            except Exception as e:
                # 评分失败时，保守地将文档归入 partial
                print(f"⚠️ 评分异常，保留文档: {e}")
                partial_docs.append(d)
        
        # 兜底策略：优先 yes，其次 partial，最后用原始 Top-3
        if yes_docs:
            filtered_docs = yes_docs + partial_docs[:2]  # yes 全部 + 最多2个 partial
            print(f"✅ 使用 {len(yes_docs)} 个直接相关 + {min(len(partial_docs), 2)} 个间接相关文档")
        elif partial_docs:
            filtered_docs = partial_docs
            print(f"⚠️ 无直接相关文档，使用 {len(partial_docs)} 个间接相关文档")
        else:
            # 最终兜底：使用原始检索结果的前3个
            filtered_docs = original_docs[:3]
            print(f"🔄 兜底模式：使用原始检索的前 {len(filtered_docs)} 个文档")
        
        return {"documents": filtered_docs, "question": question}

    def generate(state):
        print("--- GENERATE ---")
        question = state["question"]
        documents = state["documents"]
        context = "\n\n".join([doc.page_content for doc in documents])
        generation = generator_chain.invoke({"context": context, "question": question})
        return {"documents": documents, "question": question, "generation": generation}

    def decide_to_generate(state):
        if not state["documents"]:
            return "end"
        return "generate"

    # --- 构建图 ---
    workflow = StateGraph(GraphState)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {"generate": "generate", "end": END}
    )
    workflow.add_edge("generate", END)

    return workflow.compile()