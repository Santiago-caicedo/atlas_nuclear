# En config/urls.py
from django.contrib import admin
from django.urls import path, include # Asegúrate de que 'include' esté importado

urlpatterns = [
    path('admin/', admin.site.urls),
    # Añade esta línea. Todo lo que empiece con 'comparador/' será manejado por nuestra app.
    path('', include('reactores.urls')),
]