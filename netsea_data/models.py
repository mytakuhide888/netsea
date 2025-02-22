from django.db import models

class NetseaCatCsv(models.Model):
    id = models.AutoField(primary_key=True)  # 自動採番の主キー
    cat_id = models.IntegerField(null=False, blank=False)  # カテゴリID（必須）
    jan_cd = models.BigIntegerField(null=True, blank=True)  # JANコード（ブランク可）
    price = models.IntegerField(null=True, blank=True)  # 仕入れ価格（ブランク可）
    url = models.TextField(null=True, blank=True)  # 仕入れ元URL（ブランク可）

    class Meta:
        db_table = 'netsea_cat_csv'  # テーブル名を指定

    def __str__(self):
        return f"CatID: {self.cat_id}, JAN: {self.jan_cd}"