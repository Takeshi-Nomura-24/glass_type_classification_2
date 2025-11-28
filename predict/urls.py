from django.urls import path
from . import views

app_name = "predict"

urlpatterns = [
    path('', views.home, name='home'),
    path('result/', views.result, name='result'),
    path('view_data/', views.view_data, name='view_data'),
    path('exportcsv/', views.exportcsv, name='exportcsv'),
]
