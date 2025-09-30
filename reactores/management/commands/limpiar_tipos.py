# En reactores/management/commands/limpiar_tipos.py
from django.core.management.base import BaseCommand
from reactores.models import Reactor

class Command(BaseCommand):
    help = 'Limpia y estandariza el campo de tipo de reactor en categorías simples, leyendo desde el campo "modelo".'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando limpieza de tipos de reactores...")
        reactores = Reactor.objects.all()
        actualizados = 0

        for reactor in reactores:
            # --- CORRECCIÓN: Leemos desde reactor.modelo ---
            texto_fuente = reactor.modelo or ""
            categoria = None

            # Lógica para asignar categorías basadas en palabras clave
            if "PWR" in texto_fuente.upper() or "PRESSURIZED" in texto_fuente.upper():
                categoria = "PWR"
            elif "BWR" in texto_fuente.upper() or "BOILING" in texto_fuente.upper():
                categoria = "BWR"
            elif "PHWR" in texto_fuente.upper() or "CANDU" in texto_fuente.upper():
                categoria = "PHWR"
            elif "GCR" in texto_fuente.upper() or "GAS" in texto_fuente.upper() or "AGR" in texto_fuente.upper():
                categoria = "GCR"
            elif "LWGR" in texto_fuente.upper() or "RBMK" in texto_fuente.upper():
                categoria = "LWGR"
            elif "FBR" in texto_fuente.upper() or "FAST" in texto_fuente.upper():
                categoria = "FBR"
            
            if categoria and reactor.tipo_reactor_categoria != categoria:
                reactor.tipo_reactor_categoria = categoria
                reactor.save()
                actualizados += 1
        
        self.stdout.write(self.style.SUCCESS(f"¡Limpieza completada! Se actualizaron {actualizados} reactores."))