import os
import sys
import subprocess
import time

def start_application():
    """
    Project Synapse 统一启动入口
    自动调用 Streamlit 启动 Web UI
    """
    # 1. 获取当前脚本所在的目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 定位 app.py 的路径
    app_path = os.path.join(base_dir, "app.py")
    
    # 3. 检查 app.py 是否存在
    if not os.path.exists(app_path):
        print(f"❌ 错误: 找不到文件 {app_path}")
        print("   请确保 main.py 和 app.py 在同一个文件夹下。")
        return

    print(f"📂 工作目录: {base_dir}")
    print("⚡ 正在启动 Web 界面...")


    # 4. 构建启动命令
    # 使用 sys.executable 确保使用当前虚拟环境的 Python 解释器
    # 相当于执行: python -m streamlit run app.py
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]

    try:
        # 5. 执行命令
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止。再见！")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")

if __name__ == "__main__":
    start_application()