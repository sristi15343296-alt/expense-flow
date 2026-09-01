from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Transaction, Budget, SavingsGoal

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'category', 'date', 'description']
    list_filter = ['transaction_type', 'category', 'date']
    search_fields = ['description', 'category']

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'period', 'created_at']
    list_filter = ['period', 'category']

@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'target_amount', 'current_amount', 'target_date']
    search_fields = ['name']

# Extend UserAdmin to show related info if needed
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
