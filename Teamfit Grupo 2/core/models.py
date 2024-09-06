from django.db import models
#test
# Modelo TipoProyecto
class TipoProyecto(models.Model):
    nombre = models.CharField(max_length=255)
    prioridad = models.IntegerField()

    def __str__(self):
        return self.nombre

# Modelo Recurso
class Recurso(models.Model):
    nombre = models.CharField(max_length=255)
    rol = models.CharField(max_length=100)  # Puedes cambiarlo por ForeignKey si tienes un modelo de Rol separado
    prioridad = models.IntegerField()
    horas_promedio = models.IntegerField(default=8)

    def __str__(self):
        return self.nombre

# Modelo Disponibilidad
class Disponibilidad(models.Model):
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE)
    semana = models.IntegerField()  # De 1 a 52
    horas_disponibles = models.IntegerField(default=40)

    def __str__(self):
        return f'{self.recurso.nombre} - Semana {self.semana}'

# Modelo Proyecto
class Proyecto(models.Model):
    nombre = models.CharField(max_length=255)
    tipo_proyecto = models.ForeignKey(TipoProyecto, on_delete=models.CASCADE)
    horas_demandadas = models.IntegerField()
    rol_requerido = models.CharField(max_length=100)  # Similarmente, puede ser una ForeignKey si tienes un modelo de Rol
    semana = models.IntegerField()  # Semana de inicio del proyecto

    def __str__(self):
        return self.nombre

# Modelo Asignacion
class Asignacion(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE, null=True)    
    semana = models.IntegerField(null=True)
    horas_asignadas = models.IntegerField()

    def __str__(self):
        return f'{self.proyecto.nombre} - {self.recurso.nombre} - Semana {self.semana}'

