import json
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.forms.models import model_to_dict
from .models import Reactor
from django.db.models import Avg

# ==============================================================================
# ## VISTAS PRINCIPALES DE PÁGINAS ##
# ==============================================================================

def vista_dashboard(request):
    # --- Cálculos desde la base de datos ---
    total_reactores = Reactor.objects.count()
    paises_con_reactores = Reactor.objects.values('pais').distinct().count()
    potencia_total = Reactor.objects.aggregate(total_power=Sum('potencia_neta'))['total_power']
    top_paises = Reactor.objects.values('pais').annotate(total=Count('id')).order_by('-total')[:5]
    
    # --- NUEVA LÍNEA: Obtenemos la lista completa de países ---
    todos_los_paises = Reactor.objects.values('pais').annotate(total=Count('id')).order_by('-total')

    # --- Datos para las gráficas ---
    energy_mix_data = {
        'labels': ['Combustibles Fósiles', 'Hidroeléctrica', 'Nuclear', 'Eólica y Solar', 'Otras Renovables'],
        'data': [59, 15, 9, 13, 4],
    }
    top_paises_chart_data = {
        'labels': [p['pais'] for p in top_paises],
        'data': [p['total'] for p in top_paises],
    }

    context = {
        'total_reactores': total_reactores,
        'paises_con_reactores': paises_con_reactores,
        'potencia_total_gw': round(potencia_total / 1000) if potencia_total else 0,
        'top_paises': top_paises,
        'todos_los_paises': todos_los_paises, # <-- Añadimos la nueva lista al contexto
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
    Pasa la lista de modelos de reactores para el primer filtro.
    """
    modelos = Reactor.objects.exclude(modelo__isnull=True).exclude(modelo__exact='').values('modelo').distinct().order_by('modelo')
    context = {
        'modelos': modelos
    }
    return render(request, 'reactores/comparador.html', context)


# ==============================================================================
# ## VISTAS DE API (PARA SER USADAS POR JAVASCRIPT) ##
# ==============================================================================

def api_datos_mapa(request):
    """
    API: Devuelve datos agregados por país para colorear el mapa del atlas.
    Incluye alias para que los nombres coincidan con el archivo GeoJSON.
    """
    alias_paises = {
        "USA": "United States of America",
        "Russia": "Russian Federation",
        "South Korea": "Republic of Korea",
    }
    datos_paises = Reactor.objects.values('pais').annotate(total_reactores=Count('id')).order_by('pais')
    resultado = []
    for item in datos_paises:
        nombre_pais_mapa = alias_paises.get(item['pais'], item['pais'])
        resultado.append({
            'pais': nombre_pais_mapa,
            'db_name': item['pais'],
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


def api_paises_por_modelo(request):
    """
    API: Devuelve la lista de países que tienen un modelo de reactor específico.
    Usado por el filtro del comparador.
    """
    modelo = request.GET.get('modelo')
    if not modelo:
        return JsonResponse({'paises': []})
    
    paises = Reactor.objects.filter(modelo=modelo).values('pais').distinct().order_by('pais')
    return JsonResponse({'paises': list(paises)})


def api_reactores_por_modelo_y_pais(request):
    """
    API: Devuelve la lista de reactores para un modelo y país específicos.
    Usado por el filtro del comparador.
    """
    modelo = request.GET.get('modelo')
    pais = request.GET.get('pais')
    if not modelo or not pais:
        return JsonResponse({'reactores': []})
    
    reactores = Reactor.objects.filter(modelo=modelo, pais=pais).order_by('nombre')
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