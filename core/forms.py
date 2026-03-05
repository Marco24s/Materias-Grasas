from django import forms
from .models import Unit, MeasurementUnit, AircraftModel, GreaseType, AircraftGrease, FlightPlan, GreaseBatch, GreaseReferencePrice

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'description']

class MeasurementUnitForm(forms.ModelForm):
    class Meta:
        model = MeasurementUnit
        fields = ['name']

class AircraftModelForm(forms.ModelForm):
    class Meta:
        model = AircraftModel
        fields = ['name', 'unit', 'total_aircraft', 'is_active']

class GreaseTypeForm(forms.ModelForm):
    class Meta:
        model = GreaseType
        fields = ['nomenclatura', 'unidad', 'presentacion', 'nne_nsn', 'sibys', 'nato', 'normas_mil_otras', 'shelf_life_months', 'recertification_allowed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate the unidad field with a dropdown from MeasurementUnit
        unit_choices = [(u.name, u.name) for u in MeasurementUnit.objects.all()]
        
        # If there's an instance (editing), ensure its current value is in the choices
        if self.instance and self.instance.pk and self.instance.unidad:
            current_unit = self.instance.unidad
            if not any(current_unit == choice[0] for choice in unit_choices):
                unit_choices.insert(0, (current_unit, f"{current_unit} (Actual)"))
        
        unit_choices.insert(0, ('', 'Seleccione una Unidad...'))
        
        self.fields['unidad'] = forms.ChoiceField(
            choices=unit_choices,
            label="UNIDAD",
            required=True
        )

class AircraftGreaseForm(forms.ModelForm):
    class Meta:
        model = AircraftGrease
        fields = ['aircraft_model', 'grease_type', 'hourly_consumption_rate', 'notes']

class FlightPlanForm(forms.ModelForm):
    class Meta:
        model = FlightPlan
        fields = ['aircraft_model', 'period_type', 'period_start_date', 'period_end_date', 'planned_hours']
        widgets = {
            'period_start_date': forms.DateInput(attrs={'type': 'date'}),
            'period_end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        period_type = cleaned_data.get('period_type')
        start_date = cleaned_data.get('period_start_date')
        end_date = cleaned_data.get('period_end_date')
        
        if period_type == 'CUSTOM' and not end_date:
            self.add_error('period_end_date', 'Debe especificar la fecha de finalización para un período Libre.')
            
        if start_date and end_date and start_date > end_date:
            self.add_error('period_end_date', 'La fecha de finalización debe ser posterior a la de inicio.')
            
        return cleaned_data

class GreaseBatchForm(forms.ModelForm):
    total_price = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False,
        label="Costo Total Pagado ($)",
        help_text="Costo total abonado por la cantidad ingresada de este lote."
    )

    class Meta:
        model = GreaseBatch
        fields = ['grease_type', 'batch_number', 'manufacturing_date', 'expiration_date', 'initial_quantity', 'storage_location']
        widgets = {
            'manufacturing_date': forms.DateInput(attrs={'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate choices dynamically from Unit models
        unit_choices = [(unit.name, unit.name) for unit in Unit.objects.all()]
        
        # If there's an instance (editing), ensure its current value is in the choices
        if self.instance and self.instance.pk and self.instance.storage_location:
            current_loc = self.instance.storage_location
            if not any(current_loc == choice[0] for choice in unit_choices):
                unit_choices.insert(0, (current_loc, f"{current_loc} (Actual)"))
        
        # Add an empty choice at the top
        unit_choices.insert(0, ('', 'Seleccione una Unidad...'))
        
        self.fields['storage_location'] = forms.ChoiceField(
            choices=unit_choices,
            label="Ubicación (Almacén/Unidad)",
            required=True
        )

    def clean(self):
        cleaned_data = super().clean()
        initial_quantity = cleaned_data.get('initial_quantity')
        total_price = cleaned_data.get('total_price')

        if initial_quantity and total_price is not None:
            # We calculate unit_price which will be assigned to instance by the view or model save logic, 
            # actually better to just inject it to the form's instance directly here.
            self.instance.unit_price = total_price / initial_quantity
        return cleaned_data

class ConsumeGreaseForm(forms.Form):
    grease_type = forms.ModelChoiceField(queryset=GreaseType.objects.all(), label="Tipo de Grasa")
    quantity = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01, label="Cantidad a Consumir")
    reference = forms.CharField(max_length=255, required=False, label="Referencia (e.g., Plan de Empleo, Nro Orden)")
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False, label="Motivo o Notas")

class GreaseReferencePriceForm(forms.ModelForm):
    class Meta:
        model = GreaseReferencePrice
        fields = ['price', 'presentation_quantity', 'supplier']
        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'presentation_quantity': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'presentation_quantity' in self.fields:
            # We don't have direct access to grease_type unit here in ModelForm init easily without passing it,
            # but we can just use the help_text from the model.
            pass

class RetestBatchForm(forms.ModelForm):
    extension_years = forms.FloatField(
        required=True,
        min_value=0.1,
        label="Años Habilitados",
        help_text="Por cuántos años se extiende la habilitación (ej. '0.5' para medio año, '1.5', '2')."
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}), 
        required=True, 
        label="Resultado / Motivo del Retesteo", 
        help_text="Documento de referencia o justificación técnica del ensayo aplicado."
    )
    
    class Meta:
        model = GreaseBatch
        fields = ['extension_years', 'available_quantity', 'can_be_retested', 'reason']
        labels = {
            'can_be_retested': 'Puede volver a retestearse',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['available_quantity'].help_text = "Ajustar si la muestra para laboratorio consumió material."

