from django.db import models
from core.models import Unit, CustomUser

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

class BudgetSubprog(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="Código SUBPROG")
    name = models.CharField(max_length=100, verbose_name="Descripción SUBPROG", blank=True)
    class Meta: verbose_name = "Subprograma"; verbose_name_plural = "Subprogramas"
    def __str__(self): return f"{self.code} - {self.name}" if self.name else self.code

class BudgetActivity(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código ACT")
    name = models.CharField(max_length=255, verbose_name="Nombre Actividad")
    class Meta: verbose_name = "Actividad General"; verbose_name_plural = "Actividades"
    def __str__(self): return self.name

class BudgetPPPInc(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="PPP-INC")
    name = models.CharField(max_length=100, blank=True)
    class Meta: verbose_name = "PPP-INC"; verbose_name_plural = "PPP-INCs"
    def __str__(self): return self.code

class BudgetPPInc(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="PP-INC")
    name = models.CharField(max_length=100, blank=True)
    class Meta: verbose_name = "PP-INC"; verbose_name_plural = "PP-INCs"
    def __str__(self): return self.code

class BudgetPreInc(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Pre-inc")
    name = models.CharField(max_length=100, blank=True)
    class Meta: verbose_name = "Pre-inciso"; verbose_name_plural = "Pre-incisos"
    def __str__(self): return self.code

class BudgetIncisosAgrupado(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Incisos")
    name = models.CharField(max_length=100, blank=True)
    class Meta: verbose_name = "Incisos Agrupados"; verbose_name_plural = "Incisos Agrupados"
    def __str__(self): return self.code

class BudgetInc(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="INC")
    name = models.CharField(max_length=100, blank=True)
    class Meta: verbose_name = "Inciso"; verbose_name_plural = "Incisos"
    def __str__(self): return self.code

class BudgetPPAI(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="PPAI")
    name = models.CharField(max_length=100, blank=True)
    class Meta: verbose_name = "PPAI"; verbose_name_plural = "PPAIs"
    def __str__(self): return self.code

class BudgetCredit(models.Model):
    fiscal_year = models.ForeignKey(BudgetFiscalYear, on_delete=models.PROTECT, related_name="credits", verbose_name="Ejercicio")
    ff = models.ForeignKey(BudgetFF, on_delete=models.PROTECT, verbose_name="FF")
    subprog = models.ForeignKey(BudgetSubprog, on_delete=models.PROTECT, verbose_name="SUBPROG")
    actividad = models.ForeignKey(BudgetActivity, on_delete=models.PROTECT, verbose_name="Actividad")
    ppp_inc = models.ForeignKey(BudgetPPPInc, on_delete=models.PROTECT, verbose_name="PPP-INC")
    pp_inc = models.ForeignKey(BudgetPPInc, on_delete=models.PROTECT, verbose_name="PP-INC")
    pre_inc = models.ForeignKey(BudgetPreInc, on_delete=models.PROTECT, verbose_name="Pre-inc")
    incisos_agrupado = models.ForeignKey(BudgetIncisosAgrupado, on_delete=models.PROTECT, verbose_name="Incisos")
    inc = models.ForeignKey(BudgetInc, on_delete=models.PROTECT, verbose_name="INC")
    ppai = models.ForeignKey(BudgetPPAI, on_delete=models.PROTECT, verbose_name="PPAI")
    q1_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    q2_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    q3_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    q4_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    class Meta:
        verbose_name = "Crédito Presupuestario"
        verbose_name_plural = "Créditos Presupuestarios"
        unique_together = ('fiscal_year', 'ff', 'subprog', 'actividad', 'inc', 'ppai')
    def __str__(self): return f"{self.ff.code}-{self.subprog.code}-{self.inc.code}-{self.ppai.code}"
    def save(self, *args, **kwargs):
        self.total_amount = self.q1_amount + self.q2_amount + self.q3_amount + self.q4_amount
        super().save(*args, **kwargs)

class BudgetAllocation(models.Model):
    credit = models.ForeignKey(BudgetCredit, on_delete=models.CASCADE, related_name="allocations")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="budget_allocations")
    allocated_amount = models.DecimalField(max_digits=18, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    class Meta: unique_together = ('credit', 'unit')
    def __str__(self): return f"{self.unit.name} - {self.allocated_amount}"

class BudgetExecution(models.Model):
    allocation = models.ForeignKey(BudgetAllocation, on_delete=models.CASCADE, related_name="executions")
    reference_code = models.CharField(max_length=100)
    commitment_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    commitment_date = models.DateField()
    accrued_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    accrued_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    paid_date = models.DateField(null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.reference_code
