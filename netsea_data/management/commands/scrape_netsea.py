import os
import time
import zipfile
import csv
from django.core.management.base import BaseCommand, CommandError
from netsea_data.models import NetseaCatCsv, NetseaCatList
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class Command(BaseCommand):
    help = 'Scrape Netsea category data, download/extract CSV for Cat_3 within specified range'

    def add_arguments(self, parser):
        parser.add_argument('--start_cat_id', type=int, help='Start category ID for processing')
        parser.add_argument('--end_cat_id', type=int, help='End category ID for processing')

    def handle(self, *args, **options):
        start_cat_id = options['start_cat_id']
        end_cat_id = options['end_cat_id']
        if start_cat_id is None or end_cat_id is None:
            raise CommandError('Please specify --start_cat_id and --end_cat_id')

        # Seleniumの設定
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')  # ヘッドレスモード
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # ダウンロードディレクトリを設定
        prefs = {'download.default_directory': '/code/downloads'}
        chrome_options.add_experimental_option('prefs', prefs)
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)

        # ログイン処理（必要時のみ）
        self.ensure_logged_in(driver, wait)

        # カテゴリIDのURLを取得
        cat_3_urls = NetseaCatList.objects.filter(
            cat_level=3,
            cat_id__gte=start_cat_id,
            cat_id__lte=end_cat_id
        ).values_list('url', 'cat_id')

        # ダウンロードディレクトリをクリア
        download_dir = '/code/downloads'
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        else:
            for file in os.listdir(download_dir):
                os.remove(os.path.join(download_dir, file))

        # 各カテゴリIDを処理
        for url, cat_id in cat_3_urls:
            self.process_category(driver, wait, url, cat_id)
            time.sleep(5)  # 次の処理前に待機

        driver.quit()
        self.stdout.write(self.style.SUCCESS('Scraping completed'))

    def ensure_logged_in(self, driver, wait):
        """ログイン状態を確認し、必要に応じてログイン"""
        login_url = 'https://www.netsea.jp/login'
        username = 'doublenuts8'  # 実際のユーザー名に置き換え
        password = 'Maropi888'    # 実際のパスワードに置き換え

        driver.get('https://www.netsea.jp/')  # ログインチェック用のページ
        try:
            # 未ログインの場合、ログインリンクを検出
            login_link = wait.until(EC.presence_of_element_located((By.XPATH, '//a[@href="https://www.netsea.jp/login"]')))
            #print('未ログイン状態です。ログイン処理を開始します...')
            self.stdout.write(self.style.SUCCESS(f'未ログイン状態です。ログイン処理を開始します...'))
            
            # ログインページに遷移
            driver.get(login_url)

            # ユーザー名とパスワードを入力
            user_input = driver.find_element(By.ID, 'userId')
            user_input.send_keys(username)
            pass_input = driver.find_element(By.ID, 'pass')
            pass_input.send_keys(password)

            # ログインボタンをクリック
            submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()

            # ログイン成功を待つ（ユーザーIDが表示されるまで）
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'userId')))
            self.stdout.write(self.style.SUCCESS(f'ログインに成功しました...'))
            #print('ログインに成功しました')

        except TimeoutException:
            # ログインリンクが見つからない場合、すでにログイン済み
            self.stdout.write(self.style.ERROR(f'すでにログイン済みか、タイムアウトです...'))
            #print('すでにログイン済みです')

    def process_category(self, driver, wait, url, cat_id):
        """特定のカテゴリIDのページを処理"""
        try:
            self.stdout.write(self.style.SUCCESS(f'Accessing URL: {url}'))
            driver.get(url)
            self.stdout.write(self.style.SUCCESS(f'Current URL: {driver.current_url}'))

            # ページが完全に読み込まれるまで待機
            self.stdout.write(self.style.SUCCESS('Waiting for exhibit_dl...'))
            wait = WebDriverWait(driver, 10) 
            #wait.until(EC.presence_of_element_located((By.ID, 'materialDlModalTrigger')))

            # モーダルを開く
            download_button = wait.until(EC.visibility_of_element_located((By.ID, 'exhibit_dl')))
            self.stdout.write(self.style.SUCCESS('Found exhibit_dl'))
            self.stdout.write(self.style.SUCCESS('Clicking download button...'))
            download_button.click()

            # モーダルが表示されるまで待機
            self.stdout.write(self.style.SUCCESS('Waiting for modal...'))
            modal = wait.until(EC.visibility_of_element_located((By.ID, 'materialDlModal')))
            self.stdout.write(self.style.SUCCESS('Modal is visible'))

            # ダウンロードオプションを選択（例: 差分王向け「商品情報(CSV)のみ」）
            self.stdout.write(self.style.SUCCESS('Selecting radio button...'))
            time.sleep(2)

            # ラジオボタンを選択（JavaScriptで確実にクリック）
            radio_button = driver.find_element(By.ID, 'radio2_1')
            driver.execute_script("arguments[0].click();", radio_button)
            """
            radio_button = wait.until(EC.element_to_be_clickable((By.ID, 'radio2_1')))
            self.stdout.write(self.style.SUCCESS('radio2_1 is clickable'))
            #radio_button = modal.find_element(By.ID, 'radio2_1')
            radio_button.click()
            """

            # ダウンロードを実行
            self.stdout.write(self.style.SUCCESS('Clicking submit button...'))
            #submit_button = modal.find_element(By.ID, 'exhibit_dl_submit')
            submit_button = driver.find_element(By.ID, 'exhibit_dl_submit')
            submit_button.click()

            # ダウンロード完了を待つ（ディレクトリ監視）
            self.stdout.write(self.style.SUCCESS('Waiting for download...'))
            download_dir = '/code/downloads'
            max_wait = 30  # 最大待機時間（秒）
            elapsed = 0
            zip_file_path = None
            while elapsed < max_wait:
                zip_files = [f for f in os.listdir(download_dir) if f.endswith('.zip')]
                if zip_files:
                    zip_file_path = os.path.join(download_dir, zip_files[0])
                    break
                time.sleep(1)
                elapsed += 1
            if not zip_file_path:
                raise Exception(f"Download timeout for category ID {cat_id}")

            # モーダルが自動で閉じるので、閉じる処理は不要
            self.stdout.write(self.style.SUCCESS('Download completed, modal closed automatically'))

            # ダウンロードしたファイルを処理
            self.stdout.write(self.style.SUCCESS('Handling downloaded file...'))
            self.handle_downloaded_file(cat_id)

            self.stdout.write(self.style.SUCCESS(f'Processed category ID {cat_id}'))
        except TimeoutException as e:
            self.stdout.write(self.style.ERROR(f'Timeout while processing {url}: {str(e)}'))
            with open(f'page_source_timeout_{cat_id}.html', 'w') as f:
                f.write(driver.page_source)
        except NoSuchElementException as e:
            self.stdout.write(self.style.ERROR(f'Element not found while processing {url}: {str(e)}'))
            with open(f'page_source_element_{cat_id}.html', 'w') as f:
                f.write(driver.page_source)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error while processing {url}: {str(e)}'))
            with open(f'page_source_unexpected_{cat_id}.html', 'w') as f:
                f.write(driver.page_source)

    def handle_downloaded_file(self, cat_id):
        """ダウンロードしたZIPファイルを処理"""
        download_dir = '/code/downloads'
        # ダウンロードされたZIPファイルを取得（最新のファイルを使用）
        zip_files = [f for f in os.listdir(download_dir) if f.endswith('.zip')]
        if not zip_files:
            self.stdout.write(self.style.ERROR(f'No ZIP file found for cat_id {cat_id}'))
            return
        zip_path = os.path.join(download_dir, zip_files[0])  # 最新のZIPファイルを使用

        # CSV を展開
        csv_dir = '/code/csv'
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith('.csv'):
                    csv_filename = f'cat_3_{cat_id}.csv'
                    zip_ref.extract(file_info, csv_dir)
                    extracted_path = os.path.join(csv_dir, file_info.filename)
                    target_path = os.path.join(csv_dir, csv_filename)
                    os.rename(extracted_path, target_path)
                    self.stdout.write(self.style.SUCCESS(f'Extracted CSV to {target_path}'))

                    # CSV を読み込んで netsea_cat_csv に保存
                    with open(target_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader)  # ヘッダーをスキップ
                        for row in reader:
                            if len(row) >= 3:
                                jan_cd = int(row[0]) if row[0] else None
                                price = int(row[1]) if row[1] else None
                                url = row[2] if row[2] else None

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
                                    obj.cat_id = cat_id
                                    obj.jan_cd = jan_cd
                                    obj.price = price
                                    obj.csv_name = csv_filename
                                    obj.save()
                                    self.stdout.write(self.style.WARNING(f'Updated existing record for url: {url}'))
                                else:
                                    self.stdout.write(self.style.SUCCESS(f'Created new record for url: {url}'))
                        self.stdout.write(self.style.SUCCESS(f'Processed CSV data from {csv_filename} into netsea_cat_csv'))

        # ZIPファイルを削除
        os.remove(zip_path)