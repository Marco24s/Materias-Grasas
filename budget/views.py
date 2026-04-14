from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, OuterRef
from .models import (
    BudgetFiscalYear, BudgetFF, BudgetSubprog, BudgetActivity,
    BudgetPPPInc, BudgetPPInc, BudgetPreInc, BudgetIncisosAgrupado,
    BudgetInc, BudgetPPAI, BudgetCredit, BudgetAllocation, BudgetExecution
)
from .forms import (
    BudgetFiscalYearForm, BudgetCreditForm, BudgetAllocationForm,
    BudgetExecutionCommitmentForm, BudgetExecutionAccrualForm, 
    BudgetExecutionPaymentForm
)
from . import services

def is_admin(user):
    return user.is_superuser or user.groups.filter(name__in=['Administrador', 'Logistica']).exists()

def dashboard(request):
    fiscal_year = BudgetFiscalYear.objects.filter(status='OPEN').first()
    stats = {
        'total_credit': 0, 'total_allocated': 0, 'total_commitment': 0,
        'total_accrued': 0, 'total_paid': 0, 'available_to_allocate': 0,
        'available_to_execute': 0
    }
    unit_report = []
    if fiscal_year:
        if is_admin(request.user):
            credits = BudgetCredit.objects.filter(fiscal_year=fiscal_year)
            allocations = BudgetAllocation.objects.filter(credit__fiscal_year=fiscal_year)
            executions = BudgetExecution.objects.filter(allocation__credit__fiscal_year=fiscal_year)
            unit_report = services.get_unit_execution_report(fiscal_year)
        else:
            credits = BudgetCredit.objects.filter(fiscal_year=fiscal_year, allocations__unit=request.user.unit)
            allocations = BudgetAllocation.objects.filter(credit__fiscal_year=fiscal_year, unit=request.user.unit)
            executions = BudgetExecution.objects.filter(allocation__unit=request.user.unit)
            full_report = services.get_unit_execution_report(fiscal_year)
            unit_report = [r for r in full_report if r['unit'] == request.user.unit]

        stats['total_credit'] = credits.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        stats['total_allocated'] = allocations.aggregate(Sum('allocated_amount'))['allocated_amount__sum'] or 0
        stats['total_commitment'] = executions.aggregate(Sum('commitment_amount'))['commitment_amount__sum'] or 0
        stats['total_accrued'] = executions.aggregate(Sum('accrued_amount'))['accrued_amount__sum'] or 0
        stats['total_paid'] = executions.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
        stats['available_to_allocate'] = stats['total_credit'] - stats['total_allocated']
        stats['available_to_execute'] = stats['total_allocated'] - stats['total_commitment']

    return render(request, 'budget/dashboard.html', {'fiscal_year': fiscal_year, 'stats': stats, 'unit_report': unit_report, 'is_admin': is_admin(request.user)})

def fiscal_year_list(request):
    if not is_admin(request.user): return redirect('budget:dashboard')
    years = BudgetFiscalYear.objects.all().order_by('-year')
    return render(request, 'budget/fiscal_year_list.html', {'years': years})

def fiscal_year_create(request):
    if not is_admin(request.user): return redirect('budget:dashboard')
    if request.method == 'POST':
        form = BudgetFiscalYearForm(request.POST)
        if form.is_valid():
            services.create_fiscal_year(year=form.cleaned_data['year'], notes=form.cleaned_data['notes'])
            return redirect('budget:fiscal_year_list')
    else: form = BudgetFiscalYearForm()
    return render(request, 'budget/form_base.html', {'form': form, 'title': 'Crear Ejercicio Económico'})

def fiscal_year_close(request, pk):
    if not is_admin(request.user): return redirect('budget:dashboard')
    year = get_object_or_404(BudgetFiscalYear, pk=pk)
    all_executions = BudgetExecution.objects.filter(allocation__credit__fiscal_year=year)
    pending_reprogram = []
    for e in all_executions:
        if e.commitment_amount > e.accrued_amount:
            e.pending_balance = e.commitment_amount - e.accrued_amount
            pending_reprogram.append(e)
    if request.method == 'POST':
        services.close_fiscal_year(year)
        return redirect('budget:fiscal_year_list')
    return render(request, 'budget/fiscal_year_close.html', {'year': year, 'pending_reprogram': pending_reprogram})

def credit_list(request):
    if is_admin(request.user):
        credits = BudgetCredit.objects.all().order_by('inc__code', 'ppai__code')
    else:
        credits = BudgetCredit.objects.filter(allocations__unit=request.user.unit).distinct()
    return render(request, 'budget/credit_list.html', {'credits': credits})

def credit_create(request):
    if not is_admin(request.user): return redirect('budget:credit_list')
    if request.method == 'POST':
        form = BudgetCreditForm(request.POST)
        if form.is_valid():
            try:
                services.create_credit(
                    fiscal_year=form.cleaned_data['fiscal_year'],
                    ff=form.cleaned_data['ff'], subprog=form.cleaned_data['subprog'],
                    actividad=form.cleaned_data['actividad'], ppp_inc=form.cleaned_data['ppp_inc'],
                    pp_inc=form.cleaned_data['pp_inc'], pre_inc=form.cleaned_data['pre_inc'],
                    incisos_agrupado=form.cleaned_data['incisos_agrupado'], 
                    inc=form.cleaned_data['inc'], ppai=form.cleaned_data['ppai'],
                    q1=form.cleaned_data['q1_amount'], q2=form.cleaned_data['q2_amount'],
                    q3=form.cleaned_data['q3_amount'], q4=form.cleaned_data['q4_amount'],
                    notes=form.cleaned_data['notes']
                )
                return redirect('budget:credit_list')
            except Exception as e:
                messages.error(request, f"Error: {e}")
    else: form = BudgetCreditForm()
    return render(request, 'budget/form_base.html', {'form': form, 'title': 'Registrar Crédito Presupuestario'})

def allocation_list(request):
    if is_admin(request.user): allocations = BudgetAllocation.objects.all()
    else: allocations = BudgetAllocation.objects.filter(unit=request.user.unit)
    return render(request, 'budget/allocation_list.html', {'allocations': allocations})

def allocation_create(request):
    if not is_admin(request.user): return redirect('budget:allocation_list')
    if request.method == 'POST':
        form = BudgetAllocationForm(request.POST)
        if form.is_valid():
            try:
                services.allocate_credit(credit=form.cleaned_data['credit'], unit=form.cleaned_data['unit'], amount=form.cleaned_data['allocated_amount'], notes=form.cleaned_data['notes'])
                return redirect('budget:allocation_list')
            except Exception as e: messages.error(request, f"Error: {e}")
    else: form = BudgetAllocationForm()
    return render(request, 'budget/form_base.html', {'form': form, 'title': 'Distribuir Crédito a Unidad'})

def execution_list(request):
    if is_admin(request.user): executions = BudgetExecution.objects.all()
    else: executions = BudgetExecution.objects.filter(allocation__unit=request.user.unit)
    return render(request, 'budget/execution_list.html', {'executions': executions.order_by('-created_at')})

def execution_detail(request, pk):
    execution = get_object_or_404(BudgetExecution, pk=pk)
    if not is_admin(request.user) and execution.allocation.unit != request.user.unit: return redirect('budget:execution_list')
    return render(request, 'budget/execution_detail.html', {'execution': execution})

def execution_step_commitment(request):
    if request.method == 'POST':
        form = BudgetExecutionCommitmentForm(request.POST)
        if form.is_valid():
            alloc = form.cleaned_data['allocation']
            try:
                services.register_commitment(allocation=alloc, reference_code=form.cleaned_data['reference_code'], amount=form.cleaned_data['commitment_amount'], commitment_date=form.cleaned_data['commitment_date'], user=request.user)
                return redirect('budget:execution_list')
            except Exception as e: messages.error(request, f"Error: {e}")
    else:
        form = BudgetExecutionCommitmentForm()
        if not is_admin(request.user): form.fields['allocation'].queryset = BudgetAllocation.objects.filter(unit=request.user.unit)
    return render(request, 'budget/form_base.html', {'form': form, 'title': 'Paso 1: Registro de Compromiso'})

def execution_step_accrual(request, pk):
    execution = get_object_or_404(BudgetExecution, pk=pk)
    if request.method == 'POST':
        form = BudgetExecutionAccrualForm(request.POST, instance=execution)
        if form.is_valid():
            try:
                services.register_accrual(execution=execution, amount=form.cleaned_data['accrued_amount'], accrued_date=form.cleaned_data['accrued_date'])
                return redirect('budget:execution_detail', pk=pk)
            except Exception as e: messages.error(request, f"Error: {e}")
    else: form = BudgetExecutionAccrualForm(instance=execution)
    return render(request, 'budget/form_base.html', {'form': form, 'title': f'Paso 2: Devengado ({execution.reference_code})'})

def execution_step_payment(request, pk):
    execution = get_object_or_404(BudgetExecution, pk=pk)
    if request.method == 'POST':
        form = BudgetExecutionPaymentForm(request.POST, instance=execution)
        if form.is_valid():
            try:
                services.register_payment(execution=execution, amount=form.cleaned_data['paid_amount'], paid_date=form.cleaned_data['paid_date'])
                return redirect('budget:execution_detail', pk=pk)
            except Exception as e: messages.error(request, f"Error: {e}")
    else: form = BudgetExecutionPaymentForm(instance=execution)
    return render(request, 'budget/form_base.html', {'form': form, 'title': f'Paso 3: Pago ({execution.reference_code})'})
