from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.core.management import call_command
from io import StringIO
from .models import NetseaCatCsv, NetseaCatList
import os
import subprocess

@admin.register(NetseaCatCsv)
class NetseaCatCsvAdmin(admin.ModelAdmin):
    list_display = ('id', 'cat_id', 'jan_cd', 'price', 'url', 'csv_name', 'created_at', 'updated_at')
    list_filter = ('cat_id',)
    search_fields = ('jan_cd', 'url', 'csv_name')

@admin.register(NetseaCatList)
class NetseaCatListAdmin(admin.ModelAdmin):
    list_display = ('id', 'cat_id', 'cat_name', 'cat_level', 'url')
    list_filter = ('cat_id', 'cat_level')
    search_fields = ('cat_name', 'url', 'topics_path')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('csv-download/', self.admin_site.admin_view(self.csv_download_view), name='netsea_data_netseacatlist_csv_download'),
            path('csv-download/log/', self.admin_site.admin_view(self.get_log), name='netsea_data_netseacatlist_csv_download_log'),
        ]
        return custom_urls + urls

    def csv_download_view(self, request):
        log_file = '/code/logs/scrape_netsea.log'
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        if request.method == 'POST':
            start_cat_id = request.POST.get('start_cat_id')
            end_cat_id = request.POST.get('end_cat_id')
            if start_cat_id and end_cat_id:
                # コマンドを非同期で実行し、ログをファイルに出力
                cmd = f"python manage.py scrape_netsea --start_cat_id={start_cat_id} --end_cat_id={end_cat_id} > {log_file} 2>&1 &"
                subprocess.Popen(cmd, shell=True)
                return render(request, 'admin/netsea_data/csv_download.html', {
                    'start_cat_id': start_cat_id,
                    'end_cat_id': end_cat_id,
                    'running': True,
                })
        return render(request, 'admin/netsea_data/csv_download.html', {'running': False})

    def get_log(self, request):
        log_file = '/code/logs/scrape_netsea.log'
        log_content = ""
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_content = f.read().splitlines()
        return render(request, 'admin/netsea_data/csv_download_log.html', {'output': log_content})

admin.site.site_header = "NETSEA Admin"
admin.site.site_title = "NETSEA Admin"
admin.site.index_title = "NETSEA データ管理"