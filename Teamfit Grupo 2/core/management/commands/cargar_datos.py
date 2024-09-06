# proyectos/management/commands/cargar_datos.py
from django.core.management.base import BaseCommand
from core.models import TipoProyecto, Recurso, Disponibilidad, Proyecto

class Command(BaseCommand):
    help = 'Carga datos de prueba en la base de datos'

    def handle(self, *args, **kwargs):
        # Crear tipos de proyecto
        tp1 = TipoProyecto.objects.create(nombre="Proyecto A", prioridad=3)
        tp2 = TipoProyecto.objects.create(nombre="Proyecto B", prioridad=5)
        tp3 = TipoProyecto.objects.create(nombre="Proyecto C", prioridad=1)

        # Crear recursos
        recurso1 = Recurso.objects.create(nombre="Recurso 1", rol="Developer", prioridad=2, horas_promedio=8)
        recurso2 = Recurso.objects.create(nombre="Recurso 2", rol="Developer", prioridad=1, horas_promedio=8)
        recurso3 = Recurso.objects.create(nombre="Recurso 3", rol="Tester", prioridad=3, horas_promedio=8)

        # Crear disponibilidad de recursos por semana
        for semana in range(1, 53):
            Disponibilidad.objects.create(recurso=recurso1, semana=semana, horas_disponibles=40)
            Disponibilidad.objects.create(recurso=recurso2, semana=semana, horas_disponibles=40)
            Disponibilidad.objects.create(recurso=recurso3, semana=semana, horas_disponibles=40)

        # Crear proyectos
        proyecto1 = Proyecto.objects.create(nombre="Proyecto Alpha", tipo_proyecto=tp1, horas_demandadas=120, rol_requerido="Developer", semana=1)
        proyecto2 = Proyecto.objects.create(nombre="Proyecto Beta", tipo_proyecto=tp2, horas_demandadas=200, rol_requerido="Developer", semana=2)
        proyecto3 = Proyecto.objects.create(nombre="Proyecto Gamma", tipo_proyecto=tp3, horas_demandadas=80, rol_requerido="Tester", semana=1)

        self.stdout.write(self.style.SUCCESS('Datos de prueba cargados exitosamente.'))
