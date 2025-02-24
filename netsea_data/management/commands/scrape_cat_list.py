import os
import time
from django.core.management.base import BaseCommand
from netsea_data.models import NetseaCatList
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class Command(BaseCommand):
    help = 'Scrape Netsea category list from https://www.netsea.jp/category/ and save to NetseaCatList'

    def handle(self, *args, **options):
        # Seleniumの設定
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)

        # ログイン処理
        self.ensure_logged_in(driver, wait)

        # カテゴリ一覧を取得
        self.scrape_category_list(driver, wait)

        driver.quit()
        self.stdout.write(self.style.SUCCESS('Category list scraping completed successfully'))

    def ensure_logged_in(self, driver, wait):
        """ログイン状態を確認し、必要に応じてログイン"""
        login_url = 'https://www.netsea.jp/login'
        username = 'doublenuts8'  # 実際のユーザー名に置き換え
        password = 'Maropi888'    # 実際のパスワードに置き換え

        driver.get('https://www.netsea.jp/')
        try:
            login_link = wait.until(EC.presence_of_element_located((By.XPATH, '//a[@href="https://www.netsea.jp/login"]')))
            self.stdout.write(self.style.SUCCESS('未ログイン状態です。ログイン処理を開始します...'))
            
            driver.get(login_url)
            user_input = driver.find_element(By.ID, 'userId')
            user_input.send_keys(username)
            pass_input = driver.find_element(By.ID, 'pass')
            pass_input.send_keys(password)
            submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'userId')))
            self.stdout.write(self.style.SUCCESS('ログインに成功しました...'))
        except TimeoutException:
            self.stdout.write(self.style.SUCCESS('すでにログイン済みです...'))

    def scrape_category_list(self, driver, wait):
        """NETSEAのカテゴリ一覧を取得してDBに保存"""
        driver.get('https://www.netsea.jp/category/')
        
        try:
            # ページが完全に読み込まれるのを待つ
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'categoryListWrapper')))

            # レベル1: 最上位カテゴリ
            level1_elements = driver.find_elements(By.XPATH, '//ul[@class="categoryList"]/li/a[@class="category"]')
            self.stdout.write(self.style.SUCCESS(f'Found {len(level1_elements)} level 1 categories'))
            level1_data = {}
            for elem in level1_elements:
                url = elem.get_attribute('href')
                cat_name = elem.text.strip()
                cat_id = self.extract_cat_id(url)
                level1_data[cat_id] = cat_name
                self.save_category(cat_id, url, cat_name, 1, cat_name)

            # レベル2: サブカテゴリ
            level2_elements = driver.find_elements(By.XPATH, '//ul[@class="subCategory"]/li/a')
            self.stdout.write(self.style.SUCCESS(f'Found {len(level2_elements)} level 2 categories'))
            for elem in level2_elements:
                url = elem.get_attribute('href')
                cat_name = elem.text.strip()
                cat_id = self.extract_cat_id(url)
                parent_id = self.get_parent_id(cat_id, level1_data)
                parent_name = level1_data.get(parent_id, '')
                topics_path = f"{parent_name} > {cat_name}" if parent_name else cat_name
                self.save_category(cat_id, url, cat_name, 2, topics_path)

            # レベル3: 下位カテゴリ
            categ_blocks = driver.find_elements(By.XPATH, '//dl[@class="categListBlock"]')
            self.stdout.write(self.style.SUCCESS(f'Found {len(categ_blocks)} category blocks for level 3'))
            for block in categ_blocks:
                level2_elem = block.find_element(By.XPATH, './dt[@class="categListHd"]/a')
                level2_url = level2_elem.get_attribute('href')
                level2_cat_id = self.extract_cat_id(level2_url)
                level2_name = level2_elem.text.strip()
                
                level3_elements = block.find_elements(By.XPATH, './dd/ul[@class="categList"]/li/a')
                for elem in level3_elements:
                    url = elem.get_attribute('href')
                    cat_name = elem.text.strip()
                    cat_id = self.extract_cat_id(url)
                    topics_path = f"{level1_data.get(self.get_parent_id(level2_cat_id, level1_data), '')} > {level2_name} > {cat_name}"
                    self.save_category(cat_id, url, cat_name, 3, topics_path)

        except TimeoutException as e:
            self.stdout.write(self.style.ERROR(f'Timeout while scraping categories: {str(e)}'))
            with open('/code/logs/category_page_source.html', 'w') as f:
                f.write(driver.page_source)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error while scraping categories: {str(e)}'))

    def extract_cat_id(self, url):
        """URLからカテゴリIDを抽出"""
        from urllib.parse import urlparse, parse_qs
        query = urlparse(url).query
        params = parse_qs(query)
        return int(params.get('category_id', [hash(url) % 1000000])[0])

    def get_parent_id(self, cat_id, level1_data):
        """カテゴリIDから親IDを推測（簡易実装）"""
        if cat_id < 100:
            return cat_id  # レベル1はそのまま
        parent_id = cat_id // 100 if cat_id >= 1000 else cat_id // 10
        return parent_id if parent_id in level1_data else None

    def save_category(self, cat_id, url, cat_name, cat_level, topics_path):
        """カテゴリをDBに保存"""
        obj, created = NetseaCatList.objects.get_or_create(
            cat_id=cat_id,
            defaults={
                'url': url,
                'cat_name': cat_name,
                'cat_level': cat_level,
                'topics_path': topics_path,
                'cat_1': cat_id if cat_level == 1 else None,
                'cat_2': cat_id if cat_level == 2 else None,
                'cat_3': cat_id if cat_level == 3 else None,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Saved category: {cat_name} (ID: {cat_id}, Level: {cat_level})'))
        else:
            self.stdout.write(self.style.WARNING(f'Category already exists: {cat_name} (ID: {cat_id})'))
