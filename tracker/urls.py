from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transactions/', views.transactions, name='transactions'),
    path('add/', views.add_transaction, name='add_transaction'),
    path('edit/<int:pk>/', views.edit_transaction, name='edit_transaction'),
    path('delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('analytics/', views.analytics, name='analytics'),
    path('budgets/', views.budgets, name='budgets'),
    path('budgets/add/', views.add_budget, name='add_budget'),
    path('budgets/edit/<int:pk>/', views.edit_budget, name='edit_budget'),
    path('budgets/delete/<int:pk>/', views.delete_budget, name='delete_budget'),
    path('goals/', views.goals, name='goals'),
    path('goals/add/', views.add_goal, name='add_goal'),
    path('goals/edit/<int:pk>/', views.edit_goal, name='edit_goal'),
    path('goals/update/<int:pk>/', views.update_goal_amount, name='update_goal_amount'),
    path('goals/delete/<int:pk>/', views.delete_goal, name='delete_goal'),
    path('settings/', views.settings_view, name='settings'),
    path('health/', views.health_score, name='health'),
    path('', views.dashboard, name='home'),
]
