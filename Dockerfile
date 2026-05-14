FROM python:3.11-slim

WORKDIR /app

# 复制依赖文件
COPY requirements_llm.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements_llm.txt

# 复制项目文件
COPY . .

# 暴露端口（Railway会自动设置PORT环境变量）
EXPOSE 8080

# 创建启动脚本
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'export PORT=${PORT:-8080}' >> /app/start.sh && \
    echo 'python ai-project-main.py' >> /app/start.sh && \
    chmod +x /app/start.sh

# 启动命令
CMD ["/app/start.sh"]
