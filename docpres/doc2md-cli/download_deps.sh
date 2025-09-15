#!/bin/bash
# 使用Maven下载依赖到lib目录

echo "===== 使用Maven下载依赖 ====="

# 确保lib目录存在
mkdir -p lib

# 查找Maven命令
MVN_CMD=$(which mvn)
if [ -z "$MVN_CMD" ]; then
    if [ -f "/opt/homebrew/bin/mvn" ]; then
        MVN_CMD="/opt/homebrew/bin/mvn"
    elif [ -f "/usr/local/bin/mvn" ]; then
        MVN_CMD="/usr/local/bin/mvn"
    else
        echo "错误: 未找到Maven命令，请确保Maven已安装"
        echo "安装命令: brew install maven"
        exit 1
    fi
fi

echo "使用Maven: $MVN_CMD"

# 使用Maven下载依赖
echo "正在下载依赖到lib目录..."
"$MVN_CMD" dependency:copy-dependencies -DoutputDirectory=lib

echo "===== 依赖下载完成 ====="