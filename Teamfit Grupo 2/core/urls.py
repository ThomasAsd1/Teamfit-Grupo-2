from django.urls import path
from .views import (
    subirProyectos,
    pagina_principal,
    ver_proyectos,
    asignaciones_list,
    ejecutar_asignacion,
    generar_excel_proyectos,
    generar_excel_asignacion,
    eliminar_asignaciones,
    asignaciones_data,
    horas_por_recurso_data,
    horas_por_proyecto_data,
    generar_excel_recursos

)

urlpatterns = [
    path('', pagina_principal, name='index'),
    path('subirProyectos/', subirProyectos, name='subirProyectos'),
    path('subirProyectos/<upload>/', subirProyectos, name='decidirSubida'),
    path('ver-proyectos/', ver_proyectos, name='ver_proyectos'),
    
    # Vistas relacionadas con la gestión de asignaciones y proyectos
    path('asignaciones/', asignaciones_list, name='asignaciones_list'),
    path('asignaciones/data/', asignaciones_data, name='asignaciones_data'),
    path('horas_por_recurso_data/', horas_por_recurso_data, name='horas_por_recurso_data'),
    path('horas_por_proyecto_data/', horas_por_proyecto_data, name='horas_por_proyecto_data'),

    # Vistas nuevas para los reportes adicionales


    # Acciones sobre las asignaciones y generación de reportes
    path('ejecutar_asignacion/', ejecutar_asignacion, name='ejecutar_asignacion'),
    path('eliminar-asignaciones/', eliminar_asignaciones, name='eliminar_asignaciones'),
    path('generar-reporte/', generar_excel_proyectos, name='generar_reporte'),
    path('generar-reporte2/', generar_excel_asignacion, name='generar_reporte2'),
    path('generar-reporte-recursos/', generar_excel_recursos, name='generar_excel_recursos'),
]
