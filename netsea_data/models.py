from django.db import models

class NetseaCatCsv(models.Model):
    id = models.AutoField(primary_key=True)  # 自動採番の主キー
    cat_id = models.IntegerField(null=False, blank=False)  # カテゴリID（必須）
    jan_cd = models.BigIntegerField(null=True, blank=True)  # JANコード（ブランク可）
    price = models.IntegerField(null=True, blank=True)  # 仕入れ価格（ブランク可）
    url = models.CharField(max_length=255, null=True, blank=True, unique=True) # 仕入れ元URL（ブランク可）
    csv_name = models.CharField(max_length=255, null=True, blank=True) # CSVファイル名（ブランク可）
    created_at = models.DateTimeField(auto_now_add=True)  # 登録日
    updated_at = models.DateTimeField(auto_now=True)      # 更新日

    class Meta:
        db_table = 'netsea_cat_csv'  # テーブル名を指定

    def __str__(self):
        return f"CatID: {self.cat_id}, JAN: {self.jan_cd}"

class NetseaCatList(models.Model):
    id = models.AutoField(primary_key=True)  # 自動採番の主キー
    cat_id = models.IntegerField(null=False, blank=False)  # カテゴリID（必須）
    url = models.TextField(null=True, blank=True)  # カテゴリのURL（ブランク可）
    cat_name = models.TextField(null=True, blank=True)  # カテゴリ名（ブランク可）
    cat_level = models.IntegerField(null=True, blank=True)  # カテゴリ階層（ブランク可）
    topics_path = models.TextField(null=True, blank=True)  # パンくず（ブランク可）
    cat_1 = models.IntegerField(null=True, blank=True)  # カテゴリ_1（ブランク可）
    cat_2 = models.IntegerField(null=True, blank=True)  # カテゴリ_2（ブランク可）
    cat_3 = models.IntegerField(null=True, blank=True)  # カテゴリ_3（ブランク可）

    class Meta:
        db_table = 'netsea_cat_list'  # テーブル名を指定

    def __str__(self):
        return f"CatID: {self.cat_id}, Name: {self.cat_name}"
