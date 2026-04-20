from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Ejercicios
    path('fiscal-years/', views.fiscal_year_list, name='fiscal_year_list'),
    path('fiscal-years/create/', views.fiscal_year_create, name='fiscal_year_create'),
    path('fiscal-years/<int:pk>/edit/', views.fiscal_year_update, name='fiscal_year_update'),
    path('fiscal-years/<int:pk>/close/', views.fiscal_year_close, name='fiscal_year_close'),
    
    # Créditos (AA.PP.)
    path('credits/', views.credit_list, name='credit_list'),
    path('credits/create/', views.credit_create, name='credit_create'),
    path('credits/<int:pk>/detail/', views.credit_detail, name='credit_detail'),
    path('credits/<int:pk>/delete/', views.credit_delete, name='credit_delete'),
    
    # Distribución (UU.CC.)
    path('allocations/', views.allocation_list, name='allocation_list'),
    path('allocations/create/', views.allocation_create, name='allocation_create'),
    path('allocations/<int:pk>/delete/', views.allocation_delete, name='allocation_delete'),
    
    # Ejecución (Flujo Secuencial)
    path('executions/', views.execution_list, name='execution_list'),
    path('executions/commitment/', views.execution_step_commitment, name='execution_commitment'),
    path('executions/<int:pk>/accrual/', views.execution_step_accrual, name='execution_accrual'),
    path('executions/<int:pk>/payment/', views.execution_step_payment, name='execution_payment'),
    path('executions/<int:pk>/detail/', views.execution_detail, name='execution_detail'),
    path('executions/<int:pk>/release-surplus/', views.execution_release_surplus, name='execution_release_surplus'),
    path('executions/<int:pk>/delete/', views.execution_delete, name='execution_delete'),
    
    # Configuración / Nomencladores
    path('config/', views.nomenclature_dashboard, name='nomenclature_dashboard'),
    path('config/<str:catalog_type>/', views.nomenclature_list, name='nomenclature_list'),
    path('config/<str:catalog_type>/add/', views.nomenclature_create, name='nomenclature_create'),
    path('config/<str:catalog_type>/<int:pk>/edit/', views.nomenclature_update, name='nomenclature_update'),
    path('config/<str:catalog_type>/<int:pk>/delete/', views.nomenclature_delete, name='nomenclature_delete'),
]
