from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('welcome/', views.welcome_view, name='welcome'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Gestión de unidades
    path('units/', views.manage_units, name='manage_units'),
    path('units/create/', views.create_unit, name='create_unit'),
    path('units/<uuid:unit_id>/', views.unit_detail, name='unit_detail'),
    path('units/<uuid:unit_id>/delete/', views.delete_unit, name='delete_unit'),
    
    # Estadísticas
    path('statistics/', views.statistics, name='statistics'),
    
    # Datos de demostración
    path('create-demo-data/', views.create_demo_data, name='create_demo_data'),
    path('auth/units/<uuid:unit_id>/export_pdf/', views.export_readings_pdf, name='export_readings_pdf'),
    
]
