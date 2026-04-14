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

# ... Otros catálogos se pueden manejar vía Admin o un form genérico ...

class BudgetCreditForm(forms.ModelForm):
    class Meta:
        model = BudgetCredit
        fields = [
            'fiscal_year', 'ff', 'subprog', 'actividad', 
            'ppp_inc', 'pp_inc', 'pre_inc', 'incisos_agrupado', 
            'inc', 'ppai', 'q1_amount', 'q2_amount', 
            'q3_amount', 'q4_amount', 'notes'
        ]
        widgets = {
            'q1_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'q2_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'q3_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'q4_amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

class BudgetAllocationForm(forms.ModelForm):
    class Meta:
        model = BudgetAllocation
        fields = ['credit', 'unit', 'allocated_amount', 'notes']

class BudgetExecutionCommitmentForm(forms.ModelForm):
    class Meta:
        model = BudgetExecution
        fields = ['allocation', 'reference_code', 'commitment_amount', 'commitment_date']
        widgets = {
            'commitment_date': forms.DateInput(attrs={'type': 'date'}),
        }

class BudgetExecutionAccrualForm(forms.ModelForm):
    class Meta:
        model = BudgetExecution
        fields = ['accrued_amount', 'accrued_date']
        widgets = {
            'accrued_date': forms.DateInput(attrs={'type': 'date'}),
        }

class BudgetExecutionPaymentForm(forms.ModelForm):
    class Meta:
        model = BudgetExecution
        fields = ['paid_amount', 'paid_date']
        widgets = {
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
        }
