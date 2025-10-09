import json
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Sum, F
from django.forms.models import model_to_dict
from .models import HistorialRendimiento, Reactor
from django.db.models import Avg
from datetime import timedelta

# ==============================================================================
# ## VISTAS PRINCIPALES DE PÁGINAS ##
# ==============================================================================

def vista_dashboard(request):
    """
    Renderiza la página principal del dashboard con estadísticas, gráficas y guías.
    """
    # --- Cálculos para las tarjetas de métricas (KPIs) ---
    total_reactores = Reactor.objects.count()
    paises_con_reactores = Reactor.objects.values('pais').distinct().count()
    potencia_total = Reactor.objects.aggregate(total_power=Sum('potencia_neta'))['total_power']

    # --- Datos para la lista completa y la gráfica de barras ---
    top_paises = Reactor.objects.values('pais').annotate(total=Count('id')).order_by('-total')[:5]
    todos_los_paises = Reactor.objects.values('pais').annotate(total=Count('id')).order_by('-total')
    
    top_paises_chart_data = {
        'labels': [p['pais'] for p in top_paises],
        'data': [p['total'] for p in top_paises],
    }
    
    # --- Datos estáticos para la gráfica de donut ---
    energy_mix_data = {
        'labels': ['Combustibles Fósiles', 'Hidroeléctrica', 'Nuclear', 'Eólica y Solar', 'Otras Renovables'],
        'data': [59, 15, 9, 13, 4],
    }

    context = {
        'total_reactores': total_reactores,
        'paises_con_reactores': paises_con_reactores,
        'potencia_total_gw': round(potencia_total / 1000) if potencia_total else 0,
        'todos_los_paises': todos_los_paises,
        'energy_mix_json': json.dumps(energy_mix_data),
        'top_paises_chart_json': json.dumps(top_paises_chart_data)
    }
    return render(request, 'reactores/dashboard.html', context)



def vista_atlas(request):
    """
    Renderiza la página del atlas interactivo.
    Pasa la lista de países para el menú desplegable.
    """
    paises = Reactor.objects.values('pais').distinct().order_by('pais')
    context = {
        'paises': paises
    }
    return render(request, 'reactores/atlas.html', context)


def vista_comparador(request):
    """
    Renderiza la página del comparador interactivo.
    Pasa la lista de tipos de reactores para el primer filtro.
    """
    tipos = Reactor.objects.exclude(tipo_reactor_categoria__isnull=True).values_list('tipo_reactor_categoria', flat=True).distinct().order_by('tipo_reactor_categoria')
    context = {
        'tipos': tipos
    }
    return render(request, 'reactores/comparador.html', context)


# ==============================================================================
# ## VISTAS DE API (PARA SER USADAS POR JAVASCRIPT) ##
# ==============================================================================

def api_datos_mapa(request):
    """
    API que devuelve datos agregados por país para colorear el mapa del atlas.
    Incluye el diccionario de alias definitivo y verificado.
    """
    # --- DICCIONARIO DE ALIAS DEFINITIVO ---
    alias_paises = {
        # El nombre en la BD es 'United States Of America', el del mapa es 'United States of America'
        "United States Of America": "United States of America",
        
        # 'South Korea' y 'Russia' ya coinciden en la BD y en el mapa, por lo que no necesitan alias.
    }

    datos_paises = Reactor.objects.values('pais').annotate(total_reactores=Count('id')).order_by('pais')
    
    resultado = []
    for item in datos_paises:
        # Usamos el alias si existe; si no, usamos el nombre original de la base de datos
        nombre_pais_mapa = alias_paises.get(item['pais'], item['pais'])
        resultado.append({
            'pais': nombre_pais_mapa,
            'db_name': item['pais'], # El nombre original para hacer búsquedas
            'total_reactores': item['total_reactores']
        })
        
    return JsonResponse(resultado, safe=False)


def api_reactores_por_pais(request):
    """
    API: Devuelve la lista de reactores de un país específico.
    Usado por el atlas.
    """
    pais = request.GET.get('pais')
    if not pais:
        return JsonResponse({'reactores': []})
    
    reactores = Reactor.objects.filter(pais=pais).order_by('nombre')
    lista_reactores = list(reactores.values('id', 'nombre', 'potencia_neta'))
    return JsonResponse({'reactores': lista_reactores})


def api_paises_por_tipo(request):
    """
    API: Devuelve los países que tienen un TIPO de reactor específico.
    """
    tipo = request.GET.get('tipo')
    if not tipo:
        return JsonResponse({'paises': []})
    
    paises = Reactor.objects.filter(tipo_reactor_categoria=tipo).values('pais').distinct().order_by('pais')
    return JsonResponse({'paises': list(paises)})


def api_reactores_por_tipo_y_pais(request):
    """
    API: Devuelve los reactores para un TIPO y país específicos.
    """
    tipo = request.GET.get('tipo')
    pais = request.GET.get('pais')
    if not tipo or not pais:
        return JsonResponse({'reactores': []})
    
    reactores = Reactor.objects.filter(tipo_reactor_categoria=tipo, pais=pais).order_by('nombre')
    lista_reactores = list(reactores.values('id', 'nombre'))
    return JsonResponse({'reactores': lista_reactores})


def api_reactor_datos(request, pk):
    """
    API: Devuelve todos los datos de un solo reactor en formato JSON.
    Usado por el modal de detalles tanto en el atlas como en el comparador.
    """
    try:
        reactor = Reactor.objects.get(pk=pk)
        datos = model_to_dict(reactor)
        return JsonResponse({'success': True, 'datos': datos})
    except Reactor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Reactor no encontrado'}, status=404)


def api_reactor_historial(request, pk):
    try:
        reactor = Reactor.objects.get(pk=pk)
        # Obtenemos todo el historial relacionado y lo convertimos a una lista de diccionarios
        historial = list(reactor.historial.all().values())
        return JsonResponse({'success': True, 'historial': historial})
    except Reactor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Reactor no encontrado'}, status=404)


def vista_ciclo_vida(request):
    # Pasamos los países para poder filtrar el gráfico
    context = {
        'paises': Reactor.objects.values_list('pais', flat=True).distinct().order_by('pais')
    }
    return render(request, 'reactores/ciclo_vida.html', context)


# --- NUEVA API PARA ALIMENTAR LA GRÁFICA ---
def api_datos_ciclo_vida(request):
    reactores = Reactor.objects.exclude(fecha_primera_conexion__isnull=True)
    
    datos_para_grafica = []
    for reactor in reactores:
        fecha_inicio = reactor.fecha_primera_conexion
        
        # Determinamos la fecha de fin y el estado
        if reactor.fecha_cierre_permanente:
            fecha_fin = reactor.fecha_cierre_permanente
            estado = "Desmantelado"
        else:
            # Asumimos una vida útil de 60 años para la proyección
            fecha_fin = fecha_inicio + timedelta(days=60*365.25)
            estado = "Operativo (Proyección a 60 años)"
            
        datos_para_grafica.append({
            'nombre': reactor.nombre,
            'pais': reactor.pais,
            'inicio': fecha_inicio.isoformat(),
            'fin': fecha_fin.isoformat(),
            'estado': estado,
        })
        
    return JsonResponse(datos_para_grafica, safe=False)



# --- NUEVA VISTA PARA LA PÁGINA DE LA ENCICLOPEDIA ---
def vista_enciclopedia_tipos(request):
    tipos = Reactor.objects.exclude(tipo_reactor_categoria__isnull=True).values_list('tipo_reactor_categoria', flat=True).distinct().order_by('tipo_reactor_categoria')
    context = {
        'tipos': tipos
    }
    return render(request, 'reactores/enciclopedia_tipos.html', context)


# --- NUEVA API QUE CALCULA TODO PARA UN MODELO ESPECÍFICO ---
def api_datos_tipo(request, tipo):
    """
    API que devuelve un análisis completo y agregado para un tipo de reactor.
    """
    # Filtro base para todos los reactores de este tipo
    reactores_del_tipo = Reactor.objects.filter(tipo_reactor_categoria=tipo)

    # 1. Cálculos de Estadísticas Clave
    unidades_totales = reactores_del_tipo.count()
    potencia_total_gw = reactores_del_tipo.aggregate(total=Sum('potencia_neta'))['total'] or 0

    paises_operadores = list(reactores_del_tipo.values_list('pais', flat=True).distinct().order_by('pais'))

    # Cálculo del tiempo promedio de construcción en años
    tiempo_construccion_dias = reactores_del_tipo.exclude(
        fecha_inicio_construccion__isnull=True
    ).exclude(
        fecha_primera_conexion__isnull=True
    ).annotate(
        duracion=F('fecha_primera_conexion') - F('fecha_inicio_construccion')
    ).aggregate(
        promedio=Avg('duracion')
    )['promedio']
    
    tiempo_promedio_construccion = round(tiempo_construccion_dias.days / 365.25, 1) if tiempo_construccion_dias else None

    # 2. Datos para la Gráfica de Rendimiento Agregado
    historial_agregado = HistorialRendimiento.objects.filter(
        reactor__tipo_reactor_categoria=tipo
    ).values('ano').annotate(
        produccion_promedio=Avg('electricidad_suministrada')
    ).order_by('ano')

    # 3. Datos para la Línea de Tiempo de Despliegue
    despliegue_anual = reactores_del_tipo.exclude(
        fecha_primera_conexion__isnull=True
    ).extra(
        select={'ano_conexion': "EXTRACT(year FROM fecha_primera_conexion)"}
    ).values('ano_conexion').annotate(
        total=Count('id')
    ).order_by('ano_conexion')

    # 4. Lista completa de reactores de este tipo
    lista_reactores = list(reactores_del_tipo.values('id', 'nombre', 'pais', 'status', 'potencia_neta'))

    # 5. Ensamblar la respuesta JSON
    respuesta = {
        'estadisticas': {
            'unidades_totales': unidades_totales,
            'potencia_total_gw': round(potencia_total_gw / 1000, 2),
            'paises_operadores': paises_operadores,
            'tiempo_promedio_construccion': tiempo_promedio_construccion
        },
        'grafica_rendimiento': list(historial_agregado),
        'grafica_despliegue': list(despliegue_anual),
        'lista_reactores': lista_reactores
    }

    return JsonResponse(respuesta)