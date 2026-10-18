from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('polls/create/', views.poll_create_view, name='poll_create'),
    path('api/poll/<int:poll_id>/vote/', views.poll_vote_api, name='poll_vote_api'),
]
