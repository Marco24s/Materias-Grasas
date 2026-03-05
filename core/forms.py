from django import forms
from .models import Unit, AircraftModel, GreaseType, AircraftGrease, FlightPlan, GreaseBatch

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'description']

class AircraftModelForm(forms.ModelForm):
    class Meta:
        model = AircraftModel
        fields = ['name', 'unit', 'total_aircraft', 'is_active']

class GreaseTypeForm(forms.ModelForm):
    class Meta:
        model = GreaseType
        fields = ['nomenclatura', 'unidad', 'presentacion', 'nne_nsn', 'sibys', 'nato', 'normas_mil_otras', 'shelf_life_months', 'recertification_allowed']

class AircraftGreaseForm(forms.ModelForm):
    class Meta:
        model = AircraftGrease
        fields = ['aircraft_model', 'grease_type', 'hourly_consumption_rate', 'notes']

class FlightPlanForm(forms.ModelForm):
    class Meta:
        model = FlightPlan
        fields = ['aircraft_model', 'period_type', 'period_start_date', 'planned_hours']
        widgets = {
            'period_start_date': forms.DateInput(attrs={'type': 'date'})
        }

class GreaseBatchForm(forms.ModelForm):
    class Meta:
        model = GreaseBatch
        fields = ['grease_type', 'batch_number', 'manufacturing_date', 'expiration_date', 'initial_quantity', 'storage_location']
        widgets = {
            'manufacturing_date': forms.DateInput(attrs={'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ConsumeGreaseForm(forms.Form):
    grease_type = forms.ModelChoiceField(queryset=GreaseType.objects.all(), label="Tipo de Grasa")
    quantity = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01, label="Cantidad a Consumir")
    reference = forms.CharField(max_length=255, required=False, label="Referencia (e.g., Plan de Vuelo, Nro Orden)")
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False, label="Motivo o Notas")

