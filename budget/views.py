from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, OuterRef
from .models import (
    BudgetFiscalYear, BudgetFF, BudgetSubprog, BudgetActivity,
    BudgetPPPInc, BudgetPPInc, BudgetPreInc, BudgetIncisosAgrupado,
    BudgetInc, BudgetPPAI, BudgetCredit, BudgetAllocation, BudgetExecution,
    InsufficientFundsError
)
from .forms import (
    BudgetFiscalYearForm, BudgetCreditForm, BudgetAllocationForm,
    BudgetExecutionCommitmentForm, BudgetExecutionAccrualForm, 
    BudgetExecutionPaymentForm,
    BudgetFFForm, BudgetSubprogForm, BudgetActivityForm,
    BudgetPPPIncForm, BudgetPPIncForm, BudgetPreIncForm,
    BudgetIncisosAgrupadoForm, BudgetIncForm, BudgetPPAIForm
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

def fiscal_year_update(request, pk):
    if not is_admin(request.user): return redirect('budget:dashboard')
    year = get_object_or_404(BudgetFiscalYear, pk=pk)
    if request.method == 'POST':
        form = BudgetFiscalYearForm(request.POST, instance=year)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ejercicio {year.year} actualizado.")
            return redirect('budget:fiscal_year_list')
    else:
        form = BudgetFiscalYearForm(instance=year)
    return render(request, 'budget/form_base.html', {'form': form, 'title': f'Editar Ejercicio {year.year}'})

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

def credit_detail(request, pk):
    credit = get_object_or_404(BudgetCredit, pk=pk)
    if not is_admin(request.user) and not credit.allocations.filter(unit=request.user.unit).exists():
        return redirect('budget:credit_list')
        
    allocations = credit.allocations.all().select_related('unit')
    total_allocated = allocations.aggregate(Sum('allocated_amount'))['allocated_amount__sum'] or 0
    available_to_allocate = credit.total_amount - total_allocated
    
    # Calculate execution percentage for the whole credit if it's distributed
    total_spent = allocations.aggregate(Sum('spent_amount'))['spent_amount__sum'] or 0
    execution_percent = (total_spent / total_allocated * 100) if total_allocated > 0 else 0
    
    context = {
        'credit': credit,
        'allocations': allocations,
        'total_allocated': total_allocated,
        'available_to_allocate': available_to_allocate,
        'total_spent': total_spent,
        'execution_percent': execution_percent,
    }
    return render(request, 'budget/credit_detail.html', context)

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
                error_msg = ", ".join(e.messages) if hasattr(e, 'messages') else str(e)
                messages.error(request, f"Error: {error_msg}")
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
            except Exception as e:
                error_msg = ", ".join(e.messages) if hasattr(e, 'messages') else str(e)
                messages.error(request, f"Error: {error_msg}")
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
                services.register_commitment(
                    allocation_id=alloc.pk, 
                    reference_code=form.cleaned_data['reference_code'], 
                    external_id=form.cleaned_data.get('external_id'),
                    amount=form.cleaned_data['commitment_amount'], 
                    commitment_date=form.cleaned_data['commitment_date'], 
                    user=request.user
                )
                messages.success(request, "Compromiso registrado exitosamente.")
                return redirect('budget:execution_list')
            except InsufficientFundsError as e:
                messages.error(request, str(e))
            except Exception as e:
                error_msg = ", ".join(e.messages) if hasattr(e, 'messages') else str(e)
                messages.error(request, f"Ocurrió un error inesperado: {error_msg}")
    else:
        form = BudgetExecutionCommitmentForm()
        if not is_admin(request.user):
            form.fields['allocation'].queryset = BudgetAllocation.objects.filter(unit=request.user.unit)
            
    help_text = "Para registrar un compromiso, primero debe existir una Distribución de Crédito (Techo) asignada a la unidad. Si no ve opciones en el desplegable, contacte a Logística para la distribución de fondos."
    return render(request, 'budget/form_base.html', {
        'form': form, 
        'title': 'Paso 1: Registro de Compromiso',
        'help_text': help_text
    })

def execution_step_accrual(request, pk):
    execution = get_object_or_404(BudgetExecution, pk=pk)
    if request.method == 'POST':
        form = BudgetExecutionAccrualForm(request.POST, instance=execution)
        if form.is_valid():
            try:
                services.register_accrual(execution=execution, amount=form.cleaned_data['accrued_amount'], accrued_date=form.cleaned_data['accrued_date'])
                return redirect('budget:execution_detail', pk=pk)
            except Exception as e:
                error_msg = ", ".join(e.messages) if hasattr(e, 'messages') else str(e)
                messages.error(request, f"Error: {error_msg}")
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
            except Exception as e:
                error_msg = ", ".join(e.messages) if hasattr(e, 'messages') else str(e)
                messages.error(request, f"Error: {error_msg}")
    else: form = BudgetExecutionPaymentForm(instance=execution)
    return render(request, 'budget/form_base.html', {'form': form, 'title': f'Paso 3: Pago ({execution.reference_code})'})
# --- Gestión de Nomencladores (Configuración) ---

def nomenclature_dashboard(request):
    if not is_admin(request.user): return redirect('budget:dashboard')
    
    catalogs = [
        {'id': 'ff', 'name': 'Fuentes de Financiamiento (FF)', 'model': BudgetFF, 'icon': 'fa-money-bill'},
        {'id': 'subprog', 'name': 'Subprogramas', 'model': BudgetSubprog, 'icon': 'fa-diagram-project'},
        {'id': 'activity', 'name': 'Actividades Generales', 'model': BudgetActivity, 'icon': 'fa-tasks'},
        {'id': 'inc', 'name': 'Incisos Principales', 'model': BudgetInc, 'icon': 'fa-folder-open'},
        {'id': 'ppai', 'name': 'PPAIs (Objetos de Gasto)', 'model': BudgetPPAI, 'icon': 'fa-tag'},
        {'id': 'pppinc', 'name': 'PPP-INC', 'model': BudgetPPPInc, 'icon': 'fa-list-ol'},
        {'id': 'ppinc', 'name': 'PP-INC', 'model': BudgetPPInc, 'icon': 'fa-list-ol'},
        {'id': 'preinc', 'name': 'Pre-incisos', 'model': BudgetPreInc, 'icon': 'fa-list-ol'},
        {'id': 'inc_agrup', 'name': 'Incisos Agrupados / Otros', 'model': BudgetIncisosAgrupado, 'icon': 'fa-boxes-stacked'},
    ]
    
    # Add counts to each catalog
    for cat in catalogs:
        cat['count'] = cat['model'].objects.count()
        
    return render(request, 'budget/nomenclature_dashboard.html', {'catalogs': catalogs})

def nomenclature_list(request, catalog_type):
    if not is_admin(request.user): return redirect('budget:dashboard')
    
    config = _get_catalog_config(catalog_type)
    if not config: return redirect('budget:nomenclature_dashboard')
    
    items = config['model'].objects.all().order_by('code' if hasattr(config['model'], 'code') else 'id')
    return render(request, 'budget/nomenclature_list.html', {
        'items': items,
        'config': config,
        'title': f"Catálogo: {config['name']}"
    })

def nomenclature_create(request, catalog_type):
    if not is_admin(request.user): return redirect('budget:dashboard')
    
    config = _get_catalog_config(catalog_type)
    if not config: return redirect('budget:nomenclature_dashboard')
    
    if request.method == 'POST':
        form = config['form_class'](request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"{config['model']._meta.verbose_name} creado exitosamente.")
            return redirect('budget:nomenclature_list', catalog_type=catalog_type)
    else:
        form = config['form_class']()
        
    return render(request, 'budget/form_base.html', {
        'form': form,
        'title': f"Agregar {config['model']._meta.verbose_name}",
        'config': config
    })

def nomenclature_update(request, catalog_type, pk):
    if not is_admin(request.user): return redirect('budget:dashboard')
    
    config = _get_catalog_config(catalog_type)
    if not config: return redirect('budget:nomenclature_dashboard')
    
    instance = get_object_or_404(config['model'], pk=pk)
    
    if request.method == 'POST':
        form = config['form_class'](request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"{config['model']._meta.verbose_name} actualizado exitosamente.")
            return redirect('budget:nomenclature_list', catalog_type=catalog_type)
    else:
        form = config['form_class'](instance=instance)
        
    return render(request, 'budget/form_base.html', {
        'form': form,
        'title': f"Editar {config['model']._meta.verbose_name}",
        'config': config
    })

def nomenclature_delete(request, catalog_type, pk):
    if not is_admin(request.user): return redirect('budget:dashboard')
    
    config = _get_catalog_config(catalog_type)
    if not config: return redirect('budget:nomenclature_dashboard')
    
    instance = get_object_or_404(config['model'], pk=pk)
    
    if request.method == 'POST':
        try:
            instance.delete()
            messages.success(request, f"{config['model']._meta.verbose_name} eliminado exitosamente.")
        except Exception as e:
            messages.error(request, f"No se pudo eliminar: {e}")
        return redirect('budget:nomenclature_list', catalog_type=catalog_type)
        
    return render(request, 'budget/confirm_delete.html', {
        'object': instance,
        'title': f"Eliminar {config['model']._meta.verbose_name}",
        'cancel_url': 'budget:nomenclature_list'
    })

def _get_catalog_config(catalog_type):
    configs = {
        'ff': {'id': 'ff', 'model': BudgetFF, 'form_class': BudgetFFForm, 'name': 'Fuentes de Financiamiento'},
        'subprog': {'id': 'subprog', 'model': BudgetSubprog, 'form_class': BudgetSubprogForm, 'name': 'Subprogramas'},
        'activity': {'id': 'activity', 'model': BudgetActivity, 'form_class': BudgetActivityForm, 'name': 'Actividades Generales'},
        'pppinc': {'id': 'pppinc', 'model': BudgetPPPInc, 'form_class': BudgetPPPIncForm, 'name': 'PPP-INC'},
        'ppinc': {'id': 'ppinc', 'model': BudgetPPInc, 'form_class': BudgetPPIncForm, 'name': 'PP-INC'},
        'preinc': {'id': 'preinc', 'model': BudgetPreInc, 'form_class': BudgetPreIncForm, 'name': 'Pre-incisos'},
        'inc_agrup': {'id': 'inc_agrup', 'model': BudgetIncisosAgrupado, 'form_class': BudgetIncisosAgrupadoForm, 'name': 'Incisos Agrupados'},
        'inc': {'id': 'inc', 'model': BudgetInc, 'form_class': BudgetIncForm, 'name': 'Incisos'},
        'ppai': {'id': 'ppai', 'model': BudgetPPAI, 'form_class': BudgetPPAIForm, 'name': 'PPAIs'},
    }
    return configs.get(catalog_type)
