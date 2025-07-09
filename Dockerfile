# Dockerfile
FROM python:3.10-slim-buster

# タイムゾーンの設定（必要であれば）
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# 必要なシステムパッケージをインストール（後述のgRPCのため）
# gRPCのインストールには 'build-essential' と 'pkg-config' が必要になる場合があります
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    curl \
    # 他に必要なaptパッケージがあればここに追加
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# コンテナ起動時に実行されるコマンド
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
