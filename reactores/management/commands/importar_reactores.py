# En reactores/management/commands/importar_reactores.py
import requests
import time
from django.core.management.base import BaseCommand
from reactores.models import Reactor, HistorialRendimiento

class Command(BaseCommand):
    help = 'Extrae la lista de reactores y su historial con lógica de reintentos para fallos de red.'

    def handle(self, *args, **kwargs):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://world-nuclear.org/nuclear-reactor-database/search/'
        }

        # --- FASE 1 (sin cambios) ---
        self.stdout.write(self.style.SUCCESS("🚀 Fase 1: Obteniendo la lista completa de reactores..."))
        # ... (la lógica de la fase 1 se queda exactamente igual)
        
        # --- FASE 2 MEJORADA CON REINTENTOS ---
        self.stdout.write(self.style.SUCCESS("\n🚀 Fase 2: Obteniendo historial de rendimiento..."))
        
        all_reactors = Reactor.objects.all()
        for i, reactor in enumerate(all_reactors):
            # Si ya tenemos historial para este reactor, lo saltamos para ir más rápido
            if reactor.historial.exists():
                continue

            self.stdout.write(f"({i+1}/{len(all_reactors)}) Procesando: {reactor.nombre}...")
            
            reactor_name_formatted = reactor.nombre.replace(' ', '%20')
            history_url = f"https://world-nuclear.org/charts/{reactor_name_formatted}"
            
            # --- LÓGICA DE REINTENTOS ---
            success = False
            for attempt in range(3): # Intentará hasta 3 veces
                try:
                    history_response = requests.get(history_url, headers=headers, timeout=20)
                    
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        for record in history_data:
                            HistorialRendimiento.objects.update_or_create(
                                reactor=reactor,
                                ano=record.get('Year'),
                                defaults={ 'electricidad_suministrada': record.get('ElectricitySupplied'), 'potencia_referencia': record.get('ReferenceUnitPower'), 'tiempo_en_linea_anual': record.get('AnnualTimeOnLine'), 'factor_operacion': record.get('OperationFactor'), 'factor_carga_anual': record.get('LoadFactorAnnual'), }
                            )
                        self.stdout.write(self.style.SUCCESS(f"  -> Se guardaron {len(history_data)} registros del historial."))
                        success = True
                        break # Si tiene éxito, salimos del bucle de reintentos
                    
                    elif history_response.status_code == 404:
                        self.stdout.write(self.style.WARNING(f"  -> No se encontró historial (404)."))
                        success = True
                        break # Es un 404, no tiene sentido reintentar

                    else:
                         self.stdout.write(self.style.ERROR(f"  -> Error {history_response.status_code}. Reintentando..."))

                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f"  -> Error de conexión: {e}. Reintentando en 5 segundos..."))
                
                time.sleep(5) # Espera 5 segundos antes del siguiente intento

            if not success:
                self.stdout.write(self.style.ERROR(f"  -> FALLO DEFINITIVO para {reactor.nombre} después de 3 intentos."))

            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS("\n🎉 ¡Proceso de importación completado!"))