# authentication/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
import uuid
from django.contrib import admin


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    organization = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Organización'
    )
    phone = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name='Teléfono'
    )
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True, 
        null=True,
        verbose_name='Avatar'
    )
    bio = models.TextField(
        max_length=500, 
        blank=True,
        verbose_name='Biografía'
    )
    location = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Ubicación'
    )
    date_joined_extended = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de registro extendida'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Usuario verificado'
    )
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
        
    def __str__(self):
        return f"Perfil de {self.user.get_full_name() or self.user.username}"
    
    def get_display_name(self):
        """Retorna el nombre completo o username si no hay nombre"""
        return self.user.get_full_name() or self.user.username


class CompostUnit(models.Model):
    """Modelo para unidades de compostaje"""
    
    UNIT_TYPES = [
        ('domestic', 'Doméstico'),
        ('community', 'Comunitario'),
        ('commercial', 'Comercial'),
        ('industrial', 'Industrial'),
        ('educational', 'Educativo'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('maintenance', 'Mantenimiento'),
        ('full', 'Lleno'),
    ]
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='compost_units',
        verbose_name='Propietario'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    location = models.CharField(
        max_length=200,
        verbose_name='Ubicación'
    )
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        blank=True, 
        null=True,
        verbose_name='Latitud'
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        blank=True, 
        null=True,
        verbose_name='Longitud'
    )
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Capacidad (kg)'
    )
    current_load = models.PositiveIntegerField(
        default=0,
        verbose_name='Carga actual (kg)'
    )
    unit_type = models.CharField(
        max_length=20, 
        choices=UNIT_TYPES,
        verbose_name='Tipo de unidad'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active',
        verbose_name='Estado'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Visible públicamente'
    )
    temperature = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name='Temperatura (°C)'
    )
    ph_level = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(14)],
        verbose_name='Nivel de pH'
    )
    moisture_level = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Nivel de humedad (%)'
    )
    
    def get_latest_reading(self):
        """Devuelve la última lectura de sensores asociada a esta unidad de compostaje."""
        return self.readings.order_by('-timestamp').first()

    class Meta:
        verbose_name = 'Unidad de Compostaje'
        verbose_name_plural = 'Unidades de Compostaje'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} - {self.owner.username}"
    
    def get_absolute_url(self):
        return reverse('compost_unit_detail', kwargs={'pk': self.pk})
    
    def is_full(self):
        """Determina si la unidad está llena"""
        return self.get_capacity_percentage() >= 95
    
    def can_add_material(self, amount):
        """Verifica si se puede agregar cierta cantidad de material"""
        return (self.current_load + amount) <= self.capacity

    def get_capacity_percentage(self):
        """Calcula el porcentaje de capacidad utilizada"""
        try:
            if self.capacity and self.capacity > 0:
                return float((self.current_load / self.capacity) * 100)
            return 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0


class CompostMaterial(models.Model):
    """Materiales de compostaje"""
    
    MATERIAL_TYPES = [
        ('green', 'Material Verde'),  # Nitrógeno
        ('brown', 'Material Marrón'), # Carbono
        ('other', 'Otro'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre del material'
    )
    material_type = models.CharField(
        max_length=10, 
        choices=MATERIAL_TYPES,
        verbose_name='Tipo de material'
    )
    carbon_nitrogen_ratio = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Relación C/N'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    is_recommended = models.BooleanField(
        default=True,
        verbose_name='Material recomendado'
    )
    
    class Meta:
        verbose_name = 'Material de Compostaje'
        verbose_name_plural = 'Materiales de Compostaje'
        ordering = ['name']
        
    def __str__(self):
        return self.name


class CompostEntry(models.Model):
    """Entradas de material en las unidades de compostaje"""
    
    compost_unit = models.ForeignKey(
        CompostUnit, 
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name='Unidad de compostaje'
    )
    material = models.ForeignKey(
        CompostMaterial, 
        on_delete=models.CASCADE,
        verbose_name='Material'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    quantity = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Cantidad (kg)'
    )
    date_added = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de agregado'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    
    class Meta:
        verbose_name = 'Entrada de Material'
        verbose_name_plural = 'Entradas de Material'
        ordering = ['-date_added']
        
    def __str__(self):
        return f"{self.quantity}kg de {self.material.name} - {self.date_added.date()}"


class CompostHarvest(models.Model):
    """Cosechas de compost terminado"""
    
    QUALITY_GRADES = [
        ('A', 'Excelente'),
        ('B', 'Buena'),
        ('C', 'Regular'),
        ('D', 'Necesita mejoras'),
    ]
    
    compost_unit = models.ForeignKey(
        CompostUnit, 
        on_delete=models.CASCADE,
        related_name='harvests',
        verbose_name='Unidad de compostaje'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    quantity = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Cantidad cosechada (kg)'
    )
    quality_grade = models.CharField(
        max_length=1, 
        choices=QUALITY_GRADES,
        verbose_name='Calificación de calidad'
    )
    harvest_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de cosecha'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas sobre la cosecha'
    )
    compost_age_days = models.PositiveIntegerField(
        verbose_name='Edad del compost (días)'
    )
    
    class Meta:
        verbose_name = 'Cosecha de Compost'
        verbose_name_plural = 'Cosechas de Compost'
        ordering = ['-harvest_date']
        
    def __str__(self):
        return f"Cosecha {self.quantity}kg - {self.harvest_date.date()}"




class MonitoringLog(models.Model):
    compost_unit = models.ForeignKey(CompostUnit, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ph_level = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    moisture_level = models.PositiveIntegerField(null=True, blank=True)
    pest_presence = models.BooleanField(default=False)
    turning_performed = models.BooleanField(default=False)
    odor_intensity = models.IntegerField(null=True, blank=True)
    date_recorded = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Monitoreo {self.compost_unit.name} - {self.date_recorded.strftime('%Y-%m-%d %H:%M')}"


class SensorReading(models.Model):
    compost_unit = models.ForeignKey(
        CompostUnit,
        on_delete=models.CASCADE,
        related_name='readings',
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ph = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    humidity = models.PositiveIntegerField(null=True, blank=True, validators=[
        MinValueValidator(0), MaxValueValidator(100)
    ])
    oxygen = models.PositiveIntegerField(null=True, blank=True, validators=[
        MinValueValidator(0), MaxValueValidator(100)
    ])

    class Meta:
        verbose_name = 'Lectura de Sensor'
        verbose_name_plural = 'Lecturas de Sensor'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.compost_unit.name if self.compost_unit else 'Unidad desconocida'} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    def get_compost_phase(self):
        # lógica para determinar la fase del compost según los datos
        if self.temperature > 50:
            return "Fase Termófila"
        elif self.temperature > 30:
            return "Fase Mesófila"
        else:
            return "Fase de Enfriamiento"
