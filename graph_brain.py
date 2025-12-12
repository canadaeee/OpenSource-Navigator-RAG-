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
        filtered_docs = []
        for d in documents:
            score = grader_chain.invoke({"question": question, "document": d.page_content})
            if score.get("score") == "yes":
                filtered_docs.append(d)
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