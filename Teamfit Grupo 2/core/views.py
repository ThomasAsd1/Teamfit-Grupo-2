from django.shortcuts import redirect, render
from .forms import UploadFileForm
from datetime import datetime, timedelta, time
import random
import requests
import json
import csv
from django.contrib import messages
import pandas as pd
from .models import Proyecto, Recurso, Disponibilidad, Asignacion, AsignacionControl
# import plotly.express as px
# import plotly.graph_objects as go
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
from django.utils import timezone
import pytz
from django.db.models import Sum, Q, Count
from django.db import transaction
from django.db.models import F
from datetime import datetime,date
from decimal import Decimal
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.http import HttpResponse
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
import logging
from django.db import DatabaseError, OperationalError
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import render_to_string


# Create your views here.

def pagina_principal(request):
    data = {'form':UploadFileForm()}
    return render(request, 'core/index.html', data)

def ver_proyectos(request):
    Proyectos = proyectos.objects.all()
    return render(request, 'core/ver_proyectos.html', {'proyectos': Proyectos})


def subirProyectos(request, upload='Sh'):
    data = {'form': UploadFileForm()}
    showTable = False
    
    if upload == "Can":
        try:
            request.session.pop('df_proyectos')
        except KeyError:
            pass
        return redirect('subirProyectos')
        
    if upload == "Up":
        df = cambiarFormatoAlmacenarDb(request.session.get('df_proyectos', []))
        cont = 0
        
        for _, row in df.iterrows():
            # Obtener el valor de ocupación inicial
            ocupacionInicio = row.get('ocupacionInicio', 0)
            
            # Calcular la disponibilidad en función de la ocupación
            disponibilidad = 100 - ocupacionInicio
            
            # Obtener el valor de utilización, o establecer en 0 si no está presente
            utilizacion = row.get('utilizacion', 0)
            
            # Calcular la ocupación final
            ocupacionFinal = ocupacionInicio + utilizacion
            
            # Validación de los rangos de ocupación
            # if ocupacionFinal < 81 or ocupacionFinal > 95:
            #    data['mesg'] = f"Error: La ocupación final del proyecto '{row.get('proyecto', 'Desconocido')}' está fuera del rango permitido (81% - 95%). Ocupación final: {ocupacionFinal}%."
            #   return render(request, "core/subirProyectos.html", data)
            
            # Guardar el proyecto si pasa las validaciones
            proyecto = proyecto(
                id=row.get('id'),
                proyecto=row.get('proyecto'),
                lineaNegocio=row.get('lineaNegocio'),
                tipo=row.get('tipo'),
                cliente=row.get('cliente'),
                createDate=row.get('createDate'),
                cierre=row.get('cierre'),
                egresosNoHHCLP=row.get('egresosNoHHCLP'),
                montoOfertaCLP=row.get('montoOfertaCLP'),
                usoAgencia=row.get('usoAgencia'),
                ocupacionInicio=ocupacionInicio,
                disponibilidad=disponibilidad,
                utilizacion=utilizacion,
            )
            cont += 1
            proyecto.save()
        
        request.session.pop('df_proyectos', None)
        return redirect('ver_proyectos')
    
    if request.method == 'POST' and 'file' in request.FILES:
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            if not file.name.endswith(('.csv', '.xlsx')):
                data['mesg'] = 'Archivo no compatible. Por favor, selecciona un archivo CSV o XLSX.'
            else:
                df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
                required_columns = ['id', 'Proyecto', 'Línea de Negocio', 'tipo', 'cliente', 'create_date', 
                                    'Cierre', 'Egresos No HH CLP', 'Monto Oferta CLP',
                                    'C/Agencia', 'Ocupación Al Iniciar (%)']
                if not all(col in df.columns for col in required_columns):
                    data['mesg'] = 'El archivo no contiene las columnas requeridas. Por favor, sube un archivo con estas columnas.'
                else:
                    df = cambiarFormatoAlmacenarDf(df)
                    validado = verificarDf(df)
                    df_validado = validado['valido']
                    
                    datosDfDict = df.to_dict(orient='records')
                    data["proyectos"] = datosDfDict
                    data['validado'] = df_validado
                    showTable = True
                    
                    if not df_validado:
                        data['mesg'] = validado['mesg']
                    else:
                        data['mesg'] = validado['mesg']
                        request.session['df_proyectos'] = datosDfDict
        else:
            data["mesg"] = "El valor es inválido"
    data["showTable"] = showTable
        
    return render(request, "core/subirProyectos.html", data)

def cambiarFormatoAlmacenarDf(df):
    df = df
    df['create_date'] = df['create_date'].astype(str)
    df['Cierre'] = df['Cierre'].astype(str)
    df.rename(columns={'Proyecto': 'proyecto'}, inplace=True)
    df.rename(columns={'Línea de Negocio': 'lineaNegocio'}, inplace=True)
    df.rename(columns={'create_date': 'createDate'}, inplace=True)
    df.rename(columns={'Cierre': 'cierre'}, inplace=True)
    df.rename(columns={'Egresos No HH CLP': 'egresosNoHHCLP'}, inplace=True)
    df.rename(columns={'Monto Oferta CLP': 'montoOfertaCLP'}, inplace=True)    
    df.rename(columns={'C/Agencia': 'usoAgencia'}, inplace=True)
    df.rename(columns={'Ocupación Al Iniciar (%)': 'ocupacionInicio'}, inplace=True)
    df['ocupacionInicio'] = df['ocupacionInicio'].round(2)
    df['ocupacionInicio'] = df['ocupacionInicio'] * 100
    return df

def cambiarFormatoAlmacenarDb(df):
    df = pd.DataFrame(df)
    df['createDate'] = pd.to_datetime(df['createDate'])
    df['cierre'] = pd.to_datetime(df['cierre'])
    df['cliente'] = df['cliente'].astype(int)
    df['usoAgencia'] = df['usoAgencia'].fillna(0)
    df['usoAgencia'] = df['usoAgencia'].replace({'Sí': 1, 'no': 0}).astype(bool)
    df['montoOfertaCLP'] = df['montoOfertaCLP'].astype(int)
    df['ocupacionInicio'] = df['ocupacionInicio'].astype(float) 
    return df

def verificarDf(df):
    """Verifica que los valores relevantes no sean nulos.
    
    Parametros de Entrada: 
    df (El dataframe a utilizar)
    
    Return: 
    Diccionario con mesg y valido.

        mesg(string) = Mensaje a mostrar en HTML.
    
        valido(boolean) = Si no contiene datos nulos es verdadero 
    """
    columns_to_check = ['id', 'proyecto', 'lineaNegocio', 'tipo', 'cliente', 'createDate', 'montoOfertaCLP', 'ocupacionInicio']
    if df[columns_to_check].isnull().values.any():
        ids_nulos = df.loc[df[columns_to_check].isnull().any(axis=1), 'id'].tolist()
        ids_nulos = sorted(ids_nulos)
        if(len(ids_nulos) > 5):
            mesg = ("IDs con valores nulos en los siguientes registros: <br> <strong>" + str(ids_nulos[:5]) + "</strong> entre otros. <br>"
                    "Por favor, verifique los registros indicados.")
            validado = {'mesg':mesg,'valido':False}
    else:
        mesg = 'No se han encontrado datos que puedan provocar conflictos'
        validado = {'mesg':mesg, 'valido':True}
    return validado


def subir_empleados(request):
    data = {'form': UploadFileForm()}
    showTable = False
    
    if request.method == 'POST':
        if 'file' in request.FILES:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                if not file.name.endswith(('.csv', '.xlsx')):
                    data['mesg'] = 'Archivo no compatible. Por favor, selecciona un archivo CSV o XLSX.'
                else:
                    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
                    required_columns = ['id_empleado', 'nombre', 'cargo', 'telefono', 'categoria', 'horas_laborales', 'disponibilidad', 'estado']
                    if not all(col in df.columns for col in required_columns):
                        data['mesg'] = 'El archivo no contiene las columnas requeridas. Por favor, sube un archivo con las columnas [id_empleado, nombre, cargo, telefono, categoria, horas_laborales, disponibilidad, estado].'
                    else:
                        for _, row in df.iterrows():
                            empleado.objects.update_or_create(
                                id_empleado=row['id_empleado'],
                                defaults={
                                    'nombre': row['nombre'],
                                    'cargo': row['cargo'],
                                    'telefono': row['telefono'],
                                    'categoria': row['categoria'],
                                    'horas_laborales': row['horas_laborales'],
                                    'disponibilidad': row['disponibilidad'],
                                    'estado': row['estado']
                                }
                            )
                        data['mesg'] = 'Archivo procesado correctamente.'
                        data['showTable'] = True
                        data['empleados'] = empleado.objects.all()
            else:
                data['mesg'] = 'Formulario inválido.'
        else:
            id_empleado = request.POST.get('id_empleado')
            nombre = request.POST.get('nombre')
            cargo = request.POST.get('cargo')
            telefono = request.POST.get('telefono')
            categoria = request.POST.get('categoria')
            horas_laborales = request.POST.get('horas_laborales')
            disponibilidad = request.POST.get('disponibilidad')
            estado = request.POST.get('estado')
            
            empleado.objects.update_or_create(
                id_empleado=id_empleado,
                defaults={
                    'nombre': nombre,
                    'cargo': cargo,
                    'telefono': telefono,
                    'categoria': categoria,
                    'horas_laborales': horas_laborales,
                    'disponibilidad': disponibilidad,
                    'estado': estado
                }
            )
            data['mesg'] = 'Empleado agregado correctamente.'
            data['showTable'] = True
            data['empleados'] = empleado.objects.all()
            
    return render(request, 'core/upload_empleados.html', data)

def ver_proyectos_empleados(request):
    proyectos_activos = proyectos.objects.all()
    empleados_disponibles = empleado.objects.filter(estado='Disponible')

    return render(request, 'ver_proyectos_empleados.html', {
        'proyectos': proyectos_activos,
        'empleados': empleados_disponibles
    })

def calcular_horas_requeridas(proyecto):
    fecha_inicio = proyecto.createDate.date() if isinstance(proyecto.createDate, datetime) else proyecto.createDate
    fecha_cierre = proyecto.cierre if isinstance(proyecto.cierre, date) else proyecto.cierre.date()
    dias = (fecha_cierre - fecha_inicio).days
    return dias * 8  # Asumiendo 8 horas por día de trabajo

# ----------------------------------------------------------------------------------- Asignador HH -------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------- Asignador HH -------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------- Asignador HH -------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------- Asignador HH -------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------- Asignador HH -------------------------------------------------------------------------------------------


# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 
# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 
# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 
# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 

def asignar_recursos():
    """
    Algoritmo que asigna recursos semana a semana según la duración y la semana de inicio de cada proyecto.
    Se asegura de que solo se asigne un jefe de proyecto por proyecto y que si no hay jefe disponible,
    la asignación sea marcada como 'Sin jefe de proyecto asignado' en lugar de 0 horas.
    """
    mensaje = ""
    asignacion_realizada = False  # Para verificar si se realizó alguna asignación

    # Iteramos sobre cada proyecto para asignar recursos según su duración
    proyectos = Proyecto.objects.all().order_by('-tipo_proyecto__prioridad', 'nombre')

    for proyecto in proyectos:
        # Obtener la semana de inicio y la duración del proyecto
        semana_inicio = proyecto.semana_inicio
        duracion_semanas = proyecto.duracion_semanas
        
        print(f"Procesando proyecto '{proyecto.nombre}' con duración de {duracion_semanas} semanas, comenzando en la semana {semana_inicio}...")

        # Iteramos sobre las semanas que abarca el proyecto
        for i in range(duracion_semanas):
            # Calcular la semana de asignación considerando el ciclo de 52 semanas
            semana_asignacion = (semana_inicio + i - 1) % 52 + 1  # Reiniciar el conteo al llegar a la semana 53
            print(f"Asignando en la semana {semana_asignacion}...")

            # Obtener los recursos disponibles para el rol requerido
            rol_requerido = proyecto.rol_requerido
            recursos_disponibles = Recurso.objects.filter(rol=rol_requerido).order_by('-prioridad', 'nombre')

            if not recursos_disponibles.exists():
                print(f"No hay recursos disponibles para el rol '{rol_requerido}' del proyecto '{proyecto.nombre}' en la semana {semana_asignacion}.")
                continue

            horas_demandadas = proyecto.horas_demandadas
            
            for recurso in recursos_disponibles:
                # Recuperar la disponibilidad del recurso para la semana en curso
                disponibilidad = Disponibilidad.objects.filter(recurso=recurso, semana=semana_asignacion).first()

                if not disponibilidad or disponibilidad.horas_disponibles <= 0:
                    print(f"Recurso '{recurso.nombre}' no tiene horas disponibles en la semana {semana_asignacion}.")
                    continue

                # Verificar si el proyecto ya ha terminado
                if i >= duracion_semanas:
                    break

                # Comprobamos si ya hay una asignación existente
                asignacion_existente = Asignacion.objects.filter(proyecto=proyecto, recurso=recurso, semana=semana_asignacion).first()

                if asignacion_existente:
                    print(f"Asignación previa ya detectada para el recurso '{recurso.nombre}' en el proyecto '{proyecto.nombre}' en la semana {semana_asignacion}.")
                    continue

                # Asignar tantas horas como estén disponibles
                horas_a_asignar = min(horas_demandadas, disponibilidad.horas_disponibles)
                print(f"Asignando {horas_a_asignar} horas del recurso '{recurso.nombre}' al proyecto '{proyecto.nombre}' en la semana {semana_asignacion}.")

                # Realizar la asignación
                Asignacion.objects.create(
                    proyecto=proyecto,
                    recurso=recurso,
                    semana=semana_asignacion,
                    horas_asignadas=horas_a_asignar
                )

                # Actualizar la disponibilidad del recurso
                disponibilidad.horas_disponibles -= horas_a_asignar
                disponibilidad.save()

                # Reducir la demanda del proyecto
                horas_demandadas -= horas_a_asignar
                asignacion_realizada = True  # Marcamos que se ha realizado una asignación

                # Si se asignaron todas las horas demandadas, salir del bucle
                if horas_demandadas <= 0:
                    print(f"Se completaron todas las horas demandadas para el proyecto '{proyecto.nombre}' en la semana {semana_asignacion}.")
                    break

            # Si quedan horas no asignadas, las guardamos para la siguiente semana
            if horas_demandadas > 0:
                print(f"Quedan {horas_demandadas} horas no asignadas para el proyecto '{proyecto.nombre}' después de la semana {semana_asignacion}.")
                proyecto.horas_demandadas = horas_demandadas
                proyecto.save()

    # Mensaje final de depuración
    if asignacion_realizada:
        return "Asignación de recursos realizada con éxito."
    else:
        return "No se pudo realizar la asignación. Verifique la disponibilidad de recursos y la demanda de horas."


# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 
# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 
# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 
# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 

#ESTA FUNCIÓN TE GENERA LOS DATOS DE LAS TABLAS EN EXEL Y PDF

#Esta es la función que genera el exel de la tabla horas_por_recurso_data
def generar_excel_proyectos(request):
    # Obtener los datos de la tabla horas por recurso
    proyectos = Asignacion.objects.values(
        'recurso__nombre',  # Nombre del recurso
        'recurso__rol',     # Rol del recurso
        'semana',           # Semana
    ).annotate(
        total_horas_rol=Sum('horas_asignadas')  # Total de horas asignadas
    )

    # Crear un DataFrame a partir de los datos de los proyectos
    df = pd.DataFrame(list(proyectos))

    # Crear un nuevo DataFrame pivotado
    df_pivot = df.pivot_table(
        index=['recurso__nombre', 'recurso__rol'],  # Agrupar por nombre y rol del recurso
        columns='semana',                           # Semanas se convierten en columnas
        values='total_horas_rol',                   # Valores que se colocan en la tabla
        fill_value=0                                # Rellenar con 0 donde no hay horas asignadas
    ).reset_index()

    # Renombrar las columnas para incluir "Semana"
    df_pivot.columns.name = None  # Eliminar el nombre de la columna
    df_pivot.columns = [f'Semana {col}' if isinstance(col, int) else str(col) for col in df_pivot.columns]

    # Calcular el total de horas por recurso y añadirlo como una nueva fila por rol
    total_row = df_pivot.iloc[:, 2:].sum().to_frame().T  # Sumar las horas, omitiendo las dos primeras columnas (nombre y rol)
    total_row['recurso__nombre'] = 'Total'  # Asignar el nombre de la fila total
    total_row['recurso__rol'] = ''  # Dejar vacío el campo de rol en la fila total
    df_pivot = pd.concat([df_pivot, total_row], ignore_index=True)

    output = BytesIO()

    # Crear el archivo Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_pivot.to_excel(writer, index=False, sheet_name='Horas por Recurso y Semana')

    # Posicionar el buffer al inicio para leer los datos
    output.seek(0)

    # Preparar la respuesta de Excel
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reporte_horas_por_recurso.xlsx"'
    return response

#Función que genera el exel de la segunda tabla
def generar_excel_recursos(request):
    # Obtener los datos de asignaciones de la tabla actualizada
    asignaciones = Asignacion.objects.values(
        'proyecto__nombre',  # Nombre del proyecto
        'semana',            # Semana
    ).annotate(
        total_horas_proyecto=Sum('horas_asignadas')  # Total de horas asignadas por proyecto
    )

    # Crear un DataFrame a partir de los datos de las asignaciones
    df = pd.DataFrame(list(asignaciones))

    # Crear un nuevo DataFrame pivotado
    df_pivot = df.pivot_table(
        index='proyecto__nombre',  # Agrupar por nombre del proyecto
        columns='semana',          # Semanas se convierten en columnas
        values='total_horas_proyecto',  # Valores que se colocan en la tabla
        fill_value=0               # Rellenar con 0 donde no hay horas asignadas
    ).reset_index()

    # Renombrar las columnas para incluir "Semana"
    df_pivot.columns.name = None  # Eliminar el nombre de la columna
    df_pivot.columns = [f'Semana {col}' if isinstance(col, int) else str(col) for col in df_pivot.columns]

    # Calcular el total de horas por proyecto y añadirlo como una nueva fila
    total_row = df_pivot.iloc[:, 1:].sum().to_frame().T  # Sumar las horas, omitiendo la primera columna que es el proyecto
    total_row['proyecto__nombre'] = 'Total'  # Asignar el nombre de la fila total
    df_pivot = pd.concat([df_pivot, total_row], ignore_index=True)

    output = BytesIO()

    # Crear el archivo Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_pivot.to_excel(writer, index=False, sheet_name='Horas por Proyecto y Semana')

    # Posicionar el buffer al inicio para leer los datos
    output.seek(0)

    # Preparar la respuesta de Excel
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reporte_horas_por_proyecto.xlsx"'
    return response
    
from io import BytesIO
from django.http import HttpResponse
import pandas as pd
from .models import Asignacion  # Asegúrate de que este sea el nombre correcto de tu modelo

#Esta es la función que genera el exel de la tabla asignaciones
def generar_excel_asignacion(request):
    # Obtener el formato seleccionado desde el request
    formato = request.GET.get('formato')

    # Obtener los datos de las asignaciones
    asignaciones = Asignacion.objects.all().values(
        'proyecto__nombre',  # Accediendo al nombre del proyecto
        'recurso__nombre',   # Accediendo al nombre del recurso
        'recurso__rol',      # Accediendo al rol del recurso
        'semana',
        'año',
        'horas_asignadas'
    )

    # Generar Excel
    if formato == 'excel':
        # Crear un DataFrame a partir de los datos de las asignaciones
        df = pd.DataFrame(list(asignaciones))

        # Crear un nuevo DataFrame pivotado
        df_pivot = df.pivot_table(
            index=['proyecto__nombre', 'recurso__nombre', 'recurso__rol'],  # Mantener estas columnas como índices
            columns=['semana'],  # Las semanas se convierten en columnas
            values='horas_asignadas',  # Valores que se colocan en la tabla
            fill_value=0  # Rellenar con 0 donde no hay horas asignadas
        ).reset_index()

        # Renombrar las columnas para mayor claridad
        df_pivot.columns.name = None  # Eliminar el nombre de la columna
        df_pivot.columns = [f'Semana {col}' if col not in ['proyecto__nombre', 'recurso__nombre', 'recurso__rol'] else col for col in df_pivot.columns]

        # Calcular el total de horas por semana
        total_horas = df_pivot.loc[:, df_pivot.columns.str.startswith('Semana ')]
        total_horas_sum = total_horas.sum().to_frame().T  # Transponer para que sea una fila
        total_horas_sum['proyecto__nombre'] = ''
        total_horas_sum['recurso__nombre'] = ''
        total_horas_sum['recurso__rol'] = 'Total Horas'  # Etiqueta para la fila de totales

        # Concatenar los datos pivotados con los totales
        df_final = pd.concat([df_pivot, total_horas_sum], ignore_index=True)

        output = BytesIO()

        # Crear el archivo Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Asignaciones')

        # Posicionar el buffer al inicio para leer los datos
        output.seek(0)

        # Preparar la respuesta de Excel
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="reporte_asignaciones.xlsx"'
        return response

    # Si no se selecciona un formato válido
    else:
        return HttpResponse('Formato no soportado', status=400)

#ESTA ES LA FUNCIÓN DE BUSQUEDA SI TIENE QUE MIDIFICAR ALGO PARA BUSCAR QUE SEA AQUI NO TOQUEN LO DEMAS
def busqueda_de_datos(queryset, search_value, search_fields):
    """
    Función que realiza la búsqueda de datos en los campos especificados.
    
    Args:
        queryset: El conjunto de datos que se va a filtrar.
        search_value: El valor de búsqueda que el usuario ha ingresado.
        search_fields: Una lista de campos donde se debe buscar el valor.

    Returns:
        Un queryset filtrado por el valor de búsqueda.
    """
    if search_value:
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": search_value})
        queryset = queryset.filter(query)
    
    return queryset

# PRIMERA TABLA
def horas_por_recurso_data(request):
    order_column = request.GET.get('order[0][column]', 0)
    order_dir = request.GET.get('order[0][dir]', 'asc')

    # Definición de las columnas para ordenar
    columns = ['recurso__nombre','recurso__rol', 'semana', 'total_horas_rol']
    order_field = columns[int(order_column)]

    # Búsqueda por valor
    search_value = request.GET.get('search[value]', '')

    # Agrupar por semana y rol requerido
    proyectos = Asignacion.objects.values(
        'recurso__nombre',
        'recurso__rol',
        'semana',
    ).annotate(
        total_horas_rol=Sum('horas_asignadas'),
        
    ).filter(
        Q(recurso__rol__icontains=search_value) |
        Q(semana__icontains=search_value)
    ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

    # Paginar los resultados
    paginator = Paginator(proyectos, request.GET.get('length', 10))
    page_number = int(request.GET.get('start', 0)) // paginator.per_page + 1
    page_obj = paginator.get_page(page_number)

    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(page_obj)
    }

    return JsonResponse(data)


# Recursos agrupados por proyecto (SEGUNDA TABLA)
def horas_por_proyecto_data(request):
    order_column = request.GET.get('order[0][column]', 0)
    order_dir = request.GET.get('order[0][dir]', 'asc')

    # Definición de las columnas para ordenar
    columns = ['proyecto__nombre', 'semana', 'total_horas_proyecto']
    order_field = columns[int(order_column)]

    search_value = request.GET.get('search[value]', '')

    # Agrupar por semana y nombre del proyecto
    asignaciones = Asignacion.objects.values(
        'proyecto__nombre',
        'semana'
    ).annotate(
        total_horas_proyecto=Sum('horas_asignadas')
    ).filter(
        Q(proyecto__nombre__icontains=search_value) |
        Q(semana__icontains=search_value)
    ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

    # Paginación de resultados
    paginator = Paginator(asignaciones, request.GET.get('length', 10))
    page_number = int(request.GET.get('start', 0)) // paginator.per_page + 1
    page_obj = paginator.get_page(page_number)

    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(page_obj)
    }

    return JsonResponse(data)


# # Proyectos (PRIMERA TABLA)
# def proyectos_data(request):
#     # Definir el orden por defecto
#     order_column = request.GET.get('order[0][column]', 0)
#     order_dir = request.GET.get('order[0][dir]', 'asc')

#     columns = ['nombre', 'duracion_semanas', 'horas_demandadas', 'tipo_proyecto__prioridad', 'rol_requerido']
#     order_field = columns[int(order_column)]

#     search_value = request.GET.get('search[value]', '')

#     proyectos = Proyecto.objects.filter(
#         Q(nombre__icontains=search_value) |
#         Q(duracion_semanas__icontains=search_value) |
#         Q(horas_demandadas__icontains=search_value) |
#         Q(tipo_proyecto__prioridad__icontains=search_value) |
#         Q(rol_requerido__icontains=search_value)
#     ).values(
#         'nombre', 'duracion_semanas', 'horas_demandadas', 'tipo_proyecto__prioridad', 'rol_requerido'
#     ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

#     # Si se solicita un formato de salida (solo Excel)
#     if 'formato' in request.GET and request.GET.get('formato') == 'excel':
#         return generar_excel(request, proyectos)  # Pasar los datos de 'proyectos'

#     paginator = Paginator(proyectos, request.GET.get('length', 10))
#     page_number = request.GET.get('start', 1)
#     page_obj = paginator.get_page(int(page_number) // paginator.per_page + 1)

#     data = {
#         'draw': int(request.GET.get('draw', 1)),
#         'recordsTotal': paginator.count,
#         'recordsFiltered': paginator.count,
#         'data': list(page_obj)
#     }

#     return JsonResponse(data)


# # Recursos (SEGUNDA TABLA)
# def recursos_asignados_data(request):
#     # Definir el orden por defecto
#     order_column = request.GET.get('order[0][column]', 0)
#     order_dir = request.GET.get('order[0][dir]', 'asc')

#     columns = ['proyecto__nombre', 'semana', 'total_horas_semanales']
#     order_field = columns[int(order_column)]

#     search_value = request.GET.get('search[value]', '')

#     asignaciones = Asignacion.objects.values(
#         'proyecto__nombre',
#         'semana'
#     ).annotate(
#         total_horas_semanales=Sum('horas_asignadas')
#     ).filter(
#         Q(proyecto__nombre__icontains=search_value) |
#         Q(semana__icontains=search_value)
#     ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

#     # Si se solicita un formato de salida (solo Excel)
#     if 'formato' in request.GET and request.GET.get('formato') == 'excel':
#         return generar_excel(request, asignaciones)

#     paginator = Paginator(asignaciones, request.GET.get('length', 10))
#     page_number = int(request.GET.get('start', 0)) // paginator.per_page + 1
#     page_obj = paginator.get_page(page_number)

#     data = {
#         'draw': int(request.GET.get('draw', 1)),
#         'recordsTotal': paginator.count,
#         'recordsFiltered': paginator.count,
#         'data': list(page_obj)
#     }

#     return JsonResponse(data)

# (TERCERA TABLA)
# Vista para mostrar horas agrupadas por rol y semana
# Vista para mostrar horas agrupadas por rol y semana


# TERCERA TABLA
def asignaciones_data(request):
    order_column = request.GET.get('order[0][column]', 0)
    order_dir = request.GET.get('order[0][dir]', 'asc')

    # Definir las columnas para ordenar
    columns = ['recurso__rol', 'semana', 'total_horas']
    order_field = columns[int(order_column)]

    # Obtener el valor de búsqueda del DataTable
    search_value = request.GET.get('search[value]', '')

    # Agrupar las horas asignadas por rol y semana
    asignaciones_agrupadas = Asignacion.objects.values(
        'recurso__rol',  # Agrupar por rol
        'semana'         # Agrupar por semana
    ).annotate(
        total_horas=Sum('horas_asignadas')  # Sumar todas las horas asignadas en cada semana para el rol
    ).filter(
        Q(recurso__rol__icontains=search_value) |
        Q(semana__icontains=search_value)
    ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

    # Paginación de los resultados
    paginator = Paginator(asignaciones_agrupadas, request.GET.get('length', 10))
    page_number = int(request.GET.get('start', 0)) // paginator.per_page + 1
    page_obj = paginator.get_page(page_number)

    # Preparar el resultado para DataTables
    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(page_obj)
    }

    return JsonResponse(data)

def asignaciones_list(request):
    """
    Vista que muestra la lista de asignaciones en una tabla paginada.
    """

    # Obtener todas las asignaciones
    asignaciones = Asignacion.objects.all().order_by('semana')

    # Configurar el paginador para mostrar 10 asignaciones por página
    paginator = Paginator(asignaciones, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Calcular el rango de páginas para mostrar en la interfaz
    num_pages = paginator.num_pages
    current_page = page_obj.number
    start_page = max(current_page - 5, 1)
    end_page = min(current_page + 5, num_pages)

    # Crear una lista de páginas visibles
    page_range = list(range(start_page, end_page + 1))

    # Renderizar el template con las asignaciones paginadas
    return render(request, 'core/asignaciones_list.html', {
        'asignaciones': page_obj,
        'num_pages': num_pages,
        'current_page': current_page,
        'page_range': page_range,
    })



# Configuración de logging
logger = logging.getLogger(__name__)

def ejecutar_asignacion(request):
    if request.method == 'POST':
        try:
            control, created = AsignacionControl.objects.get_or_create(id=1)  # Usa un único registro para controlar
            mensaje = ""

            if not created:
                # Si ya existe un registro, verifica si se realizó una ejecución hoy
                if control.fecha_ultimo_ejecucion == datetime.today():
                    logger.warning("Intento de ejecutar la asignación más de una vez en el mismo día.")
                    return HttpResponse("La asignación ya ha sido ejecutada hoy.", status=400)

            # Ejecutar la asignación de recursos y capturar el mensaje de retorno
            mensaje_asignacion = asignar_recursos()

            # Si la asignación fue exitosa o parcial, actualiza el registro de control
            if "éxito" in mensaje_asignacion or "ya existen" in mensaje_asignacion:
                control.ejecuciones_exitosas += 1
                control.fecha_ultimo_ejecucion = datetime.today()
                control.save()

            mensaje = mensaje_asignacion

        except IntegrityError as e:
            # Manejar errores de integridad (claves duplicadas, etc.)
            control.ejecuciones_fallidas += 1
            control.save()
            logger.error(f"Error de integridad en la asignación: {e}")
            mensaje = f"Error de integridad: {str(e)}"
            return HttpResponse(mensaje, status=500)

        except OperationalError as e:
            # Manejar errores operacionales, como problemas de conexión a la base de datos
            control.ejecuciones_fallidas += 1
            control.save()
            logger.critical(f"Error operacional durante la asignación: {e}")
            mensaje = f"Error operacional: {str(e)}"
            return HttpResponse(mensaje, status=500)

        except DatabaseError as e:
            # Manejar cualquier otro error relacionado con la base de datos
            control.ejecuciones_fallidas += 1
            control.save()
            logger.error(f"Error de base de datos: {e}")
            mensaje = f"Error de base de datos: {str(e)}"
            return HttpResponse(mensaje, status=500)

        except Exception as e:
            # Manejar cualquier otra excepción inesperada
            control.ejecuciones_fallidas += 1
            control.save()
            logger.exception(f"Error inesperado en la asignación: {e}")
            mensaje = f"Error inesperado: {str(e)}"
            return HttpResponse(mensaje, status=500)

        # Asegúrate de devolver una respuesta con el mensaje adecuado
        return HttpResponse(mensaje, status=200)

    return HttpResponse(status=405)  # Método no permitido

def eliminar_asignaciones(request):
    """
    Vista para eliminar todas las asignaciones actuales.
    """
    if request.method == 'POST':
        # Eliminar todas las asignaciones
        Asignacion.objects.all().delete()

        # Redirigir o devolver una respuesta de éxito
        return redirect('asignaciones_list')  # Redirige a la página de asignaciones

    return HttpResponse(status=405)  # Devuelve un error si no es un POST




# def proyectos_a_asignar(request):
#     # Filtrar proyectos que necesitan asignación para mostrar
#     proyectos_necesitan_asignacion = proyectos.objects.filter(
#         ocupacionInicio__lt=80.00,  # Ocupación menor al 80%
#         disponibilidad__gt=0        # Debe tener disponibilidad
#     )

#     # Contexto para renderizar
#     context = {
#         'proyectos': proyectos_necesitan_asignacion,
#         'asignaciones': asignacion.objects.all()
#     }

#     return render(request, 'core/proyectos_a_asignar.html', context)

# def limpiar_asignaciones(request):
#     # Limpiar asignaciones previas
#     asignacion.objects.all().delete()
#     return redirect('proyectos_a_asignar')

# def limpiar_proyectos(request):
#     if request.method == 'POST':
#         proyectos.objects.all().delete()
#         messages.success(request, "Todos los proyectos han sido eliminados exitosamente.")
#         return redirect('asignar_recursos')
    
# def pruebas(request):
#     # Puedes incluir lógica aquí si es necesario
#     # Por ahora, esta vista simplemente renderiza la plantilla con el contexto recibido
#     return render(request, 'core/pruebas.html')