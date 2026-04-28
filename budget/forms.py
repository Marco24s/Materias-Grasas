from django import forms
from .models import (
    BudgetFiscalYear, BudgetFF, BudgetSubprog, BudgetActivity,
    BudgetPPPInc, BudgetPPInc, BudgetPreInc, BudgetIncisosAgrupado,
    BudgetInc, BudgetPPAI, BudgetCredit, 
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

class BudgetActivityForm(forms.ModelForm):
    class Meta:
        model = BudgetActivity
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

class BudgetPPAIForm(forms.ModelForm):
    class Meta:
        model = BudgetPPAI
        fields = ['code', 'name']

class BudgetCreditForm(forms.ModelForm):
    class Meta:
        model = BudgetCredit
        fields = [
            'fiscal_year', 'ff', 'subprog', 'actividad', 
            'ppp_inc', 'pp_inc', 'pre_inc', 'incisos_agrupado', 
            'inc', 'ppai', 'q1_amount', 'q2_amount', 
            'q3_amount', 'q4_amount', 'notes'
        ]
        labels = {
            'fiscal_year': 'Ejercicio Económico',
            'ff': 'Fuente de Financiamiento (FF)',
            'subprog': 'Subprograma',
            'actividad': 'Actividad General',
            'ppp_inc': 'PPP-INC',
            'pp_inc': 'PP-INC',
            'pre_inc': 'Pre-inciso',
            'incisos_agrupado': 'Sub-Incisos',
            'inc': 'Inciso Principal',
            'ppai': 'PPAI (Objeto de Gasto)',
            'q1_amount': 'Monto 1er Cuatrimestre',
            'q2_amount': 'Monto 2do Cuatrimestre',
            'q3_amount': 'Monto 3er Cuatrimestre',
            'q4_amount': 'Monto 4to Cuatrimestre',
            'notes': 'Observaciones'
        }
        widgets = {
            'q1_amount': forms.TextInput(attrs={'class': 'currency-input', 'placeholder': '0,00'}),
            'q2_amount': forms.TextInput(attrs={'class': 'currency-input', 'placeholder': '0,00'}),
            'q3_amount': forms.TextInput(attrs={'class': 'currency-input', 'placeholder': '0,00'}),
            'q4_amount': forms.TextInput(attrs={'class': 'currency-input', 'placeholder': '0,00'}),
        }

class BudgetAllocationForm(forms.ModelForm):
    class Meta:
        model = BudgetAllocation
        fields = ['credit', 'unit', 'allocated_amount', 'notes']
        widgets = {
            'allocated_amount': forms.TextInput(attrs={'class': 'currency-input', 'placeholder': '0,00'}),
        }

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
            'commitment_amount': forms.TextInput(attrs={'class': 'currency-input', 'placeholder': '0,00'}),
        }

class BudgetExecutionAccrualForm(forms.ModelForm):
    class Meta:
        model = BudgetExecution
        fields = ['accrued_amount', 'accrued_date']
        widgets = {
            'accrued_date': forms.DateInput(attrs={'type': 'date'}),
            'accrued_amount': forms.TextInput(attrs={'class': 'currency-input', 'placeholder': '0,00'}),
        }

class BudgetExecutionPaymentForm(forms.ModelForm):
    class Meta:
        model = BudgetExecution
        fields = ['paid_amount', 'paid_date']
        widgets = {
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
            'paid_amount': forms.TextInput(attrs={'class': 'currency-input', 'placeholder': '0,00'}),
        }
