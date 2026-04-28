from django.db import models
from core.models import Unit, CustomUser

class InsufficientFundsError(Exception):
    """Excepción lanzada cuando no hay saldo disponible en el techo presupuestario."""
    pass

class BudgetFiscalYear(models.Model):
    year = models.PositiveIntegerField(unique=True, verbose_name="Año / Ejercicio")
    status = models.CharField(max_length=10, choices=[('OPEN', 'Abierto'), ('CLOSED', 'Cerrado')], default='OPEN', verbose_name="Estado")
    notes = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    class Meta: verbose_name = "Ejercicio Económico"; verbose_name_plural = "Ejercicios Económicos"; ordering = ['-year']
    def __str__(self): return f"Ejercicio {self.year} ({self.get_status_display()})"

class BudgetFF(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="Código FF")
    name = models.CharField(max_length=100, verbose_name="Descripción FF", blank=True)
    class Meta: verbose_name = "Fuente"; verbose_name_plural = "Fuentes"
    def __str__(self): return f"{self.code} - {self.name}" if self.name else self.code

class BudgetCreditType(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="Código")
    name = models.CharField(max_length=150, verbose_name="Nombre / Descripción")
    class Meta: verbose_name = "Tipo de Crédito"; verbose_name_plural = "Tipos de Crédito"
    def __str__(self): return f"{self.code} - {self.name}"

class BudgetSubprog(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="Código SUBPROG")
    name = models.CharField(max_length=100, verbose_name="Descripción SUBPROG", blank=True)
    class Meta: verbose_name = "Subprograma"; verbose_name_plural = "Subprogramas"
    def __str__(self): return f"{self.code} - {self.name}" if self.name else self.code

class BudgetProg(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código PROG")
    name = models.CharField(max_length=255, verbose_name="Nombre Programa")
    class Meta: verbose_name = "Programa"; verbose_name_plural = "Programas"
    def __str__(self): return f"{self.code} - {self.name}"

class BudgetPPPInc(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código PPAL")
    name = models.CharField(max_length=100, blank=True, verbose_name="Nombre PPAL")
    class Meta: verbose_name = "PPAL"; verbose_name_plural = "PPALs"
    def __str__(self): return f"{self.code} - {self.name}" if self.name else self.code

class BudgetPPInc(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código PARCIAL")
    name = models.CharField(max_length=100, blank=True, verbose_name="Nombre PARCIAL")
    class Meta: verbose_name = "PARCIAL"; verbose_name_plural = "PARCIALes"
    def __str__(self): return f"{self.code} - {self.name}" if self.name else self.code

class BudgetPreInc(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código SUBPC")
    name = models.CharField(max_length=100, blank=True, verbose_name="Nombre SUBPC")
    class Meta: verbose_name = "SUBPC"; verbose_name_plural = "SUBPCs"
    def __str__(self): return f"{self.code} - {self.name}" if self.name else self.code

class BudgetIncisosAgrupado(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código MONEDA")
    name = models.CharField(max_length=100, blank=True, verbose_name="Nombre MONEDA")
    class Meta: verbose_name = "MONEDA"; verbose_name_plural = "MONEDAs"
    def __str__(self): return f"{self.code} - {self.name}" if self.name else self.code

class BudgetInc(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="Código INCISO")
    name = models.CharField(max_length=100, blank=True, verbose_name="Nombre INCISO")
    class Meta: verbose_name = "INCISO"; verbose_name_plural = "INCISOs"
    def __str__(self): return f"{self.code} - {self.name}" if self.name else self.code


class BudgetClassification(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Clasificación")
    notes = models.TextField(blank=True, null=True, verbose_name="Descripción / Notas")
    
    class Meta:
        verbose_name = "Clasificación Personalizada"
        verbose_name_plural = "Clasificaciones Personalizadas"
        
    def __str__(self):
        return self.name


class BudgetCredit(models.Model):
    fiscal_year = models.ForeignKey(BudgetFiscalYear, on_delete=models.PROTECT, related_name="credits", verbose_name="Ejercicio")
    custom_class = models.ForeignKey(BudgetClassification, on_delete=models.SET_NULL, null=True, blank=True, related_name='credits', verbose_name="Clasificación Especial")
    credit_type = models.ForeignKey(BudgetCreditType, on_delete=models.PROTECT, null=True, blank=True, related_name='credits', verbose_name="Tipo de Crédito")
    ff = models.ForeignKey(BudgetFF, on_delete=models.PROTECT, verbose_name="FF", null=True, blank=True)
    programa = models.ForeignKey(BudgetProg, on_delete=models.PROTECT, verbose_name="Programa", null=True, blank=True)
    subprog = models.ForeignKey(BudgetSubprog, on_delete=models.PROTECT, verbose_name="SUBPROG", null=True, blank=True)
    inc = models.ForeignKey(BudgetInc, on_delete=models.PROTECT, verbose_name="INCISO", null=True, blank=True)
    ppp_inc = models.ForeignKey(BudgetPPPInc, on_delete=models.PROTECT, verbose_name="PPAL", null=True, blank=True)
    pp_inc = models.ForeignKey(BudgetPPInc, on_delete=models.PROTECT, verbose_name="PARCIAL", null=True, blank=True)
    pre_inc = models.ForeignKey(BudgetPreInc, on_delete=models.PROTECT, verbose_name="SUBPC", null=True, blank=True)
    incisos_agrupado = models.ForeignKey(BudgetIncisosAgrupado, on_delete=models.PROTECT, verbose_name="MONEDA", null=True, blank=True)
    q1_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    q2_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    q3_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    q4_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    class Meta:
        verbose_name = "Crédito Presupuestario"
        verbose_name_plural = "Créditos Presupuestarios"
        unique_together = ('fiscal_year', 'ff', 'programa', 'subprog', 'inc', 'ppp_inc', 'pp_inc', 'pre_inc', 'incisos_agrupado')

    def __str__(self):
        parts = []
        parts.append(self.ff.code if self.ff else "?")
        parts.append(self.programa.code if self.programa else "00")
        parts.append(self.subprog.code if self.subprog else "00")
        parts.append(self.inc.code if self.inc else "?")
        parts.append(self.ppp_inc.code if self.ppp_inc else "?")
        parts.append(self.pp_inc.code if self.pp_inc else "?")
        parts.append(self.pre_inc.code if self.pre_inc else "?")
        parts.append(self.incisos_agrupado.code if self.incisos_agrupado else "?")
        return "-".join(parts)
    def save(self, *args, **kwargs):
        self.total_amount = self.q1_amount + self.q2_amount + self.q3_amount + self.q4_amount
        super().save(*args, **kwargs)

class BudgetAllocation(models.Model):
    credit = models.ForeignKey(BudgetCredit, on_delete=models.PROTECT, related_name="allocations", verbose_name="Crédito Origen")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="budget_allocations", verbose_name="Unidad Destino")
    allocated_amount = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="Monto Asignado (Techo)")
    spent_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="Monto Comprometido (Acumulado)")
    notes = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    class Meta: 
        verbose_name = "Distribución de Crédito"
        verbose_name_plural = "Distribuciones de Crédito"
        unique_together = ('credit', 'unit')
    
    @property
    def available_amount(self):
        return self.allocated_amount - self.spent_amount

    def __str__(self): return f"{self.unit.name} - ${self.allocated_amount}"

class BudgetExecution(models.Model):
    allocation = models.ForeignKey(BudgetAllocation, on_delete=models.PROTECT, related_name="executions", verbose_name="Distribución / Techo")
    reference_code = models.CharField(max_length=100, verbose_name="Nro. Expediente / Referencia")
    external_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="ID de Control Único (Opcional)", help_text="Código para evitar registros duplicados (Ej: Nro. Factura, ID de sistema externo, etc).")
    commitment_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="Monto Comprometido")
    commitment_date = models.DateField(verbose_name="Fecha de Compromiso")
    accrued_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="Monto Devengado")
    accrued_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Devengado")
    paid_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="Monto Pagado")
    paid_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Pago")
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, verbose_name="Usuario")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    class Meta:
        verbose_name = "Ejecución Presupuestaria"
        verbose_name_plural = "Ejecuciones Presupuestarias"
    def __str__(self): return self.reference_code


class BudgetCreditTypeLog(models.Model):
    ACTION_ASSIGN = 'ASSIGN'
    ACTION_UNASSIGN = 'UNASSIGN'
    ACTION_CHANGE = 'CHANGE'
    ACTION_CHOICES = [
        (ACTION_ASSIGN, 'Asignación'),
        (ACTION_UNASSIGN, 'Desasignación'),
        (ACTION_CHANGE, 'Cambio de Tipo'),
    ]

    credit = models.ForeignKey(BudgetCredit, on_delete=models.CASCADE, related_name='type_logs', verbose_name="Crédito")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="Acción")
    previous_type = models.ForeignKey(BudgetCreditType, on_delete=models.SET_NULL, null=True, blank=True, related_name='unassigned_logs', verbose_name="Tipo Anterior")
    new_type = models.ForeignKey(BudgetCreditType, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_logs', verbose_name="Tipo Nuevo")
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, verbose_name="Realizado por")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")
    notes = models.TextField(blank=True, null=True, verbose_name="Motivo / Observaciones")

    class Meta:
        verbose_name = "Registro de Cambio de Tipo"
        verbose_name_plural = "Registros de Cambios de Tipo"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_display()} — {self.credit} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"
