from django.db import models
from django.utils import timezone

class PredResult(models.Model):
    # 測定/入力データ
    # verbose_nameを追加: Django AdminやFormでの表示名が分かりやすくなります
    RI = models.FloatField(verbose_name="屈折率 (RI)")
    Na = models.FloatField(verbose_name="ナトリウム (Na)")
    Mg = models.FloatField(verbose_name="マグネシウム (Mg)")
    Al = models.FloatField(verbose_name="アルミニウム (Al)")
    Si = models.FloatField(verbose_name="ケイ素 (Si)")
    K  = models.FloatField(verbose_name="カリウム (K)")
    Ca = models.FloatField(verbose_name="カルシウム (Ca)")
    Ba = models.FloatField(verbose_name="バリウム (Ba)")
    Fe = models.FloatField(verbose_name="鉄 (Fe)")
    
    # 予測結果
    classification = models.CharField(
        max_length=30,
        verbose_name="予測分類結果"
    )

    # 監査/トラッキング用のタイムスタンプを追加
    created_at = models.DateTimeField(
        default=timezone.now, # データの保存時に自動で日時を記録
        verbose_name="予測日時"
    )

    class Meta:
        # 管理画面での表示名を設定
        verbose_name = "予測結果"
        verbose_name_plural = "予測結果一覧"
        # 新しい結果が常に上に来るようにデフォルトの並び順を設定
        ordering = ['-created_at'] 

    def __str__(self):
        # どの予測結果か、いつの結果かを分かりやすく返すように変更
        return f"[{self.classification}] - {self.created_at.strftime('%Y/%m/%d %H:%M')}"

