from django import forms
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from .models import (
    BudgetFiscalYear, BudgetFF, BudgetSubprog, BudgetProg,
    BudgetPPPInc, BudgetPPInc, BudgetPreInc, BudgetIncisosAgrupado,
    BudgetInc, BudgetCredit, BudgetClassification, BudgetCreditType,
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
            'fiscal_year', 'credit_type', 'ff', 'programa', 'subprog', 'inc',
            'ppp_inc', 'pp_inc', 'pre_inc', 'incisos_agrupado',
            'q1_amount', 'q2_amount', 'q3_amount', 'q4_amount', 'notes'
        ]
        labels = {
            'fiscal_year': 'Ejercicio Económico',
            'credit_type': 'Tipo de Crédito',
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
            'q1_amount': forms.TextInput(attrs={'class': 'form-control currency-input', 'placeholder': '0,00'}),
            'q2_amount': forms.TextInput(attrs={'class': 'form-control currency-input', 'placeholder': '0,00'}),
            'q3_amount': forms.TextInput(attrs={'class': 'form-control currency-input', 'placeholder': '0,00'}),
            'q4_amount': forms.TextInput(attrs={'class': 'form-control currency-input', 'placeholder': '0,00'}),
        }
        localized_fields = ('q1_amount', 'q2_amount', 'q3_amount', 'q4_amount')

class CreditChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        available = getattr(obj, 'available_amount', obj.total_amount)
        # Formato de puntos y comas. Reemplazando para evitar locale configs locales
        av_str = f"{available:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{obj} (Disponible para distribuir: ${av_str})"

class BudgetAllocationForm(forms.ModelForm):
    credit = CreditChoiceField(
        queryset=BudgetCredit.objects.none(),
        label="Crédito Origen",
        empty_label="--------- Seleccione un Crédito ---------"
    )
    
    class Meta:
        model = BudgetAllocation
        fields = ['credit', 'unit', 'allocated_amount', 'notes']
        widgets = {
            'allocated_amount': forms.TextInput(attrs={'class': 'form-control currency-input', 'placeholder': '0,00'}),
        }
        localized_fields = ('allocated_amount',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.db import models
        # Annotate available_amount efficiently 
        self.fields['credit'].queryset = BudgetCredit.objects.annotate(
            allocated_total=Coalesce(Sum('allocations__allocated_amount'), 0, output_field=models.DecimalField())
        ).annotate(
            available_amount=F('total_amount') - F('allocated_total')
        ).order_by('-fiscal_year__year', 'ff__code')

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
            'commitment_amount': forms.TextInput(attrs={'class': 'form-control currency-input', 'placeholder': '0,00'}),
        }
        localized_fields = ('commitment_amount',)

class BudgetExecutionAccrualForm(forms.ModelForm):
    class Meta:
        model = BudgetExecution
        fields = ['accrued_amount', 'accrued_date']
        widgets = {
            'accrued_date': forms.DateInput(attrs={'type': 'date'}),
            'accrued_amount': forms.TextInput(attrs={'class': 'form-control currency-input', 'placeholder': '0,00'}),
        }
        localized_fields = ('accrued_amount',)

class BudgetExecutionPaymentForm(forms.ModelForm):
    class Meta:
        model = BudgetExecution
        fields = ['paid_amount', 'paid_date']
        widgets = {
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
            'paid_amount': forms.TextInput(attrs={'class': 'form-control currency-input', 'placeholder': '0,00'}),
        }
        localized_fields = ('paid_amount',)

class BudgetCreditTypeForm(forms.ModelForm):
    class Meta:
        model = BudgetCreditType
        fields = ['code', 'name']
        labels = {'code': 'Código', 'name': 'Nombre / Descripción'}

class BudgetClassificationForm(forms.ModelForm):
    class Meta:
        model = BudgetClassification
        fields = ['name', 'notes']
        labels = {
            'name': 'Nombre de la Clasificación',
            'notes': 'Notas / Descripción'
        }

class BudgetCreditMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        amount_str = f"{obj.total_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{obj} — [Total: ${amount_str}]"

class BudgetClassificationAssignForm(forms.Form):
    # This form is used from the classification perspective to pull credits into itself
    credits = BudgetCreditMultipleChoiceField(
        queryset=BudgetCredit.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Seleccionar Créditos"
    )

    def __init__(self, *args, **kwargs):
        self.classification = kwargs.pop('classification', None)
        super().__init__(*args, **kwargs)
        if self.classification:
            # Set initial checked instances (credit items)
            self.fields['credits'].initial = self.classification.credits.all()
            
            # Since credits have fiscal years, let's limit choices if needed.
            # Right now let's just make sure active fiscal year is considered if any, or order by fiscal_year
            self.fields['credits'].queryset = BudgetCredit.objects.all().select_related(
                'fiscal_year', 'ff', 'programa', 'subprog', 'inc', 'ppp_inc', 'pp_inc', 'pre_inc'
            ).order_by('-fiscal_year__year')
