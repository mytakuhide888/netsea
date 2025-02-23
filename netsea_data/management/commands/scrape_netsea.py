import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from netsea_data.models import NetseaCatList, NetseaCatCsv
import os
import zipfile
import csv
import time

class Command(BaseCommand):
    help = 'Scrape Netsea category data, download/extract CSV for Cat_3 within specified range'

    def add_arguments(self, parser):
        parser.add_argument('--start_cat_id', type=int, help='Start category ID for processing')
        parser.add_argument('--end_cat_id', type=int, help='End category ID for processing')

    def handle(self, *args, **options):
        login_url = 'https://www.netsea.jp/login'
        username = 'doublenuts8'
        password = 'Maropi888'
        category_list_url = 'https://www.netsea.jp/category/'
        download_url = 'https://www.netsea.jp/exhibit_data_download'

        # 引数の取得
        start_cat_id = options['start_cat_id']
        end_cat_id = options['end_cat_id']
        if start_cat_id is None or end_cat_id is None:
            raise CommandError('Please specify --start_cat_id and --end_cat_id')

        session = requests.Session()
        response = session.get(login_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        login_form = soup.find('form', action='https://www.netsea.jp/login')
        if not login_form:
            self.stdout.write(self.style.WARNING('Already logged in or unexpected page structure'))
        else:
            csrf_token = soup.find('input', {'name': '_token'})['value']
            payload = {
                'login_id': username,
                'password': password,
                '_token': csrf_token,
                'remember': 'on',
                'bookmark': 'on'
            }
            login_response = session.post(login_url, data=payload)
            if login_response.status_code == 200 and 'login' not in login_response.url:
                self.stdout.write(self.style.SUCCESS('Login successful'))
            else:
                self.stdout.write(self.style.ERROR(f'Login failed: {login_response.status_code}, URL: {login_response.url}'))
                return

        # カテゴリ一覧を取得
        category_response = session.get(category_list_url)
        if category_response.status_code != 200:
            self.stdout.write(self.style.ERROR(f'Failed to access category list: {category_response.status_code}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Accessed category list: {category_list_url}'))
        soup = BeautifulSoup(category_response.text, 'html.parser')
        self.scrape_categories(soup)

        # ZIP と CSV ディレクトリを作成
        os.makedirs('/code/zip', exist_ok=True)
        os.makedirs('/code/csv', exist_ok=True)

        # カテゴリ_3 の URL を範囲指定で取得
        cat_3_urls = NetseaCatList.objects.filter(
            cat_level=3,
            cat_id__gte=start_cat_id,
            cat_id__lte=end_cat_id
        ).values_list('url', 'cat_id')
        
        for url, cat_id in cat_3_urls:
            self.download_extract_and_save_csv(session, url, download_url, cat_id)
            self.stdout.write(self.style.SUCCESS(f'Waiting 10 seconds before next download...'))
            time.sleep(10)  # 10秒待機

    def scrape_categories(self, soup):
        category_headers = soup.find_all('h2', class_='categHd')
        for header in category_headers:
            a_tag = header.find('a')
            if not a_tag:
                continue

            cat_url = a_tag['href']
            cat_name = a_tag.text.strip()
            cat_id = self.extract_cat_id(cat_url)

            cat_1_obj, created = NetseaCatList.objects.get_or_create(
                cat_id=cat_id,
                defaults={'url': cat_url, 'cat_name': cat_name, 'cat_level': 1}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Saved Cat_1: {cat_name} (ID: {cat_id})'))

            categ_list_wrap = header.find_next('div', class_='categListWrap')
            if categ_list_wrap:
                categ_blocks = categ_list_wrap.find_all('dl', class_='categListBlock')
                for block in categ_blocks:
                    dt_tag = block.find('dt', class_='categListHd')
                    if dt_tag:
                        level_2_a = dt_tag.find('a', href=True)
                        if level_2_a:
                            level_2_url = level_2_a['href']
                            level_2_name = level_2_a.text.strip()
                            level_2_id = self.extract_cat_id(level_2_url)

                            level_2_obj, created = NetseaCatList.objects.get_or_create(
                                cat_id=level_2_id,
                                defaults={'url': level_2_url, 'cat_name': level_2_name, 'cat_level': 2, 'cat_1': cat_id}
                            )
                            if created:
                                self.stdout.write(self.style.SUCCESS(f'Saved Cat_2: {level_2_name} (ID: {level_2_id}, Parent: {cat_id})'))

                            dd_tag = block.find('dd')
                            if dd_tag:
                                level_3_list = dd_tag.find('ul', class_='categList')
                                if level_3_list:
                                    level_3_items = level_3_list.find_all('a', href=True)
                                    for level_3_a in level_3_items:
                                        level_3_url = level_3_a['href']
                                        level_3_name = level_3_a.text.strip()
                                        level_3_id = self.extract_cat_id(level_3_url)

                                        level_3_obj, created = NetseaCatList.objects.get_or_create(
                                            cat_id=level_3_id,
                                            defaults={'url': level_3_url, 'cat_name': level_3_name, 'cat_level': 3, 'cat_1': cat_id, 'cat_2': level_2_id}
                                        )
                                        if created:
                                            self.stdout.write(self.style.SUCCESS(f'Saved Cat_3: {level_3_name} (ID: {level_3_id}, Parent: {level_2_id})'))

    def download_extract_and_save_csv(self, session, cat_3_url, download_url, cat_id):
        # カテゴリ_3 ページにアクセス
        response = session.get(cat_3_url)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f'Failed to access {cat_3_url}: {response.status_code}'))
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', id='inputForm')
        if not form:
            self.stdout.write(self.style.ERROR(f'Form not found in {cat_3_url}'))
            return

        # CSRF トークンと exhibit_ids を取得
        csrf_token = form.find('input', {'name': '_token'})['value']
        exhibit_ids = [input_tag['value'] for input_tag in form.find_all('input', {'name': 'exhibit_ids[]'})]

        # CSV ダウンロードのリクエスト
        payload = {
            '_token': csrf_token,
            'd_mode': '3',
            'exhibit_ids[]': exhibit_ids
        }
        csv_response = session.post(download_url, data=payload)
        if csv_response.status_code != 200:
            self.stdout.write(self.style.ERROR(f'Failed to download ZIP: {csv_response.status_code}'))
            return

        # ZIP ファイルを保存
        zip_filename = f'/code/zip/cat_3_{cat_id}.zip'
        with open(zip_filename, 'wb') as f:
            f.write(csv_response.content)
        self.stdout.write(self.style.SUCCESS(f'Downloaded ZIP for {cat_3_url} to {zip_filename}'))

        # ZIP を展開して CSV を直接 /code/csv/ に保存
        csv_dir = '/code/csv'
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith('.csv'):
                    csv_filename = f'cat_3_{cat_id}.csv'  # サブディレクトリを避けるために固定名
                    zip_ref.extract(file_info, csv_dir)
                    extracted_path = os.path.join(csv_dir, file_info.filename)
                    target_path = os.path.join(csv_dir, csv_filename)
                    os.rename(extracted_path, target_path)
        self.stdout.write(self.style.SUCCESS(f'Extracted CSV to {target_path}'))

        # CSV を読み込んで netsea_cat_csv に保存
        csv_path = target_path
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ（必要に応じて確認）
            for row in reader:
                if len(row) >= 3:  # 最低 3 列あることを確認
                    jan_cd = int(row[0]) if row[0] else None
                    price = int(row[1]) if row[1] else None
                    url = row[2] if row[2] else None

                    # 重複チェックと更新または作成
                    obj, created = NetseaCatCsv.objects.get_or_create(
                        url=url,
                        defaults={
                            'cat_id': cat_id,
                            'jan_cd': jan_cd,
                            'price': price,
                            'csv_name': csv_filename,
                        }
                    )
                    if not created:
                        # 重複した場合、既存レコードを更新（updated_at も自動更新）
                        obj.cat_id = cat_id
                        obj.jan_cd = jan_cd
                        obj.price = price
                        obj.csv_name = csv_filename
                        obj.save()
                        self.stdout.write(self.style.WARNING(f'Updated existing record for url: {url}'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'Created new record for url: {url}'))
            self.stdout.write(self.style.SUCCESS(f'Saved CSV data from {csv_filename} to netsea_cat_csv'))

    def extract_cat_id(self, url):
        from urllib.parse import urlparse, parse_qs
        query = urlparse(url).query
        params = parse_qs(query)
        return int(params.get('category_id', [0])[0])
