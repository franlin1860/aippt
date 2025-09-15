#!/bin/bash
# doc2md启动脚本

# 获取Java路径
JAVA_HOME=$(/usr/libexec/java_home)
export JAVA_HOME

# 设置库路径
export DYLD_LIBRARY_PATH="$JAVA_HOME/lib/server:$DYLD_LIBRARY_PATH"

# 运行Python脚本
python3 "$(dirname "$0")/doc2md.py" "$@"