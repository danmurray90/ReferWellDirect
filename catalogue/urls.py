"""
URL configuration for catalogue app.
"""
from django.urls import path
from . import views

app_name = 'catalogue'

urlpatterns = [
    # Web views
    path('', views.PsychologistListView.as_view(), name='psychologist_list'),
    path('<uuid:pk>/', views.PsychologistDetailView.as_view(), name='psychologist_detail'),
    path('dashboard/', views.PsychologistDashboardView.as_view(), name='psychologist_dashboard'),
]
