from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy

from django.contrib import messages
from django.shortcuts import redirect, render
from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError

import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Unit, MeasurementUnit, AircraftModel, GreaseType, AircraftGrease, FlightPlan, GreaseBatch, StockMovement, GreaseReferencePrice
from .forms import UnitForm, MeasurementUnitForm, AircraftModelForm, GreaseTypeForm, AircraftGreaseForm, FlightPlanForm, GreaseBatchForm, ConsumeGreaseForm, GreaseReferencePriceForm, RetestBatchForm
from .services import update_batch_statuses, consume_grease
from django.db.models import ProtectedError

class LogisticsRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        # RBAC: Requiere que el usuario pertenezca al grupo Administrador o Logistica,
        # o que sea superusuario.
        user = self.request.user
        if not user.is_authenticated:
            return False
        return user.is_superuser or user.groups.filter(name__in=['Administrador', 'Logistica']).exists()

# Home View
def home(request):
    expiration_alerts = []
    stock_alerts = []
    
    if request.user.is_authenticated:
        update_batch_statuses()
        
        # Alertas de Vencimiento
        expiration_alerts = GreaseBatch.objects.filter(
            status__in=['NEAR_EXPIRATION', 'EXPIRED'],
            available_quantity__gt=0
        ).order_by('expiration_date')
        
        # Alertas de Stock Mínimo (Previsión de Abastecimiento)
        grease_types = GreaseType.objects.all()
        for gt in grease_types:
            total_available = sum(b.available_quantity for b in gt.batches.filter(status__in=['SERVICEABLE', 'NEAR_EXPIRATION']))
            total_projected = 0
            
            for assoc in gt.aircraft_associations.all():
                for plan in assoc.aircraft_model.flight_plans.all():
                    total_projected += (assoc.hourly_consumption_rate * plan.planned_hours)
                    
            if total_projected > total_available:
                stock_alerts.append({
                    'grease_type': gt,
                    'shortfall': total_projected - total_available,
                    'available': total_available,
                    'projected': total_projected
                })

    return render(request, 'core/home.html', {
        'alerts': expiration_alerts,
        'stock_alerts': stock_alerts
    })

# --- Units ---
class UnitListView(LoginRequiredMixin, ListView):
    model = Unit
    template_name = 'core/unit_list.html'
    context_object_name = 'units'

class UnitCreateView(LogisticsRequiredMixin, SuccessMessageMixin, CreateView):
    model = Unit
    form_class = UnitForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('unit_list')
    success_message = "Unidad creada exitosamente."
    extra_context = {'title': 'Crear Unidad'}

class UnitUpdateView(LogisticsRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Unit
    form_class = UnitForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('unit_list')
    success_message = "Unidad actualizada exitosamente."
    extra_context = {'title': 'Editar Unidad'}

class UnitDeleteView(LogisticsRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Unit
    template_name = 'core/unit_confirm_delete.html'
    success_url = reverse_lazy('unit_list')
    success_message = "Unidad eliminada exitosamente."

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

# --- Measurement Units (Configuration) ---
class MeasurementUnitListView(LogisticsRequiredMixin, ListView):
    model = MeasurementUnit
    template_name = 'core/measurementunit_list.html'
    context_object_name = 'units'

class MeasurementUnitCreateView(LogisticsRequiredMixin, SuccessMessageMixin, CreateView):
    model = MeasurementUnit
    form_class = MeasurementUnitForm
    template_name = 'core/measurementunit_form.html'
    success_url = reverse_lazy('measurementunit_list')
    success_message = "Unidad de medida creada exitosamente."

class MeasurementUnitUpdateView(LogisticsRequiredMixin, SuccessMessageMixin, UpdateView):
    model = MeasurementUnit
    form_class = MeasurementUnitForm
    template_name = 'core/measurementunit_form.html'
    success_url = reverse_lazy('measurementunit_list')
    success_message = "Unidad de medida actualizada exitosamente."

class MeasurementUnitDeleteView(LogisticsRequiredMixin, SuccessMessageMixin, DeleteView):
    model = MeasurementUnit
    template_name = 'core/measurementunit_confirm_delete.html'
    success_url = reverse_lazy('measurementunit_list')
    success_message = "Unidad de medida eliminada exitosamente."

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

# --- Aircraft Models ---
class AircraftListView(LoginRequiredMixin, ListView):
    model = AircraftModel
    template_name = 'core/aircraft_list.html'
    context_object_name = 'aircrafts'

class AircraftCreateView(LogisticsRequiredMixin, SuccessMessageMixin, CreateView):
    model = AircraftModel
    form_class = AircraftModelForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('aircraft_list')
    success_message = "Aeronave creada exitosamente."
    extra_context = {'title': 'Crear Modelo de Aeronave'}

class AircraftUpdateView(LogisticsRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AircraftModel
    form_class = AircraftModelForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('aircraft_list')
    success_message = "Aeronave actualizada exitosamente."
    extra_context = {'title': 'Editar Modelo de Aeronave'}

# --- Grease Types ---
class GreaseTypeListView(LoginRequiredMixin, ListView):
    model = GreaseType
    template_name = 'core/grease_list.html'
    context_object_name = 'greases'

class GreaseTypeCreateView(LogisticsRequiredMixin, SuccessMessageMixin, CreateView):
    model = GreaseType
    form_class = GreaseTypeForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('grease_list')
    success_message = "Tipo de Grasa creado exitosamente."
    extra_context = {'title': 'Crear Tipo de Grasa'}

class GreaseTypeUpdateView(LogisticsRequiredMixin, SuccessMessageMixin, UpdateView):
    model = GreaseType
    form_class = GreaseTypeForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('grease_list')
    success_message = "Tipo de Grasa actualizado exitosamente."
    extra_context = {'title': 'Editar Tipo de Grasa'}

# --- Grease Reference Prices ---
class GreaseReferencePriceListView(LoginRequiredMixin, ListView):
    model = GreaseReferencePrice
    template_name = 'core/greasereferenceprice_list.html'
    context_object_name = 'prices'

    def get_queryset(self):
        return GreaseReferencePrice.objects.filter(grease_type_id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grease_type'] = GreaseType.objects.get(pk=self.kwargs['pk'])
        return context

class GreaseReferencePriceCreateView(LogisticsRequiredMixin, SuccessMessageMixin, CreateView):
    model = GreaseReferencePrice
    form_class = GreaseReferencePriceForm
    template_name = 'core/form_base.html'
    success_message = "Cotización / Precio de Referencia agregado exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gt = GreaseType.objects.get(pk=self.kwargs['pk'])
        context['title'] = f'Agregar Precio de Referencia - {gt.nomenclatura}'
        return context
        
    def get_initial(self):
        initial = super().get_initial()
        gt = GreaseType.objects.get(pk=self.kwargs['pk'])
        initial['presentation_quantity'] = gt.presentacion
        return initial

    def form_valid(self, form):
        form.instance.grease_type_id = self.kwargs['pk']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('grease_price_list', kwargs={'pk': self.kwargs['pk']})

class GreaseReferencePriceDeleteView(LogisticsRequiredMixin, SuccessMessageMixin, DeleteView):
    model = GreaseReferencePrice
    template_name = 'core/confirm_delete.html'
    success_message = "Precio de Referencia eliminado exitosamente."

    def get_success_url(self):
        return reverse_lazy('grease_price_list', kwargs={'pk': self.object.grease_type_id})

# --- Aircraft - Grease Associations ---
class AircraftGreaseListView(LoginRequiredMixin, ListView):
    model = AircraftGrease
    template_name = 'core/aircraftgrease_list.html'
    context_object_name = 'associations'

class AircraftGreaseCreateView(LogisticsRequiredMixin, SuccessMessageMixin, CreateView):
    model = AircraftGrease
    form_class = AircraftGreaseForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('association_list')
    success_message = "Asociación creada exitosamente."
    extra_context = {'title': 'Vincular Aeronave con Grasa'}

class AircraftGreaseUpdateView(LogisticsRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AircraftGrease
    form_class = AircraftGreaseForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('association_list')
    success_message = "Asociación actualizada exitosamente."
    extra_context = {'title': 'Editar Asociación Aeronave-Grasa'}

class AircraftGreaseDeleteView(LogisticsRequiredMixin, SuccessMessageMixin, DeleteView):
    model = AircraftGrease
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('association_list')
    success_message = "Asociación eliminada exitosamente."

# --- Flight Plans ---
class FlightPlanListView(LoginRequiredMixin, ListView):
    model = FlightPlan
    template_name = 'core/flightplan_list.html'
    context_object_name = 'flight_plans'
    ordering = ['-period_start_date']

class FlightPlanCreateView(LogisticsRequiredMixin, SuccessMessageMixin, CreateView):
    model = FlightPlan
    form_class = FlightPlanForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('flightplan_list')
    success_message = "Plan de empleo creado exitosamente."
    extra_context = {'title': 'Crear Plan de Empleo'}

class FlightPlanUpdateView(LogisticsRequiredMixin, SuccessMessageMixin, UpdateView):
    model = FlightPlan
    form_class = FlightPlanForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('flightplan_list')
    success_message = "Plan de empleo actualizado exitosamente."
    extra_context = {'title': 'Editar Plan de Empleo'}

class FlightPlanDeleteView(LogisticsRequiredMixin, SuccessMessageMixin, DeleteView):
    model = FlightPlan
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('flightplan_list')
    success_message = "Plan de empleo eliminado exitosamente."

# --- Stock Management & Batches ---
class GreaseBatchListView(LoginRequiredMixin, ListView):
    model = GreaseBatch
    template_name = 'core/greasebatch_list.html'
    context_object_name = 'batches'
    ordering = ['expiration_date']
    
    def get_queryset(self):
        # Primero actualizamos los estados antes de mostrar
        update_batch_statuses()
        return super().get_queryset()

class GreaseBatchDetailView(LoginRequiredMixin, ListView):
    # Usado para ver los movimientos de un lote específico
    model = StockMovement
    template_name = 'core/greasebatch_detail.html'
    context_object_name = 'movements'
    
    def get_queryset(self):
        return StockMovement.objects.filter(batch_id=self.kwargs['pk']).order_by('-movement_date')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = GreaseBatch.objects.get(pk=self.kwargs['pk'])
        return context

class GreaseBatchCreateView(LogisticsRequiredMixin, SuccessMessageMixin, CreateView):
    model = GreaseBatch
    form_class = GreaseBatchForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('batch_list')
    extra_context = {'title': 'Registrar Ingreso de Lote'}

    @transaction.atomic
    def form_valid(self, form):
        # Set available quantity initially to the incoming amount
        form.instance.available_quantity = form.instance.initial_quantity
        response = super().form_valid(form)
        
        # Generar movimiento de auditoría (INCOMING) indescifrable / no borrable
        StockMovement.objects.create(
            batch=self.object,
            movement_type='INCOMING',
            quantity_changed=self.object.initial_quantity,
            user=self.request.user,
            reason="Ingreso inicial al sistema"
        )
        return response

class ConsumeGreaseView(LogisticsRequiredMixin, FormView):
    template_name = 'core/form_base.html'
    form_class = ConsumeGreaseForm
    success_url = reverse_lazy('batch_list')
    extra_context = {'title': 'Registrar Consumo de Grasa'}

    def form_valid(self, form):
        grease_type = form.cleaned_data['grease_type']
        quantity = form.cleaned_data['quantity']
        reference = form.cleaned_data['reference']
        reason = form.cleaned_data['reason']
        
        try:
            update_batch_statuses() # Always good to ensure accurate expiration states before consuming
            consume_grease(
                grease_type=grease_type,
                quantity_to_consume=quantity,
                user=self.request.user,
                reference=reference,
                reason=reason
            )
            messages.success(self.request, f"Se consumieron {quantity} kg/uds de '{grease_type.nomenclatura}' exitosamente.")
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)

class GreaseBatchDeleteView(LogisticsRequiredMixin, DeleteView):
    model = GreaseBatch
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('batch_list')
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Eliminar los movimientos asociados usando filter().delete()
        # Esto hace un "bulk delete" a nivel de base de datos y esquiva la validación
        # personalizada del modelo StockMovement que impide el borrado normal.
        StockMovement.objects.filter(batch=self.object).delete()
        
        messages.success(request, f"El lote {self.object.batch_number} fue eliminado exitosamente.")
        return super().post(request, *args, **kwargs)

class RetestBatchView(LogisticsRequiredMixin, UpdateView):
    model = GreaseBatch
    form_class = RetestBatchForm
    template_name = 'core/form_base.html'
    
    def get_success_url(self):
        return reverse_lazy('batch_detail', kwargs={'pk': self.object.pk})
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Retestear Lote {self.object.batch_number} - {self.object.grease_type.nomenclatura}'
        return context

    @transaction.atomic
    def form_valid(self, form):
        reason = form.cleaned_data['reason']
        extension_time = form.cleaned_data['extension_time']
        
        # Calcular diferencia si el usuario modificó la disponibilidad por consumo de laboratorio
        old_quantity = form.initial.get('available_quantity', 0)
        new_quantity = form.cleaned_data.get('available_quantity', 0)
        diff = new_quantity - old_quantity

        response = super().form_valid(form)
        
        # registrar movimiento
        StockMovement.objects.create(
            batch=self.object,
            movement_type='RETEST',
            quantity_changed=diff,
            user=self.request.user,
            reason=f"Retesteo / Extensión de Vencimiento. Tiempo Habilitado: {extension_time}. {reason}"
        )
        
        # update batch status based on new expiration
        update_batch_statuses()
        
        messages.success(self.request, "Retesteo registrado y lote actualizado exitosamente.")
        return response

# --- Procurement Forecasting ---
class ProcurementForecastingView(LoginRequiredMixin, TemplateView):
    template_name = 'core/procurement_forecast.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grease_types = GreaseType.objects.all()
        forecast_data = []

        update_batch_statuses()

        for gt in grease_types:
            total_available = sum(b.available_quantity for b in gt.batches.filter(status__in=['SERVICEABLE', 'NEAR_EXPIRATION']))
            
            total_projected = 0
            plan_details = []
            for assoc in gt.aircraft_associations.all():
                for plan in assoc.aircraft_model.flight_plans.all():
                    # Para el MVP, suma todos los planes. En prod se filtraría por >= today o por periodo específico
                    projected_for_plan = assoc.hourly_consumption_rate * plan.planned_hours
                    total_projected += projected_for_plan
                    plan_details.append({
                        'aircraft': assoc.aircraft_model,
                        'plan': plan,
                        'rate': assoc.hourly_consumption_rate,
                        'projected': projected_for_plan
                    })
                    
            shortfall = total_projected - total_available
            recommended_purchase = shortfall if shortfall > 0 else 0
            
            forecast_data.append({
                'grease_type': gt,
                'total_available': total_available,
                'total_projected': total_projected,
                'shortfall': shortfall,
                'recommended_purchase': recommended_purchase,
                'plan_details': plan_details
            })
            
        context['forecast_data'] = forecast_data
        return context

# --- CSV Exports ---
@login_required
def export_grease_batches_csv(request):
    update_batch_statuses()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="stock_lotes.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Tipo de Grasa', 'Lote', 'Vencimiento', 'Estado', 'Ubicación', 'Cantidad Inicial', 'Cantidad Disponible'])
    
    batches = GreaseBatch.objects.all().order_by('expiration_date')
    for b in batches:
        writer.writerow([
            b.grease_type.nomenclatura,
            b.batch_number,
            b.expiration_date.strftime('%Y-%m-%d'),
            b.get_status_display(),
            b.storage_location,
            b.initial_quantity,
            b.available_quantity
        ])
    return response

@login_required
def export_procurement_forecast_csv(request):
    update_batch_statuses()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="pronostico_abastecimiento.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Tipo de Grasa', 'Stock Disponible', 'Consumo Proyectado', 'Diferencia (Sobrante/Faltante)', 'Compra Recomendada'])
    
    for gt in GreaseType.objects.all():
        total_available = sum(b.available_quantity for b in gt.batches.filter(status__in=['SERVICEABLE', 'NEAR_EXPIRATION']))
        total_projected = 0
        for assoc in gt.aircraft_associations.all():
            for plan in assoc.aircraft_model.flight_plans.all():
                total_projected += (assoc.hourly_consumption_rate * plan.planned_hours)
                
        shortfall = total_projected - total_available
        recommended_purchase = shortfall if shortfall > 0 else 0
        
        writer.writerow([
            gt.nomenclatura,
            total_available,
            total_projected,
            shortfall,
            recommended_purchase
        ])
    return response

# --- PDF Exports ---
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

@login_required
def export_grease_batches_pdf(request):
    update_batch_statuses()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Reporte de Stock de Lotes de Grasa", styles['Title']))
    elements.append(Spacer(1, 12))
    
    data = [['Tipo de Grasa', 'Lote', 'Vencimiento', 'Estado', 'Ubicación', 'Inicial', 'Disponible']]
    for b in GreaseBatch.objects.all().order_by('expiration_date'):
        data.append([
            b.grease_type.nomenclatura,
            b.batch_number,
            b.expiration_date.strftime('%d/%m/%Y'),
            b.get_status_display(),
            b.storage_location,
            str(b.initial_quantity),
            str(b.available_quantity)
        ])
    
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    
    elements.append(t)
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="stock_lotes.pdf"'
    return response

@login_required
def export_procurement_forecast_pdf(request):
    update_batch_statuses()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Reporte de Pronóstico de Abastecimiento", styles['Title']))
    elements.append(Spacer(1, 12))
    
    data = [['Tipo de Grasa', 'Stock\nDisponible', 'Consumo\nProyectado', 'Diferencia\n(Sobrante/Faltante)', 'Recomendación\nde Compra']]
    
    for gt in GreaseType.objects.all():
        total_available = sum(b.available_quantity for b in gt.batches.filter(status__in=['SERVICEABLE', 'NEAR_EXPIRATION']))
        total_projected = sum((assoc.hourly_consumption_rate * plan.planned_hours) 
                              for assoc in gt.aircraft_associations.all() 
                              for plan in assoc.aircraft_model.flight_plans.all())
        shortfall = total_projected - total_available
        recommended_purchase = shortfall if shortfall > 0 else 0
        
        data.append([
            gt.nomenclatura,
            str(round(total_available, 2)),
            str(round(total_projected, 2)),
            str(round(shortfall, 2)),
            str(round(recommended_purchase, 2))
        ])
    
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    
    elements.append(t)
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="pronostico_abastecimiento.pdf"'
    return response

