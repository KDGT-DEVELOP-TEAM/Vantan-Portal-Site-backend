import os
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.views.generic import View
from django.utils.encoding import escape_uri_path
from django.conf import settings

from .models import File
# from .forms import FileUploadForm

# LoginRequiredMixinでログインを確認
# UserPassesTestMixinでアクティブユーザーかを確認

# ----------* リスト *----------
class ListFileView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.is_active

    # requestでkeywordが来てたら検索
    def get(self, request):
        keyword = request.GET.get("keyword")
        queryset = File.objects.all()

        if keyword:
            queryset = queryset.filter(Q(title__icontains=keyword))
        
        # Vue側で使わない項目は消してOK
        files = list(queryset.values("id", "title", "consent_publication", "storage_key", "created_at", "updated_at", "user_id"))

        return JsonResponse({"files": files}, safe=False)


# ----------* ダウンロード *----------
# とりあえずローカル環境の構成
class DownloadFileView(LoginRequiredMixin, UserPassesTestMixin, View):
    STORAGE_DIR = settings.LOCAL_STORAGE_DIR
    
    def test_func(self):
        return self.request.user.is_active

    def get(self, request, pk):

        # 指定されたファイルを取得
        file_obj = get_object_or_404(File, pk=pk)
            
        # ファイルパスを取得
        file_path = os.path.normpath(os.path.join(self.STORAGE_DIR, file_obj.storage_key))

        # ファイルが存在しない場合の処理(カスタムする場合は404.htmlを作る)
        if not os.path.exists(file_path):
            raise Http404("指定されたファイルが存在しません。")

        # ファイルをレスポンスにセット
        response = FileResponse(open(file_path, 'rb'), as_attachment=True)

        # ダウンロード時のファイル名を指定
        filename = escape_uri_path(os.path.basename(file_obj.storage_key))
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


# ----------* アップロード *----------
class UploadFileView(LoginRequiredMixin, UserPassesTestMixin, View):
    # アカウントのチェック
    def test_func(self):
        return self.request.user.is_active and self.request.user.role == 'admin'
    
    # この先はUC-09-01？


# ----------* 削除 *----------
class DeleteFileView(LoginRequiredMixin, UserPassesTestMixin, View):
    STORAGE_DIR = settings.LOCAL_STORAGE_DIR

    # アカウントのチェック
    def test_func(self):
        return self.request.user.is_active and self.request.user.role == 'admin'

    def delete(self, request, pk):
        # 指定されたファイルを取得
        file_obj = get_object_or_404(File, pk=pk)
        
        # ファイルパスを取得
        file_path = os.path.normpath(os.path.join(self.STORAGE_DIR, file_obj.storage_key))

        # ファイルが存在しない場合の処理
        if not os.path.exists(file_path):
            return JsonResponse({"error": "ファイルが存在しません。"}, status=404)

        # ファイル削除
        try:
            os.remove(file_path)
            file_obj.delete()
        except Exception as e:
            return JsonResponse({"error": f"削除に失敗しました: {e}"}, status=500)

        return JsonResponse({"message": "削除完了"})