# authentication/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
import json
import random
from .models import CompostMaterial
from .models import CompostUnit, SensorReading, UserProfile
from .forms import CustomUserCreationForm, CompostUnitForm
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CompostUnit, SensorReading
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def welcome_view(request):
    if request.session.get('welcome_shown'):
        return redirect('dashboard')

    request.session['welcome_shown'] = True
    return render(request, 'authentication/welcome.html')



@login_required
def export_readings_pdf(request, unit_id):
    unit = get_object_or_404(CompostUnit, id=unit_id, owner=request.user)
    readings = SensorReading.objects.filter(compost_unit=unit).order_by('timestamp')

    # Crear respuesta HTTP con tipo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{unit.name}_readings.pdf"'

    # Crear el objeto PDF
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(72, height - 72, f"Registros de sensores - Unidad: {unit.name}")

    # Encabezados de tabla
    p.setFont("Helvetica-Bold", 12)
    y = height - 100
    p.drawString(72, y, "Fecha y hora")
    p.drawString(180, y, "Temperatura (°C)")
    p.drawString(320, y, "Humedad (%)")
    p.drawString(420, y, "pH")
    p.drawString(470, y, "Oxígeno (%)")

    # Contenido
    p.setFont("Helvetica", 10)
    y -= 20
    line_height = 15
    max_lines_per_page = 40
    lines_written = 0

    for reading in readings:
        if y < 72:  # Nueva página si llegamos al final
            p.showPage()
            y = height - 72
            lines_written = 0
            # Repetir encabezados en nueva página
            p.setFont("Helvetica-Bold", 12)
            p.drawString(72, y, "Fecha y hora")
            p.drawString(180, y, "Temperatura (°C)")
            p.drawString(320, y, "Humedad (%)")
            p.drawString(420, y, "pH")
            p.drawString(470, y, "Oxígeno (%)")
            p.setFont("Helvetica", 10)
            y -= 20

        p.drawString(72, y, reading.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        p.drawString(180, y, str(reading.temperature if reading.temperature is not None else '-'))
        p.drawString(320, y, str(reading.humidity if reading.humidity is not None else '-'))
        p.drawString(420, y, str(reading.ph if reading.ph is not None else '-'))
        p.drawString(470, y, str(reading.oxygen if reading.oxygen is not None else '-'))

        y -= line_height
        lines_written += 1

    p.showPage()
    p.save()

    return response



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro exitoso. Ahora puedes iniciar sesión.")
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'authentication/register.html', {'form': form})


from django.contrib.auth import login

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Reinicia el estado de bienvenida
            request.session['welcome_shown'] = False

            messages.success(request, f'Bienvenido, {user.username}')
            return redirect('welcome')  # Redirige primero a la ventana de bienvenida
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})



def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Cuenta creada exitosamente para {username}!')

            # Crear el perfil solo si no existe
            organization = form.cleaned_data.get('organization')
            if organization:
                UserProfile.objects.get_or_create(user=user, defaults={'organization': organization})

            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            if user:
                login(request, user)
                return redirect('dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'authentication/register.html', {'form': form})


@login_required
def dashboard(request):
    user_units = CompostUnit.objects.filter(owner=request.user)
    active_units = user_units.filter(status='active').count()
    total_capacity = sum(unit.capacity for unit in user_units)

    recent_data = []
    for unit in user_units:
        latest_reading = unit.get_latest_reading()
        if latest_reading:
            recent_data.append({
                'unit': unit,
                'data': latest_reading,
                'phase': latest_reading.get_compost_phase()
            })

    context = {
        'user_units': user_units,
        'active_units': active_units,
        'total_capacity': total_capacity,
        'recent_data': recent_data,
    }
    return render(request, 'authentication/dashboard.html', context)


@login_required
def manage_units(request):
    units_list = CompostUnit.objects.filter(owner=request.user).order_by('-created_at')
    paginator = Paginator(units_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'authentication/manage_units.html', {
        'page_obj': page_obj,
        'total_units': units_list.count(),
    })


@login_required
def create_unit(request):
    if request.method == 'POST':
        form = CompostUnitForm(request.POST)
        if form.is_valid():
            unit = form.save(commit=False)
            unit.owner = request.user
            unit.save()
            messages.success(request, f'Unidad "{unit.name}" creada exitosamente!')
            return redirect('manage_units')
        messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CompostUnitForm()
    return render(request, 'authentication/create_unit.html', {'form': form})


@login_required
def unit_detail(request, unit_id):
    unit = get_object_or_404(CompostUnit, id=unit_id, owner=request.user)
    latest_reading = unit.get_latest_reading()
    
    recent_readings = SensorReading.objects.filter(
        compost_unit=unit,
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).order_by('timestamp')

    chart_data = prepare_chart_data(recent_readings)

    readings_list = SensorReading.objects.filter(compost_unit=unit).order_by('-timestamp')
    readings_page = Paginator(readings_list, 20).get_page(request.GET.get('page'))

    return render(request, 'authentication/unit_detail.html', {
        'unit': unit,
        'latest_reading': latest_reading,
        'recent_readings': recent_readings,
        'readings_page': readings_page,
        'chart_labels': json.dumps(chart_data['labels']),
        'temp_data': json.dumps(chart_data['temperature']),
        'humidity_data': json.dumps(chart_data['humidity']),
        'ph_data': json.dumps(chart_data['ph']),
        'oxygen_data': json.dumps(chart_data['oxygen']),
    })



@login_required
def delete_unit(request, unit_id):
    unit = get_object_or_404(CompostUnit, id=unit_id, owner=request.user)
    if request.method == 'POST':
        unit_name = unit.name
        unit.delete()
        messages.success(request, f'Unidad "{unit_name}" eliminada exitosamente.')
        return redirect('manage_units')
    return render(request, 'authentication/delete_unit_confirm.html', {'unit': unit})

def prepare_chart_data(readings):
    labels = []
    temperature = []
    ph = []
    humidity = []
    oxygen = []

    # Ordenar cronológicamente las lecturas
    readings = readings.order_by('timestamp')

    for r in readings:
        labels.append(r.timestamp.strftime('%d/%m %H:%M'))  # formato fecha/hora
        temperature.append(float(r.temperature) if r.temperature is not None else None)
        ph.append(float(r.ph) if r.ph is not None else None)
        humidity.append(r.humidity if r.humidity is not None else None)
        oxygen.append(r.oxygen if r.oxygen is not None else None)

    return {
        'labels': labels,
        'temperature': temperature,
        'ph': ph,
        'humidity': humidity,
        'oxygen': oxygen,
    }



@login_required
def statistics(request):
    user_units = CompostUnit.objects.filter(owner=request.user)
    total_readings = SensorReading.objects.filter(compost_unit__owner=request.user).count()

    unit_stats = []
    for unit in user_units:
        readings = SensorReading.objects.filter(compost_unit=unit)
        if readings.exists():
            stats = readings.aggregate(
                avg_temp=Avg('temperature'),
                avg_ph=Avg('ph'),
                avg_humidity=Avg('humidity'),
                avg_oxygen=Avg('oxygen'),
                count=Count('id')
            )
            stats.update({
                'unit': unit,
                'latest': readings.order_by('-timestamp').first()
            })
            unit_stats.append(stats)

    recent_readings = SensorReading.objects.filter(
        compost_unit__owner=request.user
    ).order_by('-timestamp')[:100]

    chart_data = prepare_chart_data(recent_readings)

    materiales = CompostMaterial.objects.filter(is_recommended=True)
    materiales_labels = [m.name for m in materiales]
    materiales_data = [float(m.carbon_nitrogen_ratio) for m in materiales]

    return render(request, 'authentication/statistics.html', {
    'total_readings': total_readings,
    'unit_stats': unit_stats,
    'temp_labels': chart_data['labels'],  # sin json.dumps
    'temp_data': chart_data['temperature'],
    'ph_labels': chart_data['labels'],
    'ph_data': chart_data['ph'],
    'humidity_labels': chart_data['labels'],
    'humidity_data': chart_data['humidity'],
    'oxygen_data': chart_data['oxygen'],
    'labels_materiales': materiales_labels,
    'data_materiales': materiales_data,
})




@login_required
def create_demo_data(request):
    if request.method == 'POST':
        demo_units = [
            {'name': 'Unidad Demo 1', 'location': 'Jardín Principal', 'capacity': 100.0,
             'description': 'Unidad de demostración para residuos orgánicos del hogar'},
            {'name': 'Unidad Demo 2', 'location': 'Área de Compostaje', 'capacity': 200.0,
             'description': 'Unidad industrial para grandes volúmenes de compost'}
        ]

        created = 0
        for data in demo_units:
            if not CompostUnit.objects.filter(owner=request.user, name=data['name']).exists():
                unit = CompostUnit.objects.create(owner=request.user, **data)
                create_demo_sensor_data(unit)
                created += 1

        if created:
            messages.success(request, f'Se crearon {created} unidades de demostración.')
        else:
            messages.info(request, 'Las unidades de demostración ya existen.')

    return redirect('dashboard')


def prepare_chart_data(readings):
    labels, temperature, humidity, ph, oxygen = [], [], [], [], []
    for reading in readings:
        labels.append(reading.timestamp.strftime('%d/%m %H:%M'))
        temperature.append(float(reading.temperature))
        humidity.append(float(reading.humidity))
        ph.append(float(reading.ph))
        oxygen.append(float(reading.oxygen))
    return {
        'labels': labels,
        'temperature': temperature,
        'humidity': humidity,
        'ph': ph,
        'oxygen': oxygen,
    }


def create_demo_sensor_data(unit):
    now = timezone.now()
    phases = [
        {'temp_range': (45, 65), 'humidity_range': (40, 60), 'ph_range': (6.0, 7.5), 'oxygen_range': (5, 15)},
        {'temp_range': (25, 45), 'humidity_range': (50, 70), 'ph_range': (6.5, 8.0), 'oxygen_range': (10, 20)},
        {'temp_range': (20, 35), 'humidity_range': (55, 75), 'ph_range': (7.0, 8.5), 'oxygen_range': (15, 25)},
        {'temp_range': (15, 25), 'humidity_range': (60, 80), 'ph_range': (7.5, 8.5), 'oxygen_range': (18, 30)},
    ]

    for day in range(7):
        phase = phases[min(day // 2, len(phases) - 1)]
        for _ in range(random.randint(4, 6)):
            timestamp = now - timedelta(days=6-day, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            if not SensorReading.objects.filter(
                unit=unit,
                timestamp__range=[timestamp - timedelta(minutes=30), timestamp + timedelta(minutes=30)]
            ).exists():
                SensorReading.objects.create(
                    unit=unit,
                    temperature=round(random.uniform(*phase['temp_range']), 1),
                    humidity=round(random.uniform(*phase['humidity_range']), 1),
                    ph=round(random.uniform(*phase['ph_range']), 1),
                    oxygen=round(random.uniform(*phase['oxygen_range']), 1),
                    timestamp=timestamp
                )
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now, timedelta
from .models import CompostUnit, MonitoringLog

def compost_temperature_chart(request, unit_id):
    # Obtener la unidad
    unit = get_object_or_404(CompostUnit, id=unit_id)

    # Fecha hace 7 días
    fecha_inicio = now() - timedelta(days=6)

    # Consultar logs ordenados por fecha para los últimos 7 días
    logs = MonitoringLog.objects.filter(
        compost_unit=unit,
        date_recorded__date__gte=fecha_inicio.date()
    ).order_by('date_recorded')

    # Preparar listas para etiquetas (fechas) y temperaturas
    etiquetas = []
    temperaturas = []

    # Puede que no haya datos todos los días, vamos a iterar sobre los días para garantizar etiquetas continuas
    for i in range(7):
        dia = fecha_inicio.date() + timedelta(days=i)
        etiquetas.append(dia.strftime('%d %b'))  # ej. 24 May

        # Buscar si hay un log para ese día (podemos tomar promedio o último registro)
        logs_del_dia = logs.filter(date_recorded__date=dia)
        if logs_del_dia.exists():
            # Tomamos la temperatura del último registro del día
            temp = logs_del_dia.last().temperature
            temperaturas.append(temp)
        else:
            temperaturas.append(None)  # o 0, o cualquier valor por defecto

    context = {
        'unit': unit,
        'meses': etiquetas,
        'temperaturas': temperaturas,
    }
    return render(request, 'compost/chart.html', context)

