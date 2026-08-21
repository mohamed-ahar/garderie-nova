from django.urls import path
from . import views

app_name = 'curriculum'

urlpatterns = [
    path('', views.LessonListView.as_view(), name='lesson_list'),
    path('add/', views.LessonCreateView.as_view(), name='add_lesson'),
    path('<uuid:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('<uuid:pk>/edit/', views.LessonUpdateView.as_view(), name='edit_lesson'),
    path('<uuid:pk>/delete/', views.LessonDeleteView.as_view(), name='delete_lesson'),
    
    # API for Sidebar Badge
    path('api/count/', views.lesson_count_api, name='lesson_count_api'),
]