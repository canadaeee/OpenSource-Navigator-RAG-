import streamlit as st
import os
from ingest import ingest_project, get_project_name, list_existing_projects
from local_worker import get_retriever
from graph_brain import build_graph
# --- 新增引入 ---
from profiler import generate_suggestions

st.set_page_config(page_title="OpenSource Navigator", page_icon="🧭", layout="wide")

st.title("🧭 OpenSource Navigator")

# --- Session State 初始化 ---
if "current_project" not in st.session_state:
    st.session_state["current_project"] = None
if "graph_app" not in st.session_state:
    st.session_state["graph_app"] = None
if "messages" not in st.session_state:
    st.session_state["messages"] = []
# 新增：用于存储建议问题
if "suggested_questions" not in st.session_state:
    st.session_state["suggested_questions"] = []

# 定义一个回调函数，处理点击建议问题
def set_question(question_text):
    st.session_state["prompt_trigger"] = question_text

# ================= 侧边栏 =================
with st.sidebar:
    st.header("🗂️ 项目控制台")
    tab1, tab2 = st.tabs(["📚 已有项目", "➕ 导入新项目"])
    
    # 辅助函数：加载项目后的通用逻辑
    def load_project_logic(proj_name):
        db_path = os.path.join("chroma_db_store", proj_name)
        new_retriever = get_retriever(db_path)
        st.session_state["graph_app"] = build_graph(new_retriever)
        st.session_state["current_project"] = proj_name
        st.session_state["messages"] = [{"role": "assistant", "content": f"项目 **{proj_name}** 已就绪！"}]
        
        # --- 关键：调用 Profiler 生成建议 ---
        with st.spinner("🧠 正在查看文档并提供建议..."):
            suggestions = generate_suggestions(proj_name)
            st.session_state["suggested_questions"] = suggestions
        
        st.success(f"✅ 已加载: {proj_name}")

    with tab1:
        existing_projects = list_existing_projects()
        if existing_projects:
            selected_project = st.selectbox("选择已处理的项目:", existing_projects)
            if st.button("🚀 立即加载", key="btn_load_existing"):
                load_project_logic(selected_project)
                st.rerun()

    with tab2:
        repo_url = st.text_input("GitHub URL:", placeholder="https://github.com/user/repo")
        force_update = st.checkbox("强制重新下载并处理")
        if st.button("📥 开始导入", key="btn_import"):
            if repo_url:
                proj_name = get_project_name(repo_url)
                st.info(f"正在处理: {proj_name} ...")
                db_path, msg = ingest_project(repo_url, force_update=force_update)
                if db_path:
                    load_project_logic(proj_name)
                    st.rerun()
                else:
                    st.error(f"❌ 失败: {msg}")

    st.markdown("---")
    if st.session_state["current_project"]:
        st.write(f"🟢 当前: **{st.session_state['current_project']}**")

# ================= 主界面 =================

if not st.session_state["graph_app"]:
    st.info("👋 欢迎使用Github部署智能顾问")
else:
    # --- 1. 显示建议问题区 (如果有) ---
    if st.session_state["suggested_questions"]:
        st.caption("💡 您可能想问：")
        # 创建多列布局
        for i, q in enumerate(st.session_state["suggested_questions"]):
            if st.button(q, key=f"sugg_{i}", use_container_width=True):
                # 只有点击时才触发
                set_question(q)
                st.rerun() # 强制刷新以将问题填入输入逻辑

    # --- 2. 显示聊天记录 ---
    st.divider()
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # --- 3. 处理输入 (包含手动输入和按钮触发) ---
    # 检查是否有按钮触发的输入
    user_input = None
    if "prompt_trigger" in st.session_state and st.session_state["prompt_trigger"]:
        user_input = st.session_state["prompt_trigger"]
        # 消费掉这个 trigger，防止循环
        del st.session_state["prompt_trigger"]
    
    # 同时也接受普通的聊天框输入
    chat_input = st.chat_input("请输入您的问题...")
    if chat_input: 
        user_input = chat_input

    # 如果有输入（无论是点的还是写的）
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        with st.chat_message("assistant"):
            status_container = st.status("🧠 正在思考...", expanded=True)
            app = st.session_state["graph_app"]
            final_answer = ""
            
            try:
                # 运行 Graph
                for output in app.stream({"question": user_input}):
                    for key, value in output.items():
                        if key == "retrieve":
                            status_container.write(f"🔍 检索到 {len(value['documents'])} 个片段")
                        elif key == "grade_documents":
                            n = len(value["documents"])
                            if n > 0:
                                status_container.write(f"✅ 评分保留 {n} 个有效片段")
                            # 注意：由于兜底机制，这里不再提前结束流程
                            # 即使评分后文档较少，也会尝试生成回答
                        elif key == "generate":
                            status_container.write("💡 Kimi 正在生成回答...")
                            final_answer = value["generation"]
                
                status_container.update(label="完成", state="complete", expanded=False)
                if final_answer:
                    st.markdown(final_answer)
                    st.session_state.messages.append({"role": "assistant", "content": final_answer})
            
            except Exception as e:
                st.error(f"出错: {e}")