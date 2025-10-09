import requests
import time
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from reactores.models import Reactor

class Command(BaseCommand):
    help = 'Actualiza latitud y longitud extrayendo los datos de los campos ocultos del HTML.'

    def handle(self, *args, **kwargs):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Referer': 'https://world-nuclear.org/nuclear-reactor-database/'
        }

        reactores_a_actualizar = Reactor.objects.filter(latitud__isnull=True)
        total = reactores_a_actualizar.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ ¡Todos los reactores ya tienen sus coordenadas!"))
            return

        self.stdout.write(self.style.SUCCESS(f"🚀 Iniciando la actualización de coordenadas para {total} reactores..."))
        
        for i, reactor in enumerate(reactores_a_actualizar):
            self.stdout.write(f"({i+1}/{total}) Buscando coordenadas para: {reactor.nombre}...")
            
            reactor_name_slug = reactor.nombre.title().replace(' ', '-')
            detail_page_url = f"https://world-nuclear.org/nuclear-reactor-database/details/{reactor_name_slug}"

            try:
                # 1. Descargamos el HTML de la página de detalles
                page_response = requests.get(detail_page_url, headers=headers, timeout=15)
                if page_response.status_code != 200:
                    self.stdout.write(self.style.ERROR(f"  -> Error {page_response.status_code} al acceder a la página."))
                    continue

                # 2. Analizamos el HTML con BeautifulSoup
                soup = BeautifulSoup(page_response.content, 'html.parser')
                
                # 3. Buscamos los campos <input> por su ID
                lat_input = soup.find('input', {'id': 'Latitude'})
                lon_input = soup.find('input', {'id': 'Longitude'})

                # 4. Verificamos que los encontramos y que tienen un valor
                if lat_input and lon_input and lat_input.get('value') and lon_input.get('value'):
                    try:
                        lat = float(lat_input['value'])
                        lon = float(lon_input['value'])
                        
                        reactor.latitud = lat
                        reactor.longitud = lon
                        reactor.save(update_fields=['latitud', 'longitud'])
                        self.stdout.write(self.style.SUCCESS(f"  -> Coordenadas guardadas: ({lat}, {lon})"))
                    except (ValueError, TypeError):
                        self.stdout.write(self.style.ERROR("  -> Se encontraron los campos, pero sus valores no son números válidos."))
                else:
                    self.stdout.write(self.style.WARNING("  -> No se encontraron los campos #Latitude o #Longitude en el HTML."))

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  -> Error de conexión: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  -> Ocurrió un error inesperado: {e}"))
            
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS("\n🎉 ¡Actualización de coordenadas completada!"))