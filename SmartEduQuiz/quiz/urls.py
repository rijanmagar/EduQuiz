from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('quiz/create/', views.create_quiz, name='create_quiz'),
    path('quiz/list/', views.quiz_list, name='quiz_list'),
    path('quiz/list/<int:category_id>/', views.quiz_list_category, name='quiz_list_category'),
    path('quiz/<int:quiz_id>/', views.start_quiz, name='start_quiz'),
    path('quiz/results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    path('bookmark/', views.bookmark_question, name='bookmark_question'),
]