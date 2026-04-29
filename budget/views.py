from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from django.contrib import messages
from django.db.models import Sum, F, OuterRef, ProtectedError
from .models import (
    BudgetFiscalYear, BudgetFF, BudgetSubprog, BudgetProg,
    BudgetPPPInc, BudgetPPInc, BudgetPreInc, BudgetIncisosAgrupado,
    BudgetInc, BudgetCredit, BudgetAllocation, BudgetExecution,
    BudgetClassification, BudgetCreditType, BudgetCreditTypeLog, InsufficientFundsError
)
from .forms import (
    BudgetFiscalYearForm, BudgetCreditForm, BudgetAllocationForm,
    BudgetExecutionCommitmentForm, BudgetExecutionAccrualForm, 
    BudgetExecutionPaymentForm,
    BudgetFFForm, BudgetSubprogForm, BudgetProgForm,
    BudgetPPPIncForm, BudgetPPIncForm, BudgetPreIncForm,
    BudgetIncisosAgrupadoForm, BudgetIncForm,
    BudgetClassificationForm, BudgetClassificationAssignForm,
    BudgetCreditTypeForm
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
        
        # Agregación por trimestre
        stats['q1_total'] = credits.aggregate(Sum('q1_amount'))['q1_amount__sum'] or 0
        stats['q2_total'] = credits.aggregate(Sum('q2_amount'))['q2_amount__sum'] or 0
        stats['q3_total'] = credits.aggregate(Sum('q3_amount'))['q3_amount__sum'] or 0
        stats['q4_total'] = credits.aggregate(Sum('q4_amount'))['q4_amount__sum'] or 0

        # Cálculo de anchos para la barra de progreso trimestral (basado en compromisos)
        total_q = stats['total_credit']
        rem_c = stats['total_commitment']
        
        q1_t, q2_t, q3_t, q4_t = stats['q1_total'], stats['q2_total'], stats['q3_total'], stats['q4_total']
        
        stats['q1_fill'] = (min(rem_c, q1_t) / q1_t * 100) if q1_t > 0 else 0
        rem_c = max(0, rem_c - q1_t)
        stats['q2_fill'] = (min(rem_c, q2_t) / q2_t * 100) if q2_t > 0 else 0
        rem_c = max(0, rem_c - q2_t)
        stats['q3_fill'] = (min(rem_c, q3_t) / q3_t * 100) if q3_t > 0 else 0
        rem_c = max(0, rem_c - q3_t)
        stats['q4_fill'] = (min(rem_c, q4_t) / q4_t * 100) if q4_t > 0 else 0
        
        stats['q1_seg'] = (q1_t / total_q * 100) if total_q > 0 else 0
        stats['q2_seg'] = (q2_t / total_q * 100) if total_q > 0 else 0
        stats['q3_seg'] = (q3_t / total_q * 100) if total_q > 0 else 0
        stats['q4_seg'] = (q4_t / total_q * 100) if total_q > 0 else 0

        # Desglose por Tipo de Crédito
        stats['credit_by_type'] = (
            credits.filter(credit_type__isnull=False)
            .values('credit_type__name', 'credit_type__code')
            .annotate(subtotal=Sum('total_amount'))
            .order_by('credit_type__code')
        )

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
        credits = BudgetCredit.objects.all().order_by(
            'fiscal_year', 'ff', 'programa', 'subprog',
            'inc__code', 'ppp_inc__code', 'pp_inc__code', 
            'pre_inc__code', 'incisos_agrupado__code'
        )
    else:
        credits = BudgetCredit.objects.filter(allocations__unit=request.user.unit).distinct()
        
    credit_by_type = (
        credits.filter(credit_type__isnull=False)
        .values('credit_type__name', 'credit_type__code')
        .annotate(subtotal=Sum('total_amount'))
        .order_by('credit_type__name')
    )
    unassigned_total = credits.filter(credit_type__isnull=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    return render(request, 'budget/credit_list.html', {
        'credits': credits,
        'credit_by_type': credit_by_type,
        'unassigned_total': unassigned_total
    })

def credit_detail(request, pk):
    credit = get_object_or_404(BudgetCredit, pk=pk)
    if not is_admin(request.user) and not credit.allocations.filter(unit=request.user.unit).exists():
        return redirect('budget:credit_list')
        
    allocations = credit.allocations.all().select_related('unit')
    total_allocated = allocations.aggregate(Sum('allocated_amount'))['allocated_amount__sum'] or 0
    available_to_allocate = credit.total_amount - total_allocated
    
    # Calcular anchos para la barra de progreso segmentada
    total = credit.total_amount
    q1, q2, q3, q4 = credit.q1_amount, credit.q2_amount, credit.q3_amount, credit.q4_amount
    
    rem = total_allocated
    q1_fill = (min(rem, q1) / q1 * 100) if q1 > 0 else 0
    rem = max(0, rem - q1)
    q2_fill = (min(rem, q2) / q2 * 100) if q2 > 0 else 0
    rem = max(0, rem - q2)
    q3_fill = (min(rem, q3) / q3 * 100) if q3 > 0 else 0
    rem = max(0, rem - q3)
    q4_fill = (min(rem, q4) / q4 * 100) if q4 > 0 else 0
    
    # Ancho relativo de cada segmento (trimestre) respecto al total
    q1_seg = (q1 / total * 100) if total > 0 else 0
    q2_seg = (q2 / total * 100) if total > 0 else 0
    q3_seg = (q3 / total * 100) if total > 0 else 0
    q4_seg = (q4 / total * 100) if total > 0 else 0

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
        'q_fills': [q1_fill, q2_fill, q3_fill, q4_fill],
        'q_segs': [q1_seg, q2_seg, q3_seg, q4_seg],
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
                    credit_type=form.cleaned_data.get('credit_type'),
                    ff=form.cleaned_data['ff'], 
                    programa=form.cleaned_data['programa'],
                    subprog=form.cleaned_data['subprog'],
                    inc=form.cleaned_data['inc'],
                    ppp_inc=form.cleaned_data['ppp_inc'],
                    pp_inc=form.cleaned_data['pp_inc'], 
                    pre_inc=form.cleaned_data['pre_inc'],
                    incisos_agrupado=form.cleaned_data['incisos_agrupado'], 
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

def credit_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Solo los superusuarios pueden eliminar créditos.")
        return redirect('budget:credit_list')
    
    credit = get_object_or_404(BudgetCredit, pk=pk)
    
    if request.method == 'POST':
        try:
            credit.delete()
            messages.success(request, "Crédito presupuestario eliminado exitosamente.")
            return redirect('budget:credit_list')
        except ProtectedError:
            messages.error(request, "No se puede eliminar este crédito porque ya tiene distribuciones asignadas a unidades. Debe eliminar las distribuciones primero.")
            return redirect('budget:credit_list')
        
    return render(request, 'budget/confirm_delete.html', {
        'object': credit,
        'title': f"Eliminar Crédito: {credit}",
        'cancel_url': 'budget:credit_list'
    })


def credit_unassign_type(request, pk):
    """Removes the credit_type from a single credit with an optional reason, logging the event."""
    if not is_admin(request.user): return redirect('budget:credit_list')
    credit = get_object_or_404(BudgetCredit, pk=pk)
    
    if not credit.credit_type:
        messages.warning(request, "Este crédito ya no tiene un tipo asignado.")
        return redirect('budget:credit_list')
    
    def parse_currency(value):
        if not value:
            return None
        value = str(value).replace(' ', '')
        if ',' in value:
            # Formato español: los puntos son miles, la coma es decimal
            raw = value.replace('.', '').replace(',', '.')
        else:
            # Ya limpio por JS o formato punto-decimal: el punto es decimal
            raw = value
        return Decimal(raw)

    if request.method == 'POST':
        current_amount_txt = request.POST.get('current_amount', '').strip()
        unassign_amount_txt = request.POST.get('unassign_amount', '').strip()
        notes_txt = request.POST.get('notes', '').strip()
        current_amount = None
        unassign_amount = None
        has_error = False

        if current_amount_txt:
            try:
                current_amount = parse_currency(current_amount_txt)
            except Exception:
                messages.error(request, "El monto actual ingresado no es válido.")
                has_error = True
        if unassign_amount_txt:
            try:
                unassign_amount = parse_currency(unassign_amount_txt)
            except Exception:
                messages.error(request, "El monto a desasignar ingresado no es válido.")
                has_error = True

        if has_error:
            return render(request, 'budget/credit_unassign_confirm.html', {
                'credit': credit,
                'current_amount': current_amount_txt,
                'unassign_amount': unassign_amount_txt,
                'notes': notes_txt
            })

        details = []
        if current_amount is not None:
            details.append(f"Monto crédito: ${current_amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        if unassign_amount is not None:
            details.append(f"Monto desasignado: ${unassign_amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        if notes_txt:
            details.append(notes_txt)

        notes = ' | '.join(details) if details else None

        services.unassign_credit_type(
            credit=credit,
            unassign_amount=unassign_amount,
            user=request.user,
            notes=notes
        )
        
        success_msg = f"Tipo de crédito removido de {credit}."
        if unassign_amount and unassign_amount > 0:
            formatted_amount = f"${unassign_amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            success_msg += f" Se descontaron {formatted_amount} del total."
            
        messages.success(request, success_msg)
        return redirect('budget:credit_list')

    return render(request, 'budget/credit_unassign_confirm.html', {
        'credit': credit,
        'current_amount': credit.total_amount,
        'unassign_amount': '',
        'notes': ''
    })

def credit_type_log(request):
    """Shows the full audit log of credit type assignment changes."""
    if not is_admin(request.user): return redirect('budget:dashboard')
    logs = BudgetCreditTypeLog.objects.all().select_related('credit', 'previous_type', 'new_type', 'user').order_by('-timestamp')
    return render(request, 'budget/credit_type_log.html', {'logs': logs})

def allocation_list(request):
    if is_admin(request.user): allocations = BudgetAllocation.objects.all()
    else: allocations = BudgetAllocation.objects.filter(unit=request.user.unit)
    return render(request, 'budget/allocation_list.html', {'allocations': allocations})

def allocation_create(request):
    if not is_admin(request.user): return redirect('budget:allocation_list')
    
    credit_id = request.GET.get('credit')
    fixed_credit = None
    initial = {}
    
    if credit_id:
        fixed_credit = get_object_or_404(BudgetCredit, pk=credit_id)
        initial['credit'] = fixed_credit.pk
        
    if request.method == 'POST':
        form = BudgetAllocationForm(request.POST)
        if form.is_valid():
            try:
                services.allocate_credit(
                    credit=form.cleaned_data['credit'], 
                    unit=form.cleaned_data['unit'], 
                    amount=form.cleaned_data['allocated_amount'], 
                    notes=form.cleaned_data['notes']
                )
                if fixed_credit:
                    return redirect('budget:credit_detail', pk=fixed_credit.pk)
                return redirect('budget:allocation_list')
            except Exception as e:
                error_msg = ", ".join(e.messages) if hasattr(e, 'messages') else str(e)
                messages.error(request, f"Error: {error_msg}")
    else:
        form = BudgetAllocationForm(initial=initial)
    
    if fixed_credit:
        form.fields['credit'].widget = forms.HiddenInput()
        
    return render(request, 'budget/form_base.html', {
        'form': form, 
        'title': 'Distribuir Crédito a Unidad',
        'fixed_credit': fixed_credit
    })

def allocation_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Solo los superusuarios pueden eliminar distribuciones.")
        return redirect('budget:allocation_list')
    
    allocation = get_object_or_404(BudgetAllocation, pk=pk)
    
    if request.method == 'POST':
        try:
            allocation.delete()
            messages.success(request, "Distribución de crédito eliminada exitosamente.")
            return redirect('budget:allocation_list')
        except ProtectedError:
            messages.error(request, "No se puede eliminar esta distribución porque ya tiene gastos (ejecuciones) registrados. Debe eliminar los gastos asociados primero.")
            return redirect('budget:allocation_list')
        
    return render(request, 'budget/confirm_delete.html', {
        'object': allocation,
        'title': f"Eliminar Distribución: {allocation}",
        'cancel_url': 'budget:allocation_list'
    })

def execution_list(request):
    if is_admin(request.user): executions = BudgetExecution.objects.all()
    else: executions = BudgetExecution.objects.filter(allocation__unit=request.user.unit)
    return render(request, 'budget/execution_list.html', {'executions': executions.order_by('-created_at')})

def execution_detail(request, pk):
    execution = get_object_or_404(BudgetExecution, pk=pk)
    if not is_admin(request.user) and execution.allocation.unit != request.user.unit: return redirect('budget:execution_list')
    surplus = execution.commitment_amount - execution.accrued_amount if execution.commitment_amount > execution.accrued_amount else 0
    return render(request, 'budget/execution_detail.html', {'execution': execution, 'surplus': surplus})

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

def execution_release_surplus(request, pk):
    """
    Controlador para liberar el saldo comprometido de un gasto.
    """
    execution = get_object_or_404(BudgetExecution, pk=pk)
    
    # Seguridad básica
    if not is_admin(request.user) and execution.allocation.unit != request.user.unit:
        messages.error(request, "No tiene permisos para realizar esta acción.")
        return redirect('budget:execution_detail', pk=pk)
        
    try:
        from . import services
        execution, surplus = services.release_commitment_surplus(pk, request.user)
        messages.success(request, f"Se han liberado ${surplus} exitosamente. El monto comprometido ahora coincide con el devengado.")
    except Exception as e:
        error_msg = ", ".join(e.messages) if hasattr(e, 'messages') else str(e)
        messages.error(request, f"No se pudo liberar el saldo: {error_msg}")
        
    return redirect('budget:execution_detail', pk=pk)

def execution_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado. Solo los superusuarios pueden borrar ejecuciones.")
        return redirect('budget:execution_list')
        
    execution = get_object_or_404(BudgetExecution, pk=pk)
    
    if request.method == 'POST':
        try:
            from . import services
            amount = services.delete_execution(pk, request.user)
            messages.success(request, f"Ejecución borrada exitosamente. Se restituyeron ${amount} al crédito de la unidad.")
            return redirect('budget:execution_list')
        except Exception as e:
            messages.error(request, f"Error al borrar: {str(e)}")
            return redirect('budget:execution_detail', pk=pk)
            
    return render(request, 'budget/confirm_delete.html', {
        'object': execution,
        'title': f"Borrar Ejecución: {execution.reference_code}",
        'cancel_url': 'budget:execution_list'
    })

# --- Gestión de Nomencladores (Configuración) ---


def nomenclature_dashboard(request):
    if not is_admin(request.user): return redirect('budget:dashboard')
    
    catalogs = [
        {'id': 'ff', 'name': 'Fuentes de Financiamiento (FF)', 'model': BudgetFF, 'icon': 'fa-money-bill'},
        {'id': 'program', 'name': 'Programas', 'model': BudgetProg, 'icon': 'fa-tasks'},
        {'id': 'subprog', 'name': 'Subprogramas', 'model': BudgetSubprog, 'icon': 'fa-diagram-project'},
        {'id': 'inc', 'name': 'INCISOs', 'model': BudgetInc, 'icon': 'fa-folder-open'},
        {'id': 'pppinc', 'name': 'PPALs', 'model': BudgetPPPInc, 'icon': 'fa-list-ol'},
        {'id': 'ppinc', 'name': 'PARCIALes', 'model': BudgetPPInc, 'icon': 'fa-list-ol'},
        {'id': 'preinc', 'name': 'SUBPCs', 'model': BudgetPreInc, 'icon': 'fa-list-ol'},
        {'id': 'inc_agrup', 'name': 'MONEDAs', 'model': BudgetIncisosAgrupado, 'icon': 'fa-boxes-stacked'},
        {'id': 'credit_type', 'name': 'Tipos de Crédito', 'model': BudgetCreditType, 'icon': 'fa-tags'},
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
        'program': {'id': 'program', 'model': BudgetProg, 'form_class': BudgetProgForm, 'name': 'Programas'},
        'subprog': {'id': 'subprog', 'model': BudgetSubprog, 'form_class': BudgetSubprogForm, 'name': 'Subprogramas'},
        'pppinc': {'id': 'pppinc', 'model': BudgetPPPInc, 'form_class': BudgetPPPIncForm, 'name': 'PPALs'},
        'ppinc': {'id': 'ppinc', 'model': BudgetPPInc, 'form_class': BudgetPPIncForm, 'name': 'PARCIALes'},
        'preinc': {'id': 'preinc', 'model': BudgetPreInc, 'form_class': BudgetPreIncForm, 'name': 'SUBPCs'},
        'inc_agrup': {'id': 'inc_agrup', 'model': BudgetIncisosAgrupado, 'form_class': BudgetIncisosAgrupadoForm, 'name': 'MONEDAs'},
        'inc': {'id': 'inc', 'model': BudgetInc, 'form_class': BudgetIncForm, 'name': 'INCISOs'},
        'credit_type': {'id': 'credit_type', 'model': BudgetCreditType, 'form_class': BudgetCreditTypeForm, 'name': 'Tipos de Crédito'},
    }
    return configs.get(catalog_type)

# --- Clasificaciones Personalizadas ---

def classification_list(request):
    classes = BudgetClassification.objects.annotate(
        total_assigned=Sum('credits__total_amount')
    ).order_by('name')
    
    grand_total = sum((c.total_assigned or Decimal('0')) for c in classes)
    
    return render(request, 'budget/classification_list.html', {
        'classes': classes,
        'grand_total': grand_total
    })

def classification_create(request):
    if request.method == 'POST':
        form = BudgetClassificationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Clasificación creada.")
            return redirect('budget:classification_list')
    else:
        form = BudgetClassificationForm()
    return render(request, 'budget/form_base.html', {'form': form, 'title': 'Nueva Clasificación'})

def classification_update(request, pk):
    c = get_object_or_404(BudgetClassification, pk=pk)
    if request.method == 'POST':
        form = BudgetClassificationForm(request.POST, instance=c)
        if form.is_valid():
            form.save()
            messages.success(request, "Clasificación actualizada.")
            return redirect('budget:classification_list')
    else:
        form = BudgetClassificationForm(instance=c)
    return render(request, 'budget/form_base.html', {'form': form, 'title': f'Editar Clasificación: {c.name}'})

def classification_delete(request, pk):
    c = get_object_or_404(BudgetClassification, pk=pk)
    if request.method == 'POST':
        c.delete()
        messages.success(request, "Clasificación eliminada.")
        return redirect('budget:classification_list')
    return render(request, 'budget/confirm_delete.html', {
        'object': c, 
        'title': f'Eliminar Clasificación: {c.name}',
        'cancel_url': 'budget:classification_list'
    })

def classification_assign(request, pk):
    c = get_object_or_404(BudgetClassification, pk=pk)
    if request.method == 'POST':
        form = BudgetClassificationAssignForm(request.POST, classification=c)
        if form.is_valid():
            selected_credits = form.cleaned_data['credits']
            
            # Remove this classification from any credits that aren't selected anymore
            c.credits.exclude(id__in=selected_credits).update(custom_class=None)
            
            # Assing this classification to the selected credits
            for credit in selected_credits:
                credit.custom_class = c
                credit.save(update_fields=['custom_class'])
                
            messages.success(request, f"Créditos asignados a {c.name}.")
            return redirect('budget:classification_list')
    else:
        form = BudgetClassificationAssignForm(classification=c)
        
    return render(request, 'budget/classification_assign.html', {'form': form, 'classification': c})

def classification_detail(request, pk):
    classification = get_object_or_404(BudgetClassification, pk=pk)
    credits = classification.credits.all().select_related(
        'fiscal_year', 'ff', 'programa', 'subprog', 'inc', 'ppp_inc', 'pp_inc', 'pre_inc'
    )
    
    total_assigned = Decimal('0')
    total_allocated = Decimal('0')
    total_spent = Decimal('0')
    total_accrued = Decimal('0')
    total_paid = Decimal('0')
    
    credit_details = []
    
    for cr in credits:
        allocated = BudgetAllocation.objects.filter(credit=cr).aggregate(Sum('allocated_amount'))['allocated_amount__sum'] or Decimal('0')
        spent = BudgetAllocation.objects.filter(credit=cr).aggregate(Sum('spent_amount'))['spent_amount__sum'] or Decimal('0')
        
        execs_stats = BudgetExecution.objects.filter(allocation__credit=cr).aggregate(
            t_accrued=Sum('accrued_amount'),
            t_paid=Sum('paid_amount')
        )
        accrued = execs_stats['t_accrued'] or Decimal('0')
        paid = execs_stats['t_paid'] or Decimal('0')
        
        total_assigned += cr.total_amount
        total_allocated += allocated
        total_spent += spent
        total_accrued += accrued
        total_paid += paid
        
        credit_details.append({
            'credit': cr,
            'allocated': allocated,
            'spent': spent,
            'accrued': accrued,
            'paid': paid,
        })
        
    stats = {
        'total_assigned': total_assigned,
        'total_allocated': total_allocated,
        'total_spent': total_spent,
        'total_accrued': total_accrued,
        'total_paid': total_paid,
        'available_to_allocate': total_assigned - total_allocated,
        'available_to_execute': total_allocated - total_spent
    }

    return render(request, 'budget/classification_detail.html', {
        'classification': classification,
        'stats': stats,
        'credit_details': credit_details
    })

