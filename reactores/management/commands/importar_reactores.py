import requests
from django.core.management.base import BaseCommand
from reactores.models import Reactor
from datetime import datetime

class Command(BaseCommand):
    help = 'Extrae datos de reactores usando la nueva API GET y los guarda en la BD.'

    # Función auxiliar para convertir fechas de forma segura
    def parse_date(self, date_string):
        if not date_string:
            return None
        try:
            # El formato de la API es "YYYY-MM-DDTHH:mm:ss"
            return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S').date()
        except (ValueError, TypeError):
            return None

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("🚀 Iniciando extracción con la nueva API GET..."))
        
        page_number = 1
        reactores_procesados = 0

        # Borramos los datos antiguos para empezar de cero
        Reactor.objects.all().delete()
        self.stdout.write(self.style.WARNING("Datos antiguos eliminados."))

        while True:
            # Construimos la URL para cada página
            API_URL = f"https://www.world-nuclear.org/nuclear-reactor-database/getreactordata?pageSize=100&pageNumber={page_number}"
            
            self.stdout.write(f"Obteniendo página {page_number}...")

            try:
                response = requests.get(API_URL)
                response.raise_for_status()  # Lanza un error si la petición falla (ej. 404, 500)
                
                api_data = response.json()
                reactores_en_pagina = api_data.get("data", [])

                # Si la página no devuelve reactores, hemos terminado
                if not reactores_en_pagina:
                    self.stdout.write(self.style.SUCCESS("No se encontraron más reactores. Proceso finalizado."))
                    break

                for reactor_data in reactores_en_pagina:
                    Reactor.objects.create(
                        nombre=reactor_data.get('reactorName'),
                        nombre_alternativo=reactor_data.get('alternateName'),
                        pais=reactor_data.get('location'),
                        status=reactor_data.get('status'),
                        dueño=reactor_data.get('owner'),
                        operador=reactor_data.get('operator'),
                        modelo=reactor_data.get('model'),
                        potencia_neta=reactor_data.get('referenceUnitPowerNetCapacity'),
                        capacidad_termica=reactor_data.get('thermalCapacity'),
                        capacidad_bruta=reactor_data.get('grossCapacity'),
                        fecha_inicio_construccion=self.parse_date(reactor_data.get('constructionStartDate')),
                        fecha_primera_conexion=self.parse_date(reactor_data.get('firstGridConnection')),
                        fecha_cierre_permanente=self.parse_date(reactor_data.get('permanentShutdownDate'))
                    )
                    reactores_procesados += 1

                page_number += 1

            except requests.exceptions.HTTPError as e:
                self.stdout.write(self.style.ERROR(f"Error HTTP: {e}. Deteniendo el script."))
                break
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Error de conexión: {e}. Deteniendo el script."))
                break
            except ValueError: # Error de JSON
                self.stdout.write(self.style.ERROR("No se pudo decodificar la respuesta JSON. Deteniendo."))
                break

        self.stdout.write(self.style.SUCCESS(f"🎉 ¡Éxito! Se guardaron {reactores_procesados} reactores en la base de datos."))