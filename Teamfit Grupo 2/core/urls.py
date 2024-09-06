from django.urls import path
from django.contrib.auth import views as auth_views

from .views import subirProyectos, pagina_principal, ver_proyectos,subir_empleados,ver_proyectos_empleados, asignar_recursos,limpiar_asignaciones, proyectos_a_asignar, limpiar_proyectos, asignaciones_list

urlpatterns = [ 
    path('subirProyectos',subirProyectos, name="subirProyectos"),
    path('', pagina_principal, name="index"),
    path('subirProyectos/<upload>',subirProyectos, name="decidirSubida"),
    path('ver-proyectos/', ver_proyectos, name='ver_proyectos'),
    path('subir_empleados/', subir_empleados, name='subir_empleados'),
    path('ver_proyectos_empleados/', ver_proyectos_empleados, name='ver_proyectos_empleados'),
    path('asignar_recursos/', asignar_recursos, name='asignar_recursos'),
    path('proyectos_a_asignar/', proyectos_a_asignar, name='proyectos_a_asignar'),
    path('limpiar_asignaciones/', limpiar_asignaciones, name='limpiar_asignaciones'),
    path('limpiar_proyectos/', limpiar_proyectos, name='limpiar_proyectos'),
    path('asignaciones/', asignaciones_list, name='asignaciones_list'),
]