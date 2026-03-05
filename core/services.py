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
def consume_grease(grease_type, quantity_to_consume, user, reference="", reason=""):
    """
    Consume grasa aplicando lógica estricta de vencimiento.
    Retorna True si fue exitoso, lanza ValidationError si no hay stock o hay errores.
    """
    if quantity_to_consume <= 0:
        raise ValidationError("La cantidad a consumir debe ser mayor a cero.")

    # Lotes disponibles: status SERVICEABLE o NEAR_EXPIRATION, ordenados por fecha de vencimiento más próxima
    available_batches = GreaseBatch.objects.filter(
        grease_type=grease_type,
        status__in=['SERVICEABLE', 'NEAR_EXPIRATION'],
        available_quantity__gt=0
    ).order_by('expiration_date')

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
