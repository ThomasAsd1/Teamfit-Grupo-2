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
from django.db.models import Sum
from django.db import transaction
from django.db.models import F
from datetime import datetime,date
from decimal import Decimal
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.http import HttpResponse
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist


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

def asignar_recursos():
    """
    Algoritmo que asigna recursos semana a semana.
    Ordena los proyectos y recursos según sus prioridades y distribuye las horas.
    """
    mensaje = ""
    asignacion_realizada = False

    # Iteramos sobre las semanas, de la 1 a la 52
    for semana in range(1, 53):
        proyectos = Proyecto.objects.filter(semana_inicio__lte=semana).order_by('-tipo_proyecto__prioridad', 'nombre')

        for proyecto in proyectos:
            if semana > proyecto.semana_inicio + proyecto.duracion_semanas - 1:
                continue  # Saltar si la semana actual está fuera del rango del proyecto

            # Verificar si el rol requerido está disponible
            recursos_disponibles = Recurso.objects.filter(rol=proyecto.rol_requerido).order_by('-prioridad', 'nombre')
            if not recursos_disponibles.exists():
                print(f"No hay recursos disponibles para el rol requerido '{proyecto.rol_requerido}' del proyecto '{proyecto.nombre}'.")
                continue

            horas_demandadas = proyecto.horas_demandadas

            for recurso in recursos_disponibles:
                disponibilidades = Disponibilidad.objects.filter(recurso=recurso, semana=semana)

                if not disponibilidades.exists():
                    print(f"No hay disponibilidad registrada para el recurso '{recurso.nombre}' en la semana {semana}.")
                    continue

                for disponibilidad in disponibilidades:
                    asignacion_existente = Asignacion.objects.filter(proyecto=proyecto, recurso=recurso, semana=semana).first()

                    if asignacion_existente:
                        print(f"Asignación ya existente para el proyecto '{proyecto.nombre}' con el recurso '{recurso.nombre}' en la semana {semana}.")
                        return "No se puede realizar la asignación, ya existe una asignación previa."

                    if disponibilidad.horas_disponibles >= horas_demandadas:
                        # Asignar las horas demandadas
                        Asignacion.objects.create(
                            proyecto=proyecto,
                            recurso=recurso,
                            semana=semana,
                            horas_asignadas=horas_demandadas
                        )
                        disponibilidad.horas_disponibles -= horas_demandadas
                        disponibilidad.save()
                        horas_demandadas = 0
                        asignacion_realizada = True
                        break
                    else:
                        # Asignar las horas disponibles y continuar con la siguiente disponibilidad
                        Asignacion.objects.create(
                            proyecto=proyecto,
                            recurso=recurso,
                            semana=semana,
                            horas_asignadas=disponibilidad.horas_disponibles
                        )
                        horas_demandadas -= disponibilidad.horas_disponibles
                        disponibilidad.horas_disponibles = 0
                        disponibilidad.save()

            if horas_demandadas > 0:
                proyecto.horas_demandadas = horas_demandadas
                proyecto.save()

        if semana == 52:
            for proyecto in proyectos:
                if proyecto.horas_demandadas > 0:
                    print(f'Proyecto {proyecto.nombre} tiene {proyecto.horas_demandadas} horas pendientes después de la semana 52.')

    if asignacion_realizada:
        return "Asignación de recursos realizada con éxito."
    else:
        return "No se pudo realizar la asignación."


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


def asignaciones_data(request):
    # Definir el orden por defecto
    order_column = request.GET.get('order[0][column]', 0)  # Obtiene el índice de la columna a ordenar
    order_dir = request.GET.get('order[0][dir]', 'asc')  # Obtiene el orden (ascendente o descendente)
    
    # Mapear el índice de la columna a los nombres de los campos del modelo
    columns = [
        'proyecto__nombre',
        'recurso__nombre',
        'semana',
        'horas_asignadas'
    ]
    
    # Obtener el campo por el que ordenar
    order_field = columns[int(order_column)]
    
    # Realizar la consulta con ordenación
    asignaciones = Asignacion.objects.all().select_related('proyecto', 'recurso').values(
        'proyecto__nombre', 'recurso__nombre', 'semana', 'horas_asignadas'
    ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

    # Configurar la paginación
    paginator = Paginator(asignaciones, request.GET.get('length', 10))
    page_number = int(request.GET.get('start', 0)) // paginator.per_page + 1
    page_obj = paginator.get_page(page_number)

    # Preparar la respuesta JSON
    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(page_obj)
    }

    return JsonResponse(data)

# Proyectos
def proyectos_data(request):
    proyectos = Proyecto.objects.all().values(
        'nombre', 'duracion_semanas', 'horas_demandadas', 'tipo_proyecto__prioridad', 'rol_requerido'
    )
    paginator = Paginator(proyectos, request.GET.get('length', 10))
    page_number = request.GET.get('start', 1)
    page_obj = paginator.get_page(int(page_number) // paginator.per_page + 1)
    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(page_obj)
    }
    return JsonResponse(data)

# Recursos
def recursos_asignados_data(request):
    # Realizamos una agregación de las horas asignadas por proyecto y semana
    asignaciones = Asignacion.objects.values(
        'proyecto__nombre',  # Nombre del proyecto
        'semana',  # Número de la semana
    ).annotate(
        total_horas_semanales=Sum('horas_asignadas')  # Suma de las horas asignadas por semana
    )

    # Implementamos paginación de resultados
    paginator = Paginator(asignaciones, request.GET.get('length', 10))
    page_number = int(request.GET.get('start', 0)) // paginator.per_page + 1
    page_obj = paginator.get_page(page_number)

    # Estructura de datos para enviar a DataTables
    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(page_obj)
    }

    return JsonResponse(data)

def ejecutar_asignacion(request):
    if request.method == 'POST':
        control, created = AsignacionControl.objects.get_or_create(id=1)  # Usa un único registro para controlar
        mensaje = ""

        if not created:
            # Si ya existe un registro, verifica si se realizó una ejecución hoy
            if control.fecha_ultimo_ejecucion == datetime.today():
                return HttpResponse("La asignación ya ha sido ejecutada hoy.", status=400)

        try:
            # Ejecutar la asignación de recursos
            asignar_recursos()

            # Actualizar el registro de control
            control.ejecuciones_exitosas += 1
            control.save()
            mensaje = "Asignación de recursos ejecutada con éxito."

        except IntegrityError as e:
            # Manejar errores de integridad, como claves duplicadas
            control.ejecuciones_fallidas += 1
            control.save()
            mensaje = f"Error al ejecutar la asignación: {str(e)}"
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