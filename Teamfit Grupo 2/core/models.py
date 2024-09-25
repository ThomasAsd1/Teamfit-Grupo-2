from django.db import models
from datetime import date
from datetime import datetime

# Modelo TipoProyecto
class TipoProyecto(models.Model):
    nombre = models.CharField(max_length=255)
    prioridad = models.IntegerField()  # Cuanto mayor es el número, mayor es la prioridad

    class Meta:
        db_table = "TipoProyecto"

    def __str__(self):
        return self.nombre

# Modelo Recurso
class Recurso(models.Model):
    nombre = models.CharField(max_length=255)
    rol = models.CharField(max_length=100)  # Por ejemplo, "Ingeniero de Proyectos", "Jefe de Proyecto"
    prioridad = models.IntegerField()  # Cuanto mayor es el número, mayor es la prioridad
    horas_promedio = models.IntegerField(default=40)  # Horas promedio disponibles por semana

    class Meta:
        db_table = "Recurso"

    def __str__(self):
        return f'{self.nombre} - {self.rol}'

# Modelo Disponibilidad
class Disponibilidad(models.Model):
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE)
    semana = models.IntegerField()  # De 1 a 52
    horas_disponibles = models.IntegerField(default=40)

    class Meta:
        db_table = "Disponibilidad"

    def __str__(self):
        return f'{self.recurso.nombre} - Semana {self.semana}'

# Modelo Proyecto
class Proyecto(models.Model):
    nombre = models.CharField(max_length=255)
    tipo_proyecto = models.ForeignKey(TipoProyecto, on_delete=models.CASCADE)
    horas_demandadas = models.IntegerField()
    rol_requerido = models.CharField(max_length=100)  # Similarmente, puede ser una ForeignKey si tienes un modelo de Rol
    semana_inicio = models.IntegerField()  # Semana de inicio del proyecto
    duracion_semanas = models.IntegerField()  # Duración del proyecto en semanas

    class Meta:
        db_table = "Proyecto"
    def __str__(self):
        return self.nombre

# Modelo Asignacion
class Asignacion(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE)
    semana = models.IntegerField()
    horas_asignadas = models.IntegerField()

    class Meta:
        db_table = "Asignacion"
    def __str__(self):
        return f'{self.proyecto.nombre} - {self.recurso.nombre} - Semana {self.semana} - {self.horas_asignadas} horas'



class AsignacionControl(models.Model):
    fecha_ultimo_ejecucion = models.DateField(null=True, blank=True)
    ejecuciones_exitosas = models.IntegerField(default=0)  # Agregar este campo

    def puede_ejecutar(self):
        if not self.fecha_ultimo_ejecucion:
            return True
        return self.fecha_ultimo_ejecucion < date.today()

    def registrar_ejecucion(self, exito=True):
        self.fecha_ultimo_ejecucion = date.today()
        if exito:
            self.ejecuciones_exitosas += 1  # Incrementa en caso de éxito
        self.save()