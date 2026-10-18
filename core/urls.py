from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('polls/create/', views.poll_create_view, name='poll_create'),
    path('polls/<int:poll_id>/toggle-status/', views.poll_toggle_status_view, name='poll_toggle_status'),
    path('polls/<int:poll_id>/delete/', views.poll_delete_view, name='poll_delete'),
    path('api/poll/<int:poll_id>/vote/', views.poll_vote_api, name='poll_vote_api'),
]
