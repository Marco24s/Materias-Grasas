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
from .models import Unit, AircraftModel, GreaseType, AircraftGrease, FlightPlan, GreaseBatch, StockMovement
from .forms import UnitForm, AircraftModelForm, GreaseTypeForm, AircraftGreaseForm, FlightPlanForm, GreaseBatchForm, ConsumeGreaseForm
from .services import update_batch_statuses, consume_grease_fifo

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
    alerts = []
    if request.user.is_authenticated:
        update_batch_statuses()
        alerts = GreaseBatch.objects.filter(
            status__in=['NEAR_EXPIRATION', 'EXPIRED'],
            available_quantity__gt=0
        ).order_by('expiration_date')
    return render(request, 'core/home.html', {'alerts': alerts})

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
    success_message = "Plan de vuelo creado exitosamente."
    extra_context = {'title': 'Crear Plan de Vuelo'}

class FlightPlanUpdateView(LogisticsRequiredMixin, SuccessMessageMixin, UpdateView):
    model = FlightPlan
    form_class = FlightPlanForm
    template_name = 'core/form_base.html'
    success_url = reverse_lazy('flightplan_list')
    success_message = "Plan de vuelo actualizado exitosamente."
    extra_context = {'title': 'Editar Plan de Vuelo'}

class FlightPlanDeleteView(LogisticsRequiredMixin, SuccessMessageMixin, DeleteView):
    model = FlightPlan
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('flightplan_list')
    success_message = "Plan de vuelo eliminado exitosamente."

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
    extra_context = {'title': 'Registrar Consumo de Grasa (FIFO)'}

    def form_valid(self, form):
        grease_type = form.cleaned_data['grease_type']
        quantity = form.cleaned_data['quantity']
        reference = form.cleaned_data['reference']
        reason = form.cleaned_data['reason']
        
        try:
            update_batch_statuses() # Always good to ensure accurate expiration states before consuming
            consume_grease_fifo(
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
            for assoc in gt.aircraft_associations.all():
                for plan in assoc.aircraft_model.flight_plans.all():
                    # Para el MVP, suma todos los planes. En prod se filtraría por >= today o por periodo específico
                    total_projected += (assoc.hourly_consumption_rate * plan.planned_hours)
                    
            shortfall = total_projected - total_available
            recommended_purchase = shortfall if shortfall > 0 else 0
            
            forecast_data.append({
                'grease_type': gt,
                'total_available': total_available,
                'total_projected': total_projected,
                'shortfall': shortfall,
                'recommended_purchase': recommended_purchase
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

