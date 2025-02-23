from django.contrib import admin
from .models import NetseaCatCsv, NetseaCatList

# NetseaCatCsv の管理画面設定
@admin.register(NetseaCatCsv)
class NetseaCatCsvAdmin(admin.ModelAdmin):
    list_display = ('id', 'cat_id', 'jan_cd', 'price', 'url', 'csv_name')  # 表示するフィールド
    list_filter = ('cat_id',)  # フィルタリング可能なフィールド
    search_fields = ('jan_cd', 'url', 'csv_name')  # 検索可能なフィールド

# NetseaCatList の管理画面設定
@admin.register(NetseaCatList)
class NetseaCatListAdmin(admin.ModelAdmin):
    list_display = ('id', 'cat_id', 'cat_name', 'cat_level', 'url')  # 表示するフィールド
    list_filter = ('cat_id', 'cat_level')  # フィルタリング可能なフィールド
    search_fields = ('cat_name', 'url', 'topics_path')  # 検索可能なフィールド