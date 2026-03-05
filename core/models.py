from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
    # En proyectos institucionales, un CustomUser desde el principio es la mejor práctica
    # Añadiremos campos extra más adelante si el cliente lo requiere (ej. Rango, Destino, etc)
    pass

class Unit(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Unidad")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Unidad"
        verbose_name_plural = "Unidades"

    def __str__(self):
        return self.name

class AircraftModel(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Modelo de Aeronave")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="aircrafts", verbose_name="Unidad / Escuadra")
    total_aircraft = models.PositiveIntegerField(default=1, verbose_name="Cantidad de Aeronaves")
    is_active = models.BooleanField(default=True, verbose_name="Operativa (Activa)")

    class Meta:
        verbose_name = "Modelo de Aeronave"
        verbose_name_plural = "Modelos de Aeronaves"

    def __str__(self):
        return f"{self.name} ({self.unit.name})"

class GreaseType(models.Model):
    unidad = models.CharField(max_length=50, verbose_name="UNIDAD")
    presentacion = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="PRESENTACIÓN")
    nomenclatura = models.CharField(max_length=150, unique=True, verbose_name="NOMENCLATURA")
    nne_nsn = models.CharField(max_length=100, verbose_name="N.N.E. / N.S.N.", blank=True, null=True)
    sibys = models.CharField(max_length=100, verbose_name="SIBYS", blank=True, null=True)
    nato = models.CharField(max_length=100, verbose_name="NATO", blank=True, null=True)
    normas_mil_otras = models.CharField(max_length=200, verbose_name="NORMAS MIL / OTRAS", blank=True, null=True)
    
    shelf_life_months = models.PositiveIntegerField(verbose_name="Vida Útil Total (Meses)")
    recertification_allowed = models.BooleanField(default=False, verbose_name="Permite Re-certificación")

    class Meta:
        verbose_name = "Tipo de Grasa / Aceite"
        verbose_name_plural = "Tipos de Grasas / Aceites"

    def __str__(self):
        return f"{self.nomenclatura} ({self.presentacion} {self.unidad})"

class AircraftGrease(models.Model):
    aircraft_model = models.ForeignKey(AircraftModel, on_delete=models.CASCADE, related_name="grease_associations", verbose_name="Modelo de Aeronave")
    grease_type = models.ForeignKey(GreaseType, on_delete=models.CASCADE, related_name="aircraft_associations", verbose_name="Tipo de Grasa")
    hourly_consumption_rate = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Consumo por Hora de Vuelo")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas (Punto de aplicación)")

    class Meta:
        verbose_name = "Asociación Aeronave-Grasa"
        verbose_name_plural = "Asociaciones Aeronave-Grasa"
        unique_together = ('aircraft_model', 'grease_type')

    def __str__(self):
        return f"{self.aircraft_model.name} -> {self.grease_type.nomenclatura}"

class FlightPlan(models.Model):
    PERIOD_CHOICES = [
        ('MONTHLY', 'Mensual'),
        ('QUARTERLY', 'Trimestral'),
        ('YEARLY', 'Anual'),
    ]
    aircraft_model = models.ForeignKey(AircraftModel, on_delete=models.CASCADE, related_name="flight_plans", verbose_name="Modelo de Aeronave")
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES, verbose_name="Tipo de Período")
    period_start_date = models.DateField(verbose_name="Fecha de Inicio del Plan")
    planned_hours = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Horas de Vuelo Planificadas")
    
    class Meta:
        verbose_name = "Plan de Vuelo"
        verbose_name_plural = "Planes de Vuelo"

    def __str__(self):
        return f"Plan {self.get_period_type_display()} - {self.aircraft_model.name} ({self.planned_hours} hs)"

    def get_projected_consumption(self):
        """Calcula el consumo proyectado para este plan basado en las tasas de consumo."""
        consumptions = []
        for assoc in self.aircraft_model.grease_associations.all():
            consumptions.append({
                'grease_type': assoc.grease_type,
                'projected_amount': assoc.hourly_consumption_rate * self.planned_hours
            })
        return consumptions

class GreaseBatch(models.Model):
    STATUS_CHOICES = [
        ('SERVICEABLE', 'Retesteable'),
        ('NEAR_EXPIRATION', 'Próximo a Vencer'),
        ('EXPIRED', 'Vencido'),
        ('PENDING_RECERTIFICATION', 'Pendiente Re-certificación'),
    ]

    grease_type = models.ForeignKey(GreaseType, on_delete=models.CASCADE, related_name="batches", verbose_name="Tipo de Grasa")
    batch_number = models.CharField(max_length=100, verbose_name="Número de Lote")
    manufacturing_date = models.DateField(verbose_name="Fecha de Fabricación")
    expiration_date = models.DateField(verbose_name="Fecha de Vencimiento")
    initial_quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad Inicial")
    available_quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad Disponible")
    storage_location = models.CharField(max_length=100, verbose_name="Ubicación (Almacén/Unidad)")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='SERVICEABLE', verbose_name="Estado")

    class Meta:
        verbose_name = "Lote de Grasa"
        verbose_name_plural = "Lotes de Grasas"
        unique_together = ('grease_type', 'batch_number')

    def __str__(self):
        return f"Lote {self.batch_number} - {self.grease_type.nomenclatura}"
        
    def clean(self):
        if self.available_quantity is not None and self.initial_quantity is not None:
            if self.available_quantity > self.initial_quantity:
                raise ValidationError("La cantidad disponible no puede ser mayor a la cantidad inicial.")

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('INCOMING', 'Ingreso inicial'),
        ('CONSUMPTION', 'Consumo operativo'),
        ('ADJUSTMENT', 'Ajuste de inventario/Auditoría'),
    ]
    batch = models.ForeignKey(GreaseBatch, on_delete=models.PROTECT, related_name="movements", verbose_name="Lote")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, verbose_name="Tipo de Movimiento")
    quantity_changed = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad Alterada (+ o -)")
    movement_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora del Movimiento")
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, verbose_name="Usuario Responsable")
    reference = models.CharField(max_length=255, blank=True, null=True, verbose_name="Referencia (Nro Remito / Plan Vuelo)")
    reason = models.TextField(blank=True, null=True, verbose_name="Motivo / Observaciones")

    class Meta:
        verbose_name = "Movimiento de Stock (Auditoría)"
        verbose_name_plural = "Movimientos de Stock (Auditoría)"
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.batch.batch_number} ({self.quantity_changed})"

    def delete(self, *args, **kwargs):
        raise ValidationError("Los movimientos de stock son estrictamente de auditoría y NO PUEDEN SER ELIMINADOS.")
