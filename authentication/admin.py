# authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    UserProfile, CompostUnit, CompostMaterial, 
    CompostEntry, CompostHarvest, MonitoringLog
)

class UserProfileInline(admin.StackedInline):
    """Inline para mostrar el perfil en el admin de usuarios"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'


class UserAdmin(BaseUserAdmin):
    """Admin personalizado para usuarios"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 
                   'get_organization', 'is_verified', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__is_verified')
    search_fields = ('username', 'first_name', 'last_name', 'email', 
                    'profile__organization')
    
    def get_organization(self, obj):
        return obj.profile.organization if hasattr(obj, 'profile') else '-'
    get_organization.short_description = 'Organización'
    
    def is_verified(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.is_verified
        return False
    is_verified.boolean = True
    is_verified.short_description = 'Verificado'


from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin para perfiles de usuario"""
    list_display = ('user',)  # Usa solo campo seguro
    list_filter = ()
    readonly_fields = ()
    date_hierarchy = None

    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
    )


from django.contrib import admin
from django.utils.html import format_html
from .models import CompostUnit

@admin.register(CompostUnit)
class CompostUnitAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'owner', 'unit_type', 'status', 'capacity', 
        'get_capacity_used', 'location', 'is_public', 'created_at'
    )
    readonly_fields = ('capacity_percentage_display',)

    def get_capacity_used(self, obj):
        # Llama al método del modelo que devuelve float
        percentage = obj.get_capacity_percentage()
        color = 'green' if percentage < 70 else 'orange' if percentage < 90 else 'red'
        return format_html(
        '<span style="color: {};">{:.1f}%</span>',
        color, percentage
    )
    get_capacity_used.short_description = 'Capacidad Usada'

    @admin.display(description='Porcentaje de capacidad')
    def capacity_percentage_display(self, obj):
        percentage = obj.get_capacity_percentage()
        return f"{percentage:.1f}%"

    @admin.display(description='Porcentaje de capacidad')
    def capacity_percentage_display(self, obj):
        percentage = obj.get_capacity_percentage()
        return f"{percentage:.1f}%"


@admin.register(CompostMaterial)
class CompostMaterialAdmin(admin.ModelAdmin):
    """Admin para materiales de compostaje"""
    list_display = ('name', 'material_type', 'carbon_nitrogen_ratio', 
                   'is_recommended', 'get_type_badge')
    list_filter = ('material_type', 'is_recommended')
    search_fields = ('name', 'description')
    ordering = ('material_type', 'name')
    
    def get_type_badge(self, obj):
        colors = {
            'green': '#28a745',
            'brown': '#8B4513',
            'other': '#6c757d'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.material_type, '#6c757d'),
            obj.get_material_type_display()
        )
    get_type_badge.short_description = 'Tipo'


class CompostEntryInline(admin.TabularInline):
    """Inline para mostrar entradas en el admin de unidades"""
    model = CompostEntry
    extra = 0
    readonly_fields = ('date_added',)


class MonitoringLogInline(admin.TabularInline):
    """Inline para mostrar logs de monitoreo"""
    model = MonitoringLog
    extra = 0
    readonly_fields = ('date_recorded',)


@admin.register(CompostEntry)
class CompostEntryAdmin(admin.ModelAdmin):
    """Admin para entradas de material"""
    list_display = ('compost_unit', 'material', 'quantity', 'user', 'date_added')
    list_filter = ('material__material_type', 'date_added', 'material__is_recommended')
    search_fields = ('compost_unit__name', 'material__name', 'user__username')
    date_hierarchy = 'date_added'
    readonly_fields = ('date_added',)
    
    fieldsets = (
        ('Entrada de Material', {
            'fields': ('compost_unit', 'material', 'quantity', 'user')
        }),
        ('Detalles', {
            'fields': ('date_added', 'notes')
        }),
    )


@admin.register(CompostHarvest)
class CompostHarvestAdmin(admin.ModelAdmin):
    """Admin para cosechas de compost"""
    list_display = ('compost_unit', 'quantity', 'quality_grade', 
                   'compost_age_days', 'user', 'harvest_date')
    list_filter = ('quality_grade', 'harvest_date')
    search_fields = ('compost_unit__name', 'user__username')
    date_hierarchy = 'harvest_date'
    readonly_fields = ('harvest_date',)
    
    fieldsets = (
        ('Cosecha', {
            'fields': ('compost_unit', 'user', 'quantity', 'quality_grade')
        }),
        ('Información del Compost', {
            'fields': ('compost_age_days', 'harvest_date')
        }),
        ('Observaciones', {
            'fields': ('notes',)
        }),
    )


@admin.register(MonitoringLog)
class MonitoringLogAdmin(admin.ModelAdmin):
    """Admin para registros de monitoreo"""
    list_display = ('compost_unit', 'temperature', 'ph_level', 'moisture_level', 
                   'get_status_indicators', 'user', 'date_recorded')
    list_filter = ('pest_presence', 'turning_performed', 'date_recorded')
    search_fields = ('compost_unit__name', 'user__username')
    date_hierarchy = 'date_recorded'
    readonly_fields = ('date_recorded',)
    
    fieldsets = (
        ('Unidad y Usuario', {
            'fields': ('compost_unit', 'user', 'date_recorded')
        }),
        ('Parámetros Físicos', {
            'fields': ('temperature', 'ph_level', 'moisture_level')
        }),
        ('Estado General', {
            'fields': ('odor_intensity', 'pest_presence', 'turning_performed')
        }),
        ('Observaciones', {
            'fields': ('notes',)
        }),
    )
    
    def get_status_indicators(self, obj):
        indicators = []
        
        # Indicador de pH
        if 6.5 <= obj.ph_level <= 8.0:
            ph_color = 'green'
        elif 6.0 <= obj.ph_level <= 9.0:
            ph_color = 'orange'
        else:
            ph_color = 'red'
        indicators.append(f'<span style="color: {ph_color};">pH: {obj.ph_level}</span>')
        
        # Indicador de humedad
        if 40 <= obj.moisture_level <= 60:
            moisture_color = 'green'
        elif 30 <= obj.moisture_level <= 70:
            moisture_color = 'orange'
        else:
            moisture_color = 'red'
        indicators.append(f'<span style="color: {moisture_color};">💧{obj.moisture_level}%</span>')
        
        # Indicadores de estado
        if obj.pest_presence:
            indicators.append('<span style="color: red;">🐛 Plagas</span>')
        if obj.turning_performed:
            indicators.append('<span style="color: green;">🔄 Volteado</span>')
            
        return format_html(' | '.join(indicators))
    get_status_indicators.short_description = 'Indicadores'


# Configurar el admin personalizado para User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Personalizar títulos del admin
admin.site.site_header = "Administración del Sistema de Compostaje"
admin.site.site_title = "Compostaje Admin"
admin.site.index_title = "Panel de Administración"


# Actions personalizadas
@admin.action(description='Marcar unidades como activas')
def make_active(modeladmin, request, queryset):
    queryset.update(status='active')

@admin.action(description='Marcar unidades como inactivas')
def make_inactive(modeladmin, request, queryset):
    queryset.update(status='inactive')

# Agregar acciones al admin de CompostUnit
CompostUnitAdmin.actions = [make_active, make_inactive]