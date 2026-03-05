from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # Units
    path('units/', views.UnitListView.as_view(), name='unit_list'),
    path('units/add/', views.UnitCreateView.as_view(), name='unit_create'),
    path('units/<int:pk>/edit/', views.UnitUpdateView.as_view(), name='unit_update'),
    
    # Aircraft Models
    path('aircrafts/', views.AircraftListView.as_view(), name='aircraft_list'),
    path('aircrafts/add/', views.AircraftCreateView.as_view(), name='aircraft_create'),
    path('aircrafts/<int:pk>/edit/', views.AircraftUpdateView.as_view(), name='aircraft_update'),
    
    # Grease Types
    path('greases/', views.GreaseTypeListView.as_view(), name='grease_list'),
    path('greases/add/', views.GreaseTypeCreateView.as_view(), name='grease_create'),
    path('greases/<int:pk>/edit/', views.GreaseTypeUpdateView.as_view(), name='grease_update'),
    
    # Aircraft - Grease Associations
    path('associations/', views.AircraftGreaseListView.as_view(), name='association_list'),
    path('associations/add/', views.AircraftGreaseCreateView.as_view(), name='association_create'),
    path('associations/<int:pk>/edit/', views.AircraftGreaseUpdateView.as_view(), name='association_update'),
    path('associations/<int:pk>/delete/', views.AircraftGreaseDeleteView.as_view(), name='association_delete'),
    
    # Flight Plans
    path('flightplans/', views.FlightPlanListView.as_view(), name='flightplan_list'),
    path('flightplans/add/', views.FlightPlanCreateView.as_view(), name='flightplan_create'),
    path('flightplans/<int:pk>/edit/', views.FlightPlanUpdateView.as_view(), name='flightplan_update'),
    path('flightplans/<int:pk>/delete/', views.FlightPlanDeleteView.as_view(), name='flightplan_delete'),
    
    # Stock Management & Batches
    path('stock/', views.GreaseBatchListView.as_view(), name='batch_list'),
    path('stock/add/', views.GreaseBatchCreateView.as_view(), name='batch_create'),
    path('stock/<int:pk>/movements/', views.GreaseBatchDetailView.as_view(), name='batch_detail'),
    path('stock/consume/', views.ConsumeGreaseView.as_view(), name='consume_grease'),
    
    # Procurement Forecasting
    path('procurement/', views.ProcurementForecastingView.as_view(), name='procurement_forecast'),
    path('procurement/export/', views.export_procurement_forecast_csv, name='export_procurement_forecast_csv'),
    path('procurement/export/pdf/', views.export_procurement_forecast_pdf, name='export_procurement_forecast_pdf'),
    
    # Exports
    path('stock/export/', views.export_grease_batches_csv, name='export_grease_batches_csv'),
    path('stock/export/pdf/', views.export_grease_batches_pdf, name='export_grease_batches_pdf'),
]
