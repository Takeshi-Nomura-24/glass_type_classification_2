from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django import forms # フォームモジュールをインポート
from .models import PredResult
from django.utils import timezone
import joblib
import csv
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

# ==========================================================
# 1. グローバル定数とモデルのロード
# ==========================================================

# 予測結果の分類を定数として定義
CLASSIFICATION_MAP = {
    1: '1:建物の窓（フロート処理済み）',
    2: '2:建物の窓（非フロート処理）',
    3: '3:車両の窓（フロート処理済み）',
    4: '4:車両の窓（非フロート処理）',
    5: '5:コンテナ',
    6: '6:食器',
    7: '7:ヘッドランプ',
}

# アプリケーション開始時にモデルを一度だけロード
SCALER = None
CLASSIFIER = None
try:
    SCALER = joblib.load('scaler.sav')
    CLASSIFIER = joblib.load('classifier.sav')
except FileNotFoundError:
    logger.error("MLモデルファイルが見つかりません (scaler.sav または classifier.sav)")
except Exception as e:
    logger.error(f"MLモデルのロード中にエラーが発生しました: {e}")


# ==========================================================
# 2. フォームの定義 (views.py内)
# ==========================================================
class PredictionInputForm(forms.Form):
    # 全てのフィールドがFloat型であり、必須であることを定義
    RI = forms.FloatField(required=True, label="屈折率 (RI)")
    Na = forms.FloatField(required=True, label="ナトリウム (Na)")
    Mg = forms.FloatField(required=True, label="マグネシウム (Mg)")
    Al = forms.FloatField(required=True, label="アルミニウム (Al)")
    Si = forms.FloatField(required=True, label="ケイ素 (Si)")
    K  = forms.FloatField(required=True, label="カリウム (K)")
    Ca = forms.FloatField(required=True, label="カルシウム (Ca)")
    Ba = forms.FloatField(required=True, label="バリウム (Ba)")
    Fe = forms.FloatField(required=True, label="鉄 (Fe)")


# ==========================================================
# 3. 関数ベースビュー (FBV)
# ==========================================================

def home(request):
    """ホーム画面を表示する"""
    # エラーで戻ってきた場合、フォームオブジェクトをテンプレートに渡す
    return render(request, 'home.html')

@require_http_methods(["POST", "GET"]) 
def result(request):
    """予測を行い、結果をデータベースに保存し、結果画面を表示する"""
    
    if not CLASSIFIER or not SCALER:
        return render(request, 'result.html', {'error': 'システムエラー: 予測モデルが利用できません。'})
    
    # リクエストメソッドに応じてデータソースを選択
    if request.method == 'POST':
        form = PredictionInputForm(request.POST) # POSTデータを使用
    else: 
        form = PredictionInputForm(request.GET) # GETデータを使用 (直接URLアクセス等)
        
    
    if form.is_valid():
        # 検証済みのクリーンなデータ
        cleaned_data = form.cleaned_data
        
        # 1. 予測に必要なデータのリスト化
        input_data = [
            cleaned_data['RI'], cleaned_data['Na'], cleaned_data['Mg'], cleaned_data['Al'], 
            cleaned_data['Si'], cleaned_data['K'], cleaned_data['Ca'], cleaned_data['Ba'], 
            cleaned_data['Fe']
        ]
        
        # 2. 予測処理 
        parameters = SCALER.transform([input_data])
        ans_key = CLASSIFIER.predict(parameters)[0]
        ans_display = CLASSIFICATION_MAP.get(ans_key, '分類不能な結果')
        
        # 3. データベースへの保存
        PredResult.objects.create(
            classification=ans_display,
            **cleaned_data # 検証済みのデータをまとめて渡す
        )

        return render(request, 'result.html', {'ans': ans_display})
        
    else:
        # 検証失敗時: home.htmlを再レンダリングし、エラー情報を持つ form オブジェクトを渡す
        logger.warning(f"入力フォームの検証に失敗しました: {form.errors}")
        
        # home.htmlを再レンダリングし、エラー情報を持つフォームをテンプレートに渡す
        return render(request, 'home.html', {'form': form})


def view_data(request):
    """保存された予測結果一覧を表示する"""
    # created_at の降順で並び替え
    data = {"dataset": PredResult.objects.all().order_by('-created_at')}
    return render(request, "view_data.html", data)


def exportcsv(request):
    """保存されたデータをCSVファイルとしてエクスポートする"""
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="predresults.csv"'
    
    writer = csv.writer(response)
    header = ['ID', 'RI', 'Na', 'Mg', 'Al', 'Si', 'K', 'Ca', 'Ba', 'Fe', 'Classification', 'Prediction Time']
    writer.writerow(header)

    # created_at (予測日時) も含める
    fields = ['id','RI', 'Na', 'Mg', 'Al', 'Si', 'K', 'Ca', 'Ba', 'Fe', 'classification', 'created_at']
    parameters = PredResult.objects.all().order_by('id').values_list(*fields)
    
    for row in parameters:
        writer.writerow(row)
        
    return response


