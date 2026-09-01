from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

TRANSACTION_TYPES = [('income', 'Income'), ('expense', 'Expense')]

EXPENSE_CATEGORIES = [
    ('Food', 'Food'),
    ('Shopping', 'Shopping'),
    ('Transportation', 'Transportation'),
    ('Education', 'Education'),
    ('Entertainment', 'Entertainment'),
    ('Bills', 'Bills'),
    ('Health', 'Health'),
    ('Travel', 'Travel'),
    ('Other', 'Other'),
]

INCOME_CATEGORIES = [
    ('Salary', 'Salary'),
    ('Freelance', 'Freelance'),
    ('Business', 'Business'),
    ('Gift', 'Gift'),
    ('Other', 'Other'),
]

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='expense')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    category = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.category}"

class Budget(models.Model):
    PERIOD_CHOICES = [('monthly', 'Monthly'), ('weekly', 'Weekly'), ('yearly', 'Yearly')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'category', 'period']
        ordering = ['category', '-created_at']

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.period})"

class SavingsGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    target_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.current_amount}/{self.target_amount}"
