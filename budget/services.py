from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum
from .models import (
    BudgetFiscalYear, BudgetFF, BudgetSubprog, BudgetActivity,
    BudgetPPPInc, BudgetPPInc, BudgetPreInc, BudgetIncisosAgrupado,
    BudgetInc, BudgetPPAI, BudgetCredit, BudgetAllocation, BudgetExecution
)

@transaction.atomic
def create_fiscal_year(year, notes=""):
    if BudgetFiscalYear.objects.filter(year=year).exists():
        raise ValidationError(f"El ejercicio {year} ya existe.")
    return BudgetFiscalYear.objects.create(year=year, notes=notes)


@transaction.atomic
def create_credit(fiscal_year, ff, subprog, actividad, ppp_inc, pp_inc, pre_inc, 
                  incisos_agrupado, inc, ppai, q1=0, q2=0, q3=0, q4=0, notes=""):
    """
    Registra un nuevo crédito presupuestario utilizando objetos de catálogo.
    """
    if fiscal_year.status == 'CLOSED':
        raise ValidationError("No se puede registrar crédito en un ejercicio cerrado.")
    
    return BudgetCredit.objects.create(
        fiscal_year=fiscal_year,
        ff=ff, subprog=subprog, actividad=actividad,
        ppp_inc=ppp_inc, pp_inc=pp_inc, pre_inc=pre_inc,
        incisos_agrupado=incisos_agrupado, inc=inc, ppai=ppai,
        q1_amount=q1, q2_amount=q2, q3_amount=q3, q4_amount=q4,
        notes=notes
    )


@transaction.atomic
def allocate_credit(credit, unit, amount, notes=""):
    if amount <= 0:
        raise ValidationError("El monto a distribuir debe ser positivo.")

    allocated_total = credit.allocations.aggregate(Sum('allocated_amount'))['allocated_amount__sum'] or 0
    if allocated_total + amount > credit.total_amount:
        raise ValidationError(
            f"La distribución supera el monto total del crédito disponible (${credit.total_amount}). "
        )
    
    return BudgetAllocation.objects.create(
        credit=credit, unit=unit, allocated_amount=amount, notes=notes
    )


@transaction.atomic
def register_commitment(allocation, reference_code, amount, commitment_date, user):
    if amount <= 0:
        raise ValidationError("El monto del compromiso debe ser positivo.")
    if allocation.credit.fiscal_year.status == 'CLOSED':
        raise ValidationError("No se pueden registrar gastos en un ejercicio cerrado.")

    executed_commitment_total = allocation.executions.aggregate(Sum('commitment_amount'))['commitment_amount__sum'] or 0
    if executed_commitment_total + amount > allocation.allocated_amount:
        raise ValidationError(f"Supera el crédito disponible (${allocation.allocated_amount - executed_commitment_total}).")
        
    return BudgetExecution.objects.create(
        allocation=allocation, reference_code=reference_code,
        commitment_amount=amount, commitment_date=commitment_date, user=user
    )


@transaction.atomic
def register_accrual(execution, amount, accrued_date):
    if amount < 0: raise ValidationError("Monto negativo.")
    if amount > execution.commitment_amount:
        raise ValidationError("No puede superar el compromiso.")
    execution.accrued_amount = amount
    execution.accrued_date = accrued_date
    execution.save()
    return execution


@transaction.atomic
def register_payment(execution, amount, paid_date):
    if amount < 0: raise ValidationError("Monto negativo.")
    if amount > execution.accrued_amount:
        raise ValidationError("No puede superar el devengado.")
    execution.paid_amount = amount
    execution.paid_date = paid_date
    execution.save()
    return execution


@transaction.atomic
def close_fiscal_year(fiscal_year):
    fiscal_year.status = 'CLOSED'
    fiscal_year.save()
    return True


def reprogram_commitment(original_execution, target_allocation, user):
    if original_execution.accrued_amount > 0:
        raise ValueError("Solo compromisos no devengados.")
    if target_allocation.credit.fiscal_year.status == 'CLOSED':
        raise ValueError("Ejercicio de destino cerrado.")
    amount = original_execution.commitment_amount
    executed_total = target_allocation.executions.aggregate(Sum('commitment_amount'))['commitment_amount__sum'] or 0
    available = target_allocation.allocated_amount - executed_total
    if available < amount:
        raise ValueError(f"Faltan ${amount - available} en el nuevo ejercicio.")
    return register_commitment(
        allocation=target_allocation, reference_code=f"REP-{original_execution.reference_code}",
        amount=amount, commitment_date=timezone.now(), user=user
    )


def get_unit_execution_report(fiscal_year):
    from core.models import Unit
    report = []
    units = Unit.objects.filter(budget_allocations__credit__fiscal_year=fiscal_year).distinct()
    for unit in units:
        allocations = BudgetAllocation.objects.filter(unit=unit, credit__fiscal_year=fiscal_year)
        total_allocated = allocations.aggregate(Sum('allocated_amount'))['allocated_amount__sum'] or 0
        executions = BudgetExecution.objects.filter(allocation__in=allocations)
        tc = executions.aggregate(Sum('commitment_amount'))['commitment_amount__sum'] or 0
        ta = executions.aggregate(Sum('accrued_amount'))['accrued_amount__sum'] or 0
        tp = executions.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
        report.append({
            'unit': unit, 'allocated': total_allocated, 'commitment': tc,
            'accrued': ta, 'paid': tp, 'available': total_allocated - tc,
            'residuos': tc - ta, 'deuda_flotante': ta - tp,
            'percent_executed': (tc / total_allocated * 100) if total_allocated > 0 else 0
        })
    return report
