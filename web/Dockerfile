FROM python:3.9-slim

# 作業ディレクトリの設定
WORKDIR /app

# OS パッケージの更新と MySQL クライアントライブラリ用パッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    curl \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピーしてインストール
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt


# アプリケーションのソースコードをコピー
COPY . /app/

# /tmp にログ出力するためのパーミッション確認（sticky bit で全ユーザ書き込み可）
RUN chmod 1777 /tmp

# gunicorn による起動（netsea プロジェクトとして設定）
CMD ["gunicorn", "netsea.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "debug"]
