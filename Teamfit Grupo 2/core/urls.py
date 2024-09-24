from django.urls import path
from django.contrib.auth import views as auth_views
from .views import asignaciones_data,proyectos_data,recursos_asignados_data,eliminar_asignaciones
# , cargar_asignaciones
from .views import subirProyectos, pagina_principal, ver_proyectos,subir_empleados,ver_proyectos_empleados, asignar_recursos,asignaciones_list, ejecutar_asignacion, asignaciones_list
# limpiar_asignaciones, proyectos_a_asignar, limpiar_proyectos, 

urlpatterns = [ 
    path('subirProyectos',subirProyectos, name="subirProyectos"),
    path('', pagina_principal, name="index"),
    path('subirProyectos/<upload>',subirProyectos, name="decidirSubida"),
    path('ver-proyectos/', ver_proyectos, name='ver_proyectos'),
    path('subir_empleados/', subir_empleados, name='subir_empleados'),
    path('ver_proyectos_empleados/', ver_proyectos_empleados, name='ver_proyectos_empleados'),
    path('asignar_recursos/', asignar_recursos, name='asignar_recursos'),
    # path('proyectos_a_asignar/', proyectos_a_asignar, name='proyectos_a_asignar'),
    # path('limpiar_asignaciones/', limpiar_asignaciones, name='limpiar_asignaciones'),
    # path('limpiar_proyectos/', limpiar_proyectos, name='limpiar_proyectos'),
    path('asignaciones/', asignaciones_list, name='asignaciones_list'),
    # path('cargar_asignaciones/', cargar_asignaciones, name='cargar_asignaciones'),
    path('asignaciones_data/', asignaciones_data, name='asignaciones_data'),
    path('proyectos_data/', proyectos_data, name='proyectos_data'),
    path('recursos_asignados_data/', recursos_asignados_data, name='recursos_asignados_data'),  # Nueva URL para los totales semanales
    path('ejecutar_asignacion/', ejecutar_asignacion, name='ejecutar_asignacion'),
    path('eliminar-asignaciones/', eliminar_asignaciones, name='eliminar_asignaciones'),
]
    # otras URLs...
