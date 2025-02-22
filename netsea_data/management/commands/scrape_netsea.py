import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Scrape Netsea category data with login'

    def handle(self, *args, **options):
        # ログイン情報
        login_url = 'https://www.netsea.jp/login'
        username = 'doublenuts8'
        password = 'Maropi888'
        category_url = 'https://www.netsea.jp/search/?category_id=2'

        # セッションを開始
        session = requests.Session()

        # ログインページにアクセスして CSRF トークンを取得
        response = session.get(login_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # ログイン状態をチェック
        login_form = soup.find('form', action='https://www.netsea.jp/login')
        if not login_form:
            self.stdout.write(self.style.WARNING('Already logged in or unexpected page structure'))
        else:
            # CSRF トークンを取得
            csrf_token = soup.find('input', {'name': '_token'})['value']

            # ログインデータ
            payload = {
                'login_id': username,
                'password': password,
                '_token': csrf_token,
                'remember': 'on',  # オプション: ログイン状態を維持
                'bookmark': 'on'   # オプション: ブックマーク引き継ぎ
            }

            # ログイン実行
            login_response = session.post(login_url, data=payload)
            if login_response.status_code == 200 and 'login' not in login_response.url:
                self.stdout.write(self.style.SUCCESS('Login successful'))
            else:
                self.stdout.write(self.style.ERROR(f'Login failed: {login_response.status_code}, URL: {login_response.url}'))
                return

        # カテゴリトップページにアクセス
        category_response = session.get(category_url)
        if category_response.status_code == 200:
            self.stdout.write(self.style.SUCCESS(f'Accessed category page: {category_url}'))
            soup = BeautifulSoup(category_response.text, 'html.parser')
            self.stdout.write(f'Page title: {soup.title.string}')
        else:
            self.stdout.write(self.style.ERROR(f'Failed to access category page: {category_response.status_code}'))
        