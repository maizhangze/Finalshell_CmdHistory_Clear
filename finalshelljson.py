import json
import time
import re
from pathlib import Path
from datetime import datetime

# 原始文件路径
src_file = Path(r"C:\Users\admin\AppData\Local\finalshell\config.json")
# 新文件路径
dst_file = src_file.with_name("config_new.json")
# 12个月的秒数（按180天算）
twelve_months_sec = 180 * 24 * 60 * 60

def is_package_manager_output(text):
    """识别是否为包管理器的输出内容（非用户执行的命令）"""
    if not text or not isinstance(text, str):
        return False
    
    text = text.strip()
    
    # 定义包管理器输出的特征模式
    package_output_patterns = [
        # apt/dpkg 相关输出
        r'^\d+%\s*\[=+>?\s*\].*KB/s.*eta',  # 下载进度条
        r'^Get:\d+\s+http',  # apt下载信息
        r'^Hit:\d+\s+http',  # apt命中信息
        r'^Ign:\d+\s+http',  # apt忽略信息
        r'^Reading package lists',  # 读取包列表
        r'^Building dependency tree',  # 构建依赖树
        r'^Reading state information',  # 读取状态信息
        r'^The following .* will be',  # 将要安装/升级等
        r'^After this operation',  # 操作后磁盘使用
        r'^Do you want to continue\?',  # 确认提示
        r'^Unpacking.*\(.*\)',  # 解包信息
        r'^Setting up.*\(.*\)',  # 设置信息
        r'^Processing triggers for',  # 处理触发器
        r'^dpkg: warning:',  # dpkg警告
        r'^update-alternatives:',  # 更新alternatives
        
        # yum/rpm 相关输出
        r'^Installing\s*:.*\[#+.*\]',  # yum安装进度
        r'^Updating\s*:.*\[#+.*\]',  # yum更新进度
        r'^Erasing\s*:.*\[#+.*\]',  # yum卸载进度
        r'^->\s*Processing Dependency:',  # 处理依赖
        r'^->\s*Running transaction check',  # 运行事务检查
        r'^->\s*Finished Dependency Resolution',  # 完成依赖解析
        r'^Dependencies Resolved',  # 依赖已解决
        r'^Transaction Summary',  # 事务摘要
        r'^Total download size:',  # 总下载大小
        r'^Installed size:',  # 安装大小
        r'^Is this ok \[y/d/N\]:',  # 确认提示
        r'^Downloading packages:',  # 下载包
        r'^Running transaction',  # 运行事务
        r'^Verifying\s*:',  # 验证
        r'^Installed:$',  # 已安装（单独一行）
        r'^Updated:$',  # 已更新（单独一行）
        r'^Complete!$',  # 完成（单独一行）
        r'^warning:',  # rpm警告
        
        # 通用包管理器输出
        r'^\s*\d+\)\s+',  # 编号列表（如搜索结果）
        r'^\s*\*\s+',  # 星号开头的状态信息
        r'^\(Reading database',  # 读取数据库
        r'^Preparing to unpack',  # 准备解包
        r'^Selecting previously unselected',  # 选择之前未选择的包
        r'^Created symlink',  # 创建符号链接（systemd相关）
        r'^Synchronizing state',  # 同步状态
        r'systemctl daemon-reload',  # systemd重载（输出中的）
        
        # 错误和警告信息
        r'^E:\s+',  # apt错误信息
        r'^W:\s+',  # apt警告信息
        r'^Error:\s+',  # 通用错误
        r'^Warning:\s+',  # 通用警告
        r'^Note:\s+',  # 提示信息
        
        # 其他常见的非命令输出
        r'^\s*$',  # 空行
        r'^#+$',  # 纯井号行
        r'^=+$',  # 纯等号行
        r'^-+$',  # 纯减号行
    ]
    
    # 检查是否匹配任何模式
    for pattern in package_output_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # 检查是否包含典型的包管理器输出关键词
    package_keywords = [
        'KB/s', 'MB/s', 'eta', 'ETA',  # 下载速度和预计时间
        'Setting up', 'Unpacking', 'Processing triggers',  # apt动作
        'Installing :', 'Updating :', 'Erasing :',  # yum动作
        'Transaction Summary', 'Dependencies Resolved',  # yum事务
        'Reading package lists', 'Building dependency tree',  # apt状态
        'Do you want to continue', 'Is this ok',  # 确认提示
        'Created symlink', 'Reloading', 'daemon-reload',  # systemd相关
    ]
    
    for keyword in package_keywords:
        if re.search(rf'\b{re.escape(keyword)}\b', text, re.IGNORECASE):
            return True

    return False

def is_valid_command(text):
    """判断是否为有效的用户命令"""
    if not text or not isinstance(text, str):
        return False
    
    text = text.strip()
    
    # 空行不是有效命令
    if not text:
        return False
    
    # 如果是包管理器输出，不是有效命令
    if is_package_manager_output(text):
        return False
    
    # 移除了容易误判的 common_command_patterns 检查
    # 现在只要不是包管理器输出且不是空行，就认为是有效命令
    return True

# 读取 JSON 文件
with open(src_file, "r", encoding="utf-8") as f:
    data = json.load(f)

now_ts = time.time()  # 当前时间戳（秒）

def process_history(key):
    """处理 cmd_history 或 file_history"""
    deleted_entries = []
    invalid_entries = []  # 新增：记录无效的条目
    
    if key in data:
        new_list = []
        for entry in data[key]:
            active_time_ms = entry.get("active_time", 0)
            active_time_s = active_time_ms / 1000
            
            # 检查时间条件
            if (now_ts - active_time_s) > twelve_months_sec:
                deleted_entries.append(entry)
                continue
            
            # 对于 cmd_history，额外检查是否为有效命令
            if key == "cmd_history":
                text = entry.get("text", "")
                if not is_valid_command(text):
                    invalid_entries.append(entry)
                    continue
            
            new_list.append(entry)
        
        data[key] = new_list
    
    return deleted_entries, invalid_entries

# 处理 cmd_history
deleted_cmds, invalid_cmds = process_history("cmd_history")

# 处理 file_history
deleted_files, _ = process_history("file_history")  

# 显示删除信息
if deleted_cmds:
    print(f"cmd_history 总共删除了 {len(deleted_cmds)} 条记录（超过6个月）：")
    for e in deleted_cmds:
        t_str = datetime.fromtimestamp(e["active_time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        print(f"- 时间: {t_str} | 命令: {e.get('text', '')}")
else:
    print("cmd_history 没有超过6个月的记录需要删除。")

# 新增：显示无效命令删除信息
if invalid_cmds:
    print(f"\ncmd_history 删除了 {len(invalid_cmds)} 条无效记录（包管理器输出等）：")
    for e in invalid_cmds: 
        t_str = datetime.fromtimestamp(e["active_time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        print(f"- 时间: {t_str} | 内容: {e.get('text', '')}...") 

else:
    print("\ncmd_history 没有发现无效记录。")

if deleted_files:
    print(f"\nfile_history 总共删除了 {len(deleted_files)} 条记录（超过12个月）：")
    for e in deleted_files:
        t_str = datetime.fromtimestamp(e["active_time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        print(f"- 时间: {t_str} | 文件/目录: {e.get('text', '')}")
else:
    print("\nfile_history 没有记录需要删除。")

# 显示统计信息
print(f"\n=== 清理统计 ===")
print(f"cmd_history: 按时间删除 {len(deleted_cmds)} 条，按有效性删除 {len(invalid_cmds)} 条")
print(f"file_history: 按时间删除 {len(deleted_files)} 条")
print(f"总共删除 {len(deleted_cmds) + len(invalid_cmds) + len(deleted_files)} 条记录")

# 保存到新文件
with open(dst_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"\n处理完成，新文件已保存到: {dst_file}")

