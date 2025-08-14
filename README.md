# Finalshell_CmdHistory_Clear
**Finalshell 历史命令清理工具**  

使 Finalshell 查看和检索历史命令时不卡顿
删除 Finalshell 中过时的历史命令，或误记录的命令输出内容。  

## 功能特点
- **自动清理过期命令**：删除指定天数以前的历史命令（默认 180 天）。
- **过滤误记录的命令输出**：去除误判为命令的包管理器输出、日志片段等。
- **生成新配置文件**：保留有效记录并输出为 `config_new.json`，避免直接覆盖原文件。


## 使用方法

关闭finalshell

找到并修改以下代码中的路径，确保与自己 Finalshell 安装路径一致：

src_file = Path(r"C:\Users\admin\AppData\Local\finalshell\config.json")

修改历史保留天数（可选）
修改以下参数即可更改保留时间（单位：秒）：

twelve_months_sec = 180 * 24 * 60 * 60  # 默认 180 天

运行脚本

python Finalshell_CmdHistory_Clear.py

替换配置文件

脚本运行后会生成 config_new.json

请在关闭 Finalshell 的情况下，将其替换原 config.json

