FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口（Zeabur 会自动映射到正确的端口）
EXPOSE 8080

# 启动命令 - 使用 Python 脚本启动以便读取环境变量
CMD ["python", "main.py"]