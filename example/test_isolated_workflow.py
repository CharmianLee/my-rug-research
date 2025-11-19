#!/usr/bin/env python3

import os
import subprocess
import tempfile
import shutil
import sys

def test_isolated_workflow():
    """测试非破坏性的隔离工作流"""
    
    # 确保我们在正确的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    # 创建一个测试目录结构
    test_project = "test_humantime"
    test_project_path = os.path.join(current_dir, test_project)
    
    # 如果测试目录已经存在，先删除它
    if os.path.exists(test_project_path):
        shutil.rmtree(test_project_path)
    
    # 复制 humantime 项目作为测试项目
    humantime_path = os.path.join(current_dir, "humantime")
    if os.path.exists(humantime_path):
        shutil.copytree(humantime_path, test_project_path)
        print(f"✓ 已创建测试项目：{test_project_path}")
    else:
        print(f"✗ 找不到源项目：{humantime_path}")
        return False
    
    # 记录原始文件的修改时间
    original_files = {}
    for root, dirs, files in os.walk(test_project_path):
        for file in files:
            file_path = os.path.join(root, file)
            original_files[file_path] = os.path.getmtime(file_path)
    
    print(f"✓ 记录了 {len(original_files)} 个原始文件的时间戳")
    
    # 运行修改后的 main.py
    print("🔄 开始运行隔离工作流...")
    try:
        result = subprocess.run([
            sys.executable, "main.py", test_project
        ], capture_output=True, text=True, timeout=60)
        
        print(f"📊 返回码: {result.returncode}")
        if result.stdout:
            print("📤 标准输出:")
            print(result.stdout[-500:])  # 只显示最后500个字符
        if result.stderr:
            print("📤 标准错误:")
            print(result.stderr[-500:])  # 只显示最后500个字符
            
    except subprocess.TimeoutExpired:
        print("⏰ 测试超时（60秒）")
        return False
    except Exception as e:
        print(f"✗ 运行时出错：{e}")
        return False
    
    # 检查原始文件是否被修改
    modified_files = []
    for file_path, original_time in original_files.items():
        if os.path.exists(file_path):
            current_time = os.path.getmtime(file_path)
            if abs(current_time - original_time) > 0.1:  # 允许小的浮点误差
                modified_files.append(file_path)
    
    if modified_files:
        print(f"✗ 发现 {len(modified_files)} 个文件被修改（不应该发生）:")
        for file_path in modified_files[:5]:  # 只显示前5个
            print(f"  - {file_path}")
        return False
    else:
        print("✓ 所有原始文件都未被修改")
    
    # 清理测试项目
    shutil.rmtree(test_project_path)
    print(f"✓ 已清理测试项目：{test_project_path}")
    
    return True

def test_temp_directory_cleanup():
    """测试临时目录是否正确清理"""
    
    # 获取临时目录的数量（在运行之前）
    temp_base = tempfile.gettempdir()
    rug_temps_before = [d for d in os.listdir(temp_base) if d.startswith("rug_work_")]
    
    print(f"📊 运行前的 rug 临时目录数量: {len(rug_temps_before)}")
    
    # 运行一个快速测试
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    test_project = "humantime"  # 使用现有的项目
    if not os.path.exists(test_project):
        print(f"✗ 测试项目不存在：{test_project}")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, "main.py", test_project
        ], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        print("⏰ 清理测试超时")
    except Exception as e:
        print(f"清理测试出错: {e}")
    
    # 检查临时目录数量（在运行之后）
    rug_temps_after = [d for d in os.listdir(temp_base) if d.startswith("rug_work_")]
    
    print(f"📊 运行后的 rug 临时目录数量: {len(rug_temps_after)}")
    
    # 理想情况下，运行后的临时目录数量应该和运行前一样
    if len(rug_temps_after) <= len(rug_temps_before):
        print("✓ 临时目录正确清理")
        return True
    else:
        print("⚠️ 可能存在临时目录泄露")
        for temp_dir in rug_temps_after:
            if temp_dir not in rug_temps_before:
                print(f"  - 新增临时目录: {temp_dir}")
        return False

if __name__ == "__main__":
    print("🧪 测试隔离工作流...")
    print("=" * 60)
    
    success1 = test_isolated_workflow()
    print("")
    success2 = test_temp_directory_cleanup()
    
    print("=" * 60)
    if success1 and success2:
        print("🎉 所有测试通过！隔离工作流正常工作。")
        sys.exit(0)
    else:
        print("❌ 部分测试失败。")
        sys.exit(1)