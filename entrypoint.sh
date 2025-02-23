#!/bin/bash

echo "Running as user: $(whoami)"

# ボリュームの権限を再調整
if [ ! -d /code/static ]; then
    mkdir -p /code/static
fi
chown -R niiya:niiya /code/static || echo "Failed to chown /code/static"

# ログディレクトリを作成
#mkdir -p /code/logs
#chown niiya:niiya /code/logs

# MySQL が準備できるまで待機
until mysqladmin ping -h db -u niiya -pniiya --silent; do
    echo "Waiting for MySQL..."
    sleep 2
done
echo "MySQL is ready"

# ログローテーションを実行
# logrotate -f /code/logrotate.conf
#echo "Running logrotate..."
#sudo logrotate /code/logrotate.conf || echo "logrotate skipped due to permissions"
echo "starting gunicorn..."
# Gunicorn を直接実行（タイムアウトとログレベルを指定）
#exec bash -c "gunicorn --pythonpath /code myproject.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 300 --log-level debug"
exec bash -c "gunicorn --pythonpath /code myproject.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 300 --log-level debug --access-logfile /code/logs/gunicorn_access.log --error-logfile /code/logs/gunicorn_error.log  --capture-output --enable-stdio-inheritance"
#gunicorn --pythonpath /code myproject.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 300 --log-level debug --access-logfile /code/logs/gunicorn_access.log --error-logfile /code/logs/gunicorn_error.log --capture-output --enable-stdio-inheritance
echo "gunicorn started"
