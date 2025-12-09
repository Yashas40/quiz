from django.urls import path
from . import views
from django.views.generic import RedirectView

app_name = 'quiz'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='quiz:login', permanent=False), name='root'),
    path('single-player/', views.single_player, name='single_player'),
    path('multiplayer/', views.multiplayer, name='multiplayer'),
    path('coding-battle/', views.coding_battle, name='coding_battle'),
    path('start-single-session/', views.start_single_session, name='start_single_session'),
    path('submit-answer/', views.submit_answer, name='submit_answer'),

    path('get-next-question/<int:session_id>/', views.get_next_question, name='get_next_question'),
    path('generate-quiz-session/', views.generate_quiz_session, name='generate_quiz_session'),
    
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]
