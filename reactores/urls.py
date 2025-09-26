# En reactores/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- VISTAS DE PÁGINAS PRINCIPALES ---
    # El Dashboard es la página de inicio de la app
    path('', views.vista_dashboard, name='dashboard'),
    
    # La página del Atlas Interactivo
    path('atlas/', views.vista_atlas, name='atlas'),
    
    # La página del Comparador Interactivo
    path('comparador-interactivo/', views.vista_comparador, name='comparador'),

    # --- VISTAS DE API (usadas por JavaScript) ---
    
    # API para el mapa del atlas (colores y conteo)
    path('api/datos-mapa/', views.api_datos_mapa, name='api_datos_mapa'),
    
    # API para obtener reactores de un país (usada por el atlas)
    path('api/reactores-por-pais/', views.api_reactores_por_pais, name='api_reactores_por_pais'),
    
    # API para obtener países según un modelo (usada por el comparador)
    path('api/paises-por-modelo/', views.api_paises_por_modelo, name='api_paises_por_modelo'),
    
    # API para obtener reactores según modelo y país (usada por el comparador)
    path('api/reactores-por-modelo-y-pais/', views.api_reactores_por_modelo_y_pais, name='api_reactores_por_modelo_y_pais'),
    
    # API para obtener los datos JSON completos de un reactor (usada por los modales de detalle)
    path('api/reactor-datos/<int:pk>/', views.api_reactor_datos, name='api_reactor_datos'),
]