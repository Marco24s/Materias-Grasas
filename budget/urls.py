from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Ejercicios
    path('fiscal-years/', views.fiscal_year_list, name='fiscal_year_list'),
    path('fiscal-years/create/', views.fiscal_year_create, name='fiscal_year_create'),
    path('fiscal-years/<int:pk>/close/', views.fiscal_year_close, name='fiscal_year_close'),
    
    # Créditos (AA.PP.)
    path('credits/', views.credit_list, name='credit_list'),
    path('credits/create/', views.credit_create, name='credit_create'),
    
    # Distribución (UU.CC.)
    path('allocations/', views.allocation_list, name='allocation_list'),
    path('allocations/create/', views.allocation_create, name='allocation_create'),
    
    # Ejecución (Flujo Secuencial)
    path('executions/', views.execution_list, name='execution_list'),
    path('executions/commitment/', views.execution_step_commitment, name='execution_commitment'),
    path('executions/<int:pk>/accrual/', views.execution_step_accrual, name='execution_accrual'),
    path('executions/<int:pk>/payment/', views.execution_step_payment, name='execution_payment'),
    path('executions/<int:pk>/detail/', views.execution_detail, name='execution_detail'),
]
