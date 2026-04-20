from django import forms
from .models import (
    BudgetFiscalYear, BudgetFF, BudgetSubprog, BudgetProg,
    BudgetPPPInc, BudgetPPInc, BudgetPreInc, BudgetIncisosAgrupado,
    BudgetInc, BudgetCredit, 
    BudgetAllocation, BudgetExecution
)

class BudgetFiscalYearForm(forms.ModelForm):
    class Meta:
        model = BudgetFiscalYear
        fields = ['year', 'status', 'notes']

# --- Formularios de Catálogo ---

class BudgetFFForm(forms.ModelForm):
    class Meta:
        model = BudgetFF
        fields = ['code', 'name']

class BudgetSubprogForm(forms.ModelForm):
    class Meta:
        model = BudgetSubprog
        fields = ['code', 'name']

class BudgetProgForm(forms.ModelForm):
    class Meta:
        model = BudgetProg
        fields = ['code', 'name']

class BudgetPPPIncForm(forms.ModelForm):
    class Meta:
        model = BudgetPPPInc
        fields = ['code', 'name']

class BudgetPPIncForm(forms.ModelForm):
    class Meta:
        model = BudgetPPInc
        fields = ['code', 'name']

class BudgetPreIncForm(forms.ModelForm):
    class Meta:
        model = BudgetPreInc
        fields = ['code', 'name']

class BudgetIncisosAgrupadoForm(forms.ModelForm):
    class Meta:
        model = BudgetIncisosAgrupado
        fields = ['code', 'name']

class BudgetIncForm(forms.ModelForm):
    class Meta:
        model = BudgetInc
        fields = ['code', 'name']


class BudgetCreditForm(forms.ModelForm):
    class Meta:
        model = BudgetCredit
        fields = [
            'fiscal_year', 'ff', 'programa', 'subprog', 'inc',
            'ppp_inc', 'pp_inc', 'pre_inc', 'incisos_agrupado',
            'q1_amount', 'q2_amount', 'q3_amount', 'q4_amount', 'notes'
        ]
        labels = {
            'fiscal_year': 'Ejercicio Económico',
            'ff': 'Fuente de Financiamiento (FF)',
            'programa': 'Programa',
            'subprog': 'Subprograma',
            'inc': 'INCISO',
            'ppp_inc': 'PPAL',
            'pp_inc': 'PARCIAL',
            'pre_inc': 'SUBPC',
            'incisos_agrupado': 'MONEDA',
            'q1_amount': 'Monto 1er Cuatrimestre',
            'q2_amount': 'Monto 2do Cuatrimestre',
            'q3_amount': 'Monto 3er Cuatrimestre',
            'q4_amount': 'Monto 4to Cuatrimestre',
            'notes': 'Observaciones'
        }
        widgets = {
            'q1_amount': forms.TextInput(attrs={'class': 'form-control'}),
            'q2_amount': forms.TextInput(attrs={'class': 'form-control'}),
            'q3_amount': forms.TextInput(attrs={'class': 'form-control'}),
            'q4_amount': forms.TextInput(attrs={'class': 'form-control'}),
        }
        localized_fields = ('q1_amount', 'q2_amount', 'q3_amount', 'q4_amount')

class BudgetAllocationForm(forms.ModelForm):
    class Meta:
        model = BudgetAllocation
        fields = ['credit', 'unit', 'allocated_amount', 'notes']
        widgets = {
            'allocated_amount': forms.TextInput(attrs={'class': 'form-control'}),
        }
        localized_fields = ('allocated_amount',)

class BudgetExecutionCommitmentForm(forms.ModelForm):
    class Meta:
        model = BudgetExecution
        fields = ['allocation', 'reference_code', 'external_id', 'commitment_amount', 'commitment_date']
        labels = {
            'allocation': 'Distribución / Techo Presupuestario',
            'reference_code': 'Número de Expediente / Comprobante',
            'external_id': 'ID de Control Único (Opcional)',
            'commitment_amount': 'Monto a Comprometer',
            'commitment_date': 'Fecha del Compromiso'
        }
        help_texts = {
            'allocation': 'Seleccione la distribución de crédito contra la cual se imputará el gasto.',
            'reference_code': 'Ejemplo: Exp. 123/2026 o Nota Log. 45/26',
            'commitment_amount': 'Ingrese el monto bruto que se reserva para esta operación.',
            'external_id': 'Código único para prevenir registros duplicados (Ej: Nro. Factura o ID de sistema externo).',
        }
        widgets = {
            'commitment_date': forms.DateInput(attrs={'type': 'date'}),
            'commitment_amount': forms.TextInput(attrs={'class': 'form-control'}),
        }
        localized_fields = ('commitment_amount',)

class BudgetExecutionAccrualForm(forms.ModelForm):
    class Meta:
        model = BudgetExecution
        fields = ['accrued_amount', 'accrued_date']
        widgets = {
            'accrued_date': forms.DateInput(attrs={'type': 'date'}),
            'accrued_amount': forms.TextInput(attrs={'class': 'form-control'}),
        }
        localized_fields = ('accrued_amount',)

class BudgetExecutionPaymentForm(forms.ModelForm):
    class Meta:
        model = BudgetExecution
        fields = ['paid_amount', 'paid_date']
        widgets = {
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
            'paid_amount': forms.TextInput(attrs={'class': 'form-control'}),
        }
        localized_fields = ('paid_amount',)
