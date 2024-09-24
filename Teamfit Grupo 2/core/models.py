from django.db import models

class proyectos(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name="ID Proyecto")
    proyecto = models.CharField(max_length=12, blank=False, null=False, verbose_name="Proyecto")
    lineaNegocio = models.CharField(max_length=6, blank=False, null=False, verbose_name="Línea de Negocio")
    tipo = models.CharField(max_length=50, blank=False, null=False, verbose_name="Tipo de Proyecto")
    cliente = models.IntegerField(blank=True, null=True, verbose_name="ID Cliente")
    createDate = models.DateTimeField(null=False, blank=False, verbose_name="Fecha de creación")
    cierre = models.DateField(null=False, blank=False, verbose_name="Cierre del proyecto")
    egresosNoHHCLP = models.IntegerField(null=False, blank=False, verbose_name="Egresos no HH CLP")
    montoOfertaCLP = models.IntegerField(null=False, blank=False, verbose_name="Monto Oferta CLP")
    usoAgencia = models.BooleanField(null=False, blank=False, default=0, verbose_name="Apoyo de Agencia")
    ocupacionInicio = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, verbose_name="Porcentaje de uso inicial")
    disponibilidad = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, verbose_name="Porcentaje de disponibilidad")
    utilizacion = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, verbose_name="Porcentaje de utilización")

    class Meta:
        db_table = 'PROYECTOS'

    def str(self):
        return str(self.proyecto) + " - " + str(self.lineaNegocio) + " - " + str(self.tipo)

class empleado(models.Model):
    id_empleado= models.IntegerField(primary_key=True, verbose_name="ID Empleado")
    nombre = models.CharField(max_length=100,null=False,blank=False,verbose_name="Nombre del empleado")
    cargo = models.CharField(max_length=100,null=False,blank=False,verbose_name="Cargo o Rol del empleado")
    telefono = models.CharField(max_length=15,null=False,blank=False,verbose_name="Numero de contacto")
    categoria = models.IntegerField(null=False,blank=False)
    horas_laborales = models.IntegerField(default=8,null=False,blank=False,verbose_name="Jornada laboral")  # Horas laborales por día
    disponibilidad = models.IntegerField(null=False,blank=False,verbose_name="Horas disponible del empleado")  # Horas disponibles
    estado = models.CharField(max_length=20, choices=[('Disponible', 'Disponible'), ('Ocupado', 'Ocupado')])

    class Meta:
        db_table = 'EMPLEADOS'

    def __str__(self):
        return self.nombre

class asignacion(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID Asignación")
    empleado = models.ForeignKey(empleado, on_delete=models.CASCADE, verbose_name="Empleado Asignado")
    proyecto = models.ForeignKey(proyectos, on_delete=models.CASCADE, verbose_name="Proyecto Asignado")
    horas_asignadas = models.IntegerField(null=False, blank=False, verbose_name="Horas Asignadas")
    categoria = models.IntegerField(null=False, blank=False, verbose_name="Categoría del Empleado")
    estado_empleado = models.CharField(max_length=20, choices=[('Disponible', 'Disponible'), ('Ocupado', 'Ocupado')], verbose_name="Estado del Empleado")
    disponibilidad_restante = models.IntegerField(null=False, blank=False, verbose_name="Disponibilidad Restante del Empleado")
    ocupacion = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, verbose_name="Ocupación")
    disponibilidad = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, verbose_name="Disponibilidad")
    utilizacion = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, verbose_name="Utilización")

    class Meta:
        db_table = 'ASIGNACION'

    def __str__(self):
        return f"{self.empleado.nombre} - {self.proyecto.proyecto} - {self.horas_asignadas}h"