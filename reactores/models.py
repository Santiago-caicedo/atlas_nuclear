from django.db import models

class Reactor(models.Model):
    # Usaremos el nombre como identificador único
    nombre = models.CharField(max_length=255, unique=True, verbose_name="Nombre")
    nombre_alternativo = models.CharField(max_length=255, null=True, blank=True)
    pais = models.CharField(max_length=100, null=True, blank=True, verbose_name="País")
    status = models.CharField(max_length=100, null=True, blank=True, verbose_name="Status")
    dueño = models.CharField(max_length=255, null=True, blank=True, verbose_name="Dueño")
    operador = models.CharField(max_length=255, null=True, blank=True, verbose_name="Operador")
    modelo = models.CharField(max_length=100, null=True, blank=True, verbose_name="Modelo")
    potencia_neta = models.IntegerField(null=True, blank=True, verbose_name="Potencia Neta (MWe)")
    tipo_reactor_categoria = models.CharField(max_length=20, null=True, blank=True, db_index=True, verbose_name="Categoría de Tipo")
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    capacidad_termica = models.IntegerField(null=True, blank=True, verbose_name="Capacidad Térmica (MWt)")
    capacidad_bruta = models.IntegerField(null=True, blank=True, verbose_name="Capacidad Bruta (MWe)")
    fecha_inicio_construccion = models.DateField(null=True, blank=True)
    fecha_primera_conexion = models.DateField(null=True, blank=True)
    fecha_cierre_permanente = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Reactor"
        verbose_name_plural = "Reactores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class HistorialRendimiento(models.Model):
    # Relación con el reactor principal (un reactor puede tener muchos historiales)
    reactor = models.ForeignKey(Reactor, related_name='historial', on_delete=models.CASCADE)
    
    # Campos que coinciden con el JSON que encontraste
    ano = models.IntegerField(verbose_name="Año")
    electricidad_suministrada = models.FloatField(null=True, blank=True)
    potencia_referencia = models.IntegerField(null=True, blank=True)
    tiempo_en_linea_anual = models.FloatField(null=True, blank=True)
    factor_operacion = models.FloatField(null=True, blank=True)
    factor_carga_anual = models.FloatField(null=True, blank=True)

    class Meta:
        # Nos aseguramos de que no haya entradas duplicadas para el mismo reactor en el mismo año
        unique_together = ('reactor', 'ano')
        ordering = ['ano']

    def __str__(self):
        return f"{self.reactor.nombre} - {self.ano}"