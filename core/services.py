from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import GreaseBatch, StockMovement

def update_batch_statuses():
    """Actualiza los estados de los lotes según su fecha de vencimiento."""
    today = timezone.now().date()
    warning_date = today + timedelta(days=180) # 6 months warning
    
    # Expirados
    GreaseBatch.objects.filter(
        expiration_date__lte=today,
        status__in=['SERVICEABLE', 'NEAR_EXPIRATION']
    ).update(status='EXPIRED')
    
    # Próximos a vencer (asegurar de no pisar vencidos por fecha si alguien los cambió a mano, aunque arriba ya se filtran)
    GreaseBatch.objects.filter(
        expiration_date__gt=today,
        expiration_date__lte=warning_date,
        status__in=['SERVICEABLE', 'EXPIRED'] # Added EXPIRED here to catch retests that are now near expiration
    ).update(status='NEAR_EXPIRATION')
    
    # Revertir lotes extendidos ("Retesteados") a Serviceable si ahora su vencimiento es mayor a 6 meses
    GreaseBatch.objects.filter(
        expiration_date__gt=warning_date,
        status__in=['EXPIRED', 'NEAR_EXPIRATION']
    ).update(status='SERVICEABLE')


@transaction.atomic
def consume_grease(grease_type, quantity_to_consume, user, reference="", reason="", location=None):
    """
    Consume grasa aplicando lógica estricta de vencimiento.
    Retorna True si fue exitoso, lanza ValidationError si no hay stock o hay errores.
    """
    if quantity_to_consume <= 0:
        raise ValidationError("La cantidad a consumir debe ser mayor a cero.")

    # Lotes disponibles: status SERVICEABLE o NEAR_EXPIRATION, ordenados por fecha de vencimiento más próxima
    batches_query = GreaseBatch.objects.filter(
        grease_type=grease_type,
        status__in=['SERVICEABLE', 'NEAR_EXPIRATION'],
        available_quantity__gt=0
    )
    
    if location:
        batches_query = batches_query.filter(storage_location=location)

    available_batches = batches_query.order_by('expiration_date')

    total_available = sum(batch.available_quantity for batch in available_batches)
    
    if total_available < quantity_to_consume:
        raise ValidationError(f"Stock insuficiente para la grasa {grease_type.nomenclatura}. Solicitado: {quantity_to_consume}, Disponible: {total_available}")

    remaining_to_consume = quantity_to_consume

    for batch in available_batches:
        if remaining_to_consume <= 0:
            break

        if batch.available_quantity >= remaining_to_consume:
            # Este lote puede cubrir lo que falta
            consumed_from_this_batch = remaining_to_consume
            batch.available_quantity -= remaining_to_consume
            remaining_to_consume = 0
        else:
            # Se consume todo este lote y se sigue con el próximo
            consumed_from_this_batch = batch.available_quantity
            remaining_to_consume -= batch.available_quantity
            batch.available_quantity = 0

        batch.save()
        
        # Registrar el movimiento auditable
        StockMovement.objects.create(
            batch=batch,
            movement_type='CONSUMPTION',
            quantity_changed=-consumed_from_this_batch,
            user=user,
            reference=reference,
            reason=reason
        )

    return True

def get_procurement_forecast():
    """
    Calculates the procurement forecast using a daily fractional simulation.
    Returns a list of dictionaries, one per GreaseType, containing:
    - grease_type
    - total_available
    - total_projected
    - shortfall (amount missing taking into account expirations over time)
    - plan_details (list of active plans contributing to consumption)
    """
    from datetime import date, timedelta
    from .models import GreaseType
    
    forecast_data = []
    today = date.today()
    
    for gt in GreaseType.objects.all():
        total_available = sum(b.available_quantity for b in gt.batches.filter(status__in=['SERVICEABLE', 'NEAR_EXPIRATION']))
        
        active_req = gt.requirements.filter(status__in=['PENDING', 'ORDERED']).first()
        
        fg = {
            'grease_type': gt,
            'total_available': float(total_available),
            'total_projected': 0.0,
            'shortfall': 0.0,
            'plan_details': [],
            'active_requirement': active_req,
        }
        
        # Gather all plans and daily rates
        plans_to_simulate = []
        for assoc in gt.aircraft_associations.all():
            for plan in assoc.aircraft_model.flight_plans.all():
                if not plan.period_start_date or not plan.period_end_date:
                    continue
                
                total_days = (plan.period_end_date - plan.period_start_date).days + 1
                if total_days <= 0: continue
                
                total_consumption = float(assoc.hourly_consumption_rate * plan.planned_hours)
                daily_consumption = total_consumption / total_days
                
                plans_to_simulate.append({
                    'start': plan.period_start_date,
                    'end': plan.period_end_date,
                    'daily_rate': daily_consumption
                })
                
                fg['plan_details'].append({
                    'aircraft': assoc.aircraft_model,
                    'plan': plan,
                    'rate': assoc.hourly_consumption_rate,
                    'projected': total_consumption
                })
                fg['total_projected'] += total_consumption
        
        if not plans_to_simulate:
            # If no plans, just compute straightforward difference
            fg['shortfall'] = fg['total_projected'] - fg['total_available']
            forecast_data.append(fg)
            continue
            
        # The user requested the difference to be just the real difference between stock and projected consumption.
        # We compute the straightforward difference without simulating daily expirations.
        fg['shortfall'] = fg['total_projected'] - fg['total_available']
        forecast_data.append(fg)
        
    return forecast_data
