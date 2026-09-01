from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Q, F, Avg, Count, FloatField
from django.db.models.functions import TruncMonth, TruncDay
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

from .models import Transaction, Budget, SavingsGoal
from .forms import CustomUserCreationForm, TransactionForm, BudgetForm, SavingsGoalForm

# Helper category choices
EXPENSE_CATS = ['Food', 'Shopping', 'Transportation', 'Education', 'Entertainment', 'Bills', 'Health', 'Travel', 'Other']
INCOME_CATS = ['Salary', 'Freelance', 'Business', 'Gift', 'Other']

BASE_CONTEXT = {
    'nav_items': [
        {'name':'Dashboard', 'url':'/dashboard/', 'icon':'bi-house-door'},
        {'name':'Transactions', 'url':'/transactions/', 'icon':'bi-list-ul'},
        {'name':'Add Transaction', 'url':'/add/', 'icon':'bi-plus-circle'},
        {'name':'Analytics', 'url':'/analytics/', 'icon':'bi-bar-chart'},
        {'name':'Budgets', 'url':'/budgets/', 'icon':'bi-piggy-bank'},
        {'name':'Savings Goals', 'url':'/goals/', 'icon':'bi-bullseye'},
        {'name':'Settings', 'url':'/settings/', 'icon':'bi-gear'},
    ]
}

def get_date_filter(request):
    period = request.GET.get('period', 'month')
    custom_start = request.GET.get('start')
    custom_end = request.GET.get('end')
    today = timezone.now().date()
    if period == 'today':
        start = today; end = today
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    elif period == 'month':
        start = today.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    elif period == 'year':
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)
    elif period == 'custom' and custom_start and custom_end:
        start = datetime.strptime(custom_start, '%Y-%m-%d').date()
        end = datetime.strptime(custom_end, '%Y-%m-%d').date()
    else:
        start = today - timedelta(days=30); end = today
    return period, start, end

# Auth views
from django.shortcuts import render

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Welcome back!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'tracker/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

# Dashboard
@login_required
def dashboard(request):
    user = request.user
    period, start, end = get_date_filter(request)
    txs = Transaction.objects.filter(user=user, date__gte=start, date__lte=end)
    total_income = txs.filter(transaction_type='income').aggregate(s=Sum('amount'))['s'] or Decimal('0')
    total_expense = txs.filter(transaction_type='expense').aggregate(s=Sum('amount'))['s'] or Decimal('0')
    balance = total_income - total_expense
    savings = total_income - total_expense  # simplified savings metric
    recent = Transaction.objects.filter(user=user).order_by('-date', '-created_at')[:8]

    # Spending by category for chart
    exp = txs.filter(transaction_type='expense').values('category').annotate(total=Sum('amount')).order_by('-total')
    cat_labels = [e['category'] for e in exp]
    cat_values = [float(e['total']) for e in exp]

    # Financial insights
    insights = []
    if exp:
        top = exp[0]
        insights.append(f"{top['category']} is your highest spending category this period.")
    total_txs = txs.count()
    if total_txs > 0:
        avg_expense = total_expense / max(total_txs, 1)
        insights.append(f"You made {total_txs} transactions this period.")
    if total_income > 0:
        rate = (total_income - total_expense) / total_income * 100
        insights.append(f"Your savings rate is {rate:.0f}%.")
    else:
        insights.append("Add some income to see your savings rate.")

    # Quick stats for cards
    context = BASE_CONTEXT.copy()
    context.update({
        'title': 'Dashboard',
        'period': period,
        'start': start,
        'end': end,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'savings': savings,
        'recent_transactions': recent,
        'cat_labels': cat_labels,
        'cat_values': cat_values,
        'insights': insights,
        'user': user,
    })
    return render(request, 'tracker/dashboard.html', context)

# Transaction pages
@login_required
def transactions(request):
    user = request.user
    txs = Transaction.objects.filter(user=user)
    q = request.GET.get('q', '').strip()
    cat_filter = request.GET.get('category', '')
    type_filter = request.GET.get('type', '')
    start = request.GET.get('start')
    end = request.GET.get('end')
    if q:
        txs = txs.filter(Q(description__icontains=q) | Q(category__icontains=q))
    if cat_filter:
        txs = txs.filter(category=cat_filter)
    if type_filter:
        txs = txs.filter(transaction_type=type_filter)
    if start:
        txs = txs.filter(date__gte=start)
    if end:
        txs = txs.filter(date__lte=end)
    txs = txs.order_by('-date', '-created_at')
    categories = sorted(set(t.category for t in Transaction.objects.filter(user=user)))
    context = BASE_CONTEXT.copy()
    context.update({
        'title': 'Transactions',
        'transactions': txs,
        'q': q,
        'cat_filter': cat_filter,
        'type_filter': type_filter,
        'start': start,
        'end': end,
        'categories': categories,
        'user': user,
    })
    return render(request, 'tracker/transactions.html', context)

@login_required
def add_transaction(request):
    user = request.user
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        # Set category based on type if not provided
        if form.is_valid():
            tx = form.save(commit=False)
            tx.user = user
            # If category empty or mismatched, auto-set based on type
            if not tx.category:
                if tx.transaction_type == 'income':
                    tx.category = 'Salary'
                else:
                    tx.category = 'Food'
            tx.save()
            messages.success(request, 'Transaction added successfully.')
            return redirect('transactions')
        else:
            messages.error(request, 'Please correct the errors.')
    else:
        form = TransactionForm()
        form.fields['category'].choices = [(c,c) for c in EXPENSE_CATS]
    context = BASE_CONTEXT.copy()
    context.update({'title': 'Add Transaction', 'form': form, 'user': user, 'expense_cats': EXPENSE_CATS, 'income_cats': INCOME_CATS, 'today': timezone.now().date()})
    return render(request, 'tracker/add_transaction.html', context)

@login_required
def edit_transaction(request, pk):
    user = request.user
    tx = get_object_or_404(Transaction, pk=pk, user=user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=tx)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.user = user
            tx.save()
            messages.success(request, 'Transaction updated.')
            return redirect('transactions')
        else:
            messages.error(request, 'Please correct errors.')
    else:
        form = TransactionForm(instance=tx)
    # Ensure category choices match type
    if tx.transaction_type == 'income':
        form.fields['category'].choices = [(c,c) for c in INCOME_CATS]
    else:
        form.fields['category'].choices = [(c,c) for c in EXPENSE_CATS]
    context = BASE_CONTEXT.copy()
    context.update({'title': 'Edit Transaction', 'form': form, 'tx': tx, 'user': user, 'expense_cats': EXPENSE_CATS, 'income_cats': INCOME_CATS})
    return render(request, 'tracker/edit_transaction.html', context)

@login_required
def delete_transaction(request, pk):
    user = request.user
    tx = get_object_or_404(Transaction, pk=pk, user=user)
    if request.method == 'POST':
        tx.delete()
        messages.success(request, 'Transaction deleted.')
    return redirect('transactions')

# Analytics
@login_required
def analytics(request):
    user = request.user
    txs = Transaction.objects.filter(user=user)
    # Expense by category (doughnut)
    exp = txs.filter(transaction_type='expense').values('category').annotate(total=Sum('amount')).order_by('-total')
    exp_labels = [e['category'] for e in exp]
    exp_values = [float(e['total']) for e in exp]
    # Monthly expenses (bar)
    monthly = txs.filter(transaction_type='expense').annotate(m=TruncMonth('date')).values('m').annotate(total=Sum('amount')).order_by('m')
    month_labels = [m['m'].strftime('%b %Y') if m['m'] else '' for m in monthly]
    month_values = [float(m['total']) for m in monthly]
    # Income vs Expense comparison (grouped bar / line)
    inc = txs.filter(transaction_type='income').aggregate(s=Sum('amount'))['s'] or Decimal('0')
    exp_total = txs.filter(transaction_type='expense').aggregate(s=Sum('amount'))['s'] or Decimal('0')
    # Spending trend line (daily over last 30 days)
    today = timezone.now().date()
    start30 = today - timedelta(days=29)
    trend = txs.filter(transaction_type='expense', date__gte=start30).values('date').annotate(t=Sum('amount')).order_by('date')
    trend_labels = [(today - timedelta(days=i)).strftime('%b %d') for i in range(29, -1, -1)]
    trend_map = {t['date'].strftime('%Y-%m-%d'): float(t['t']) for t in trend}
    trend_values = [trend_map.get((today - timedelta(days=i)).strftime('%Y-%m-%d'), 0) for i in range(29, -1, -1)]

    context = BASE_CONTEXT.copy()
    context.update({
        'title': 'Analytics',
        'user': user,
        'exp_labels': exp_labels,
        'exp_values': exp_values,
        'month_labels': month_labels,
        'month_values': month_values,
        'income_total': float(inc),
        'expense_total': float(exp_total),
        'trend_labels': trend_labels,
        'trend_values': trend_values,
    })
    return render(request, 'tracker/analytics.html', context)

# Budgets
@login_required
def budgets(request):
    user = request.user
    budgets = Budget.objects.filter(user=user).order_by('category', '-created_at')
    # Calculate spent per budget category for current month
    today = timezone.now().date()
    start = today.replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    spent = txs = Transaction.objects.filter(user=user, transaction_type='expense', date__gte=start, date__lte=end)
    spent_map = {}
    for s in spent.values('category').annotate(total=Sum('amount')):
        spent_map[s['category']] = float(s['total'])
    budget_status = []
    for b in budgets:
        s = spent_map.get(b.category, 0)
        pct = (s / float(b.amount) * 100) if b.amount > 0 else 0
        status = 'safe'
        if pct >= 100:
            status = 'over'
        elif pct >= 90:
            status = 'warning'
        elif pct >= 70:
            status = 'alert'
        budget_status.append({
            'budget': b,
            'spent': s,
            'remaining': float(b.amount) - s,
            'pct': pct,
            'status': status,
        })
    context = BASE_CONTEXT.copy()
    context.update({'title': 'Budgets', 'budgets': budget_status, 'user': user})
    return render(request, 'tracker/budgets.html', context)

@login_required
def add_budget(request):
    user = request.user
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            b = form.save(commit=False)
            b.user = user
            b.save()
            messages.success(request, 'Budget created.')
            return redirect('budgets')
        else:
            messages.error(request, 'Error saving budget.')
    else:
        form = BudgetForm()
    context = BASE_CONTEXT.copy()
    context.update({'title': 'Add Budget', 'form': form, 'user': user, 'expense_cats': EXPENSE_CATS})
    return render(request, 'tracker/add_budget.html', context)

@login_required
def edit_budget(request, pk):
    user = request.user
    budget = get_object_or_404(Budget, pk=pk, user=user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget updated.')
            return redirect('budgets')
    else:
        form = BudgetForm(instance=budget)
    context = BASE_CONTEXT.copy()
    context.update({'title': 'Edit Budget', 'form': form, 'budget': budget, 'user': user})
    return render(request, 'tracker/edit_budget.html', context)

@login_required
def delete_budget(request, pk):
    user = request.user
    budget = get_object_or_404(Budget, pk=pk, user=user)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted.')
    return redirect('budgets')

# Savings Goals
@login_required
def goals(request):
    user = request.user
    goals = SavingsGoal.objects.filter(user=user).order_by('-created_at')
    context = BASE_CONTEXT.copy()
    context.update({'title': 'Savings Goals', 'goals': goals, 'user': user})
    return render(request, 'tracker/goals.html', context)

@login_required
def add_goal(request):
    user = request.user
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            g = form.save(commit=False)
            g.user = user
            g.save()
            messages.success(request, 'Savings goal created.')
            return redirect('goals')
        else:
            messages.error(request, 'Error saving goal.')
    else:
        form = SavingsGoalForm()
    context = BASE_CONTEXT.copy()
    context.update({'title': 'Add Savings Goal', 'form': form, 'user': user})
    return render(request, 'tracker/add_goal.html', context)

@login_required
def edit_goal(request, pk):
    user = request.user
    goal = get_object_or_404(SavingsGoal, pk=pk, user=user)
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Goal updated.')
            return redirect('goals')
    else:
        form = SavingsGoalForm(instance=goal)
    context = BASE_CONTEXT.copy()
    context.update({'title': 'Edit Savings Goal', 'form': form, 'goal': goal, 'user': user})
    return render(request, 'tracker/edit_goal.html', context)

@login_required
def update_goal_amount(request, pk):
    user = request.user
    goal = get_object_or_404(SavingsGoal, pk=pk, user=user)
    if request.method == 'POST':
        amount = request.POST.get('amount', '0')
        try:
            goal.current_amount = Decimal(amount)
            if goal.current_amount > goal.target_amount:
                goal.current_amount = goal.target_amount
            goal.save()
            messages.success(request, 'Progress updated.')
        except Exception:
            messages.error(request, 'Invalid amount.')
    return redirect('goals')

@login_required
def delete_goal(request, pk):
    user = request.user
    goal = get_object_or_404(SavingsGoal, pk=pk, user=user)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted.')
    return redirect('goals')

# Settings
@login_required
def settings_view(request):
    user = request.user
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        currency = request.POST.get('currency', 'INR')
        theme = request.POST.get('theme', 'light')
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, 'Username already taken.')
            else:
                user.username = username
        if email:
            user.email = email
        user.save()
        # Store preferences in session for simplicity
        request.session['currency'] = currency
        request.session['theme'] = theme
        messages.success(request, 'Settings updated.')
    context = BASE_CONTEXT.copy()
    context.update({
        'title': 'Settings',
        'currency': request.session.get('currency', 'INR'),
        'theme': request.session.get('theme', 'light'),
        'user': user,
    })
    return render(request, 'tracker/settings.html', context)

# Health score
@login_required
def health_score(request):
    user = request.user
    txs = Transaction.objects.filter(user=user)
    income = txs.filter(transaction_type='income').aggregate(s=Sum('amount'))['s'] or Decimal('0')
    expense = txs.filter(transaction_type='expense').aggregate(s=Sum('amount'))['s'] or Decimal('0')
    score = 50
    if income > 0:
        ratio = float(expense) / float(income)
        score += max(0, 30 - int(ratio * 30))
    budgets = Budget.objects.filter(user=user)
    budget_adherence = 0
    if budgets.exists():
        today = timezone.now().date()
        start = today.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        spent = Transaction.objects.filter(user=user, transaction_type='expense', date__gte=start, date__lte=end)
        total_budget = sum(float(b.amount) for b in budgets)
        total_spent = float(spent.aggregate(s=Sum('amount'))['s'] or 0)
        budget_adherence = max(0, 20 - int(min(1, total_spent/total_budget)*20)) if total_budget > 0 else 20
    score += budget_adherence
    score = min(100, max(0, score))
    label = 'Good' if score >= 80 else 'Fair' if score >= 60 else 'Needs Work'
    context = BASE_CONTEXT.copy()
    context.update({'title': 'Financial Health', 'score': score, 'label': label, 'user': user})
    return render(request, 'tracker/health.html', context)
