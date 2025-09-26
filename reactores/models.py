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