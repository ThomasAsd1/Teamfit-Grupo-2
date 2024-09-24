from django.shortcuts import redirect, render
from .models import proyectos
from .forms import UploadFileForm
from datetime import datetime, timedelta, time
import random
import requests
import json
import csv
from django.contrib import messages
import pandas as pd
from .models import proyectos,empleado,asignacion
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
            proyecto = proyectos(
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

def asignar_recursos(request):
    if request.method == 'POST':
        # Limpiar asignaciones previas
        asignacion.objects.all().delete()

        # Filtrar proyectos que necesitan asignación
        proyectos_necesitan_asignacion = proyectos.objects.filter(
            ocupacionInicio__lt=80.00,  # Ocupación menor al 80%
            disponibilidad__gt=0        # Debe tener disponibilidad
        )

        # Asignar recursos a proyectos
        for proyecto in proyectos_necesitan_asignacion:
            horas_requeridas = calcular_horas_requeridas(proyecto)
            empleados_disponibles = empleado.objects.filter(estado='Disponible')

            # Asegurar que ambas fechas son del mismo tipo (date)
            fecha_inicio = proyecto.createDate.date() if isinstance(proyecto.createDate, datetime) else proyecto.createDate
            fecha_termino = proyecto.cierre if isinstance(proyecto.cierre, date) else proyecto.cierre.date()

            # Calcular la duración del proyecto en días
            duracion_proyecto = (fecha_termino - fecha_inicio).days

            # Verificar cuántos empleados son necesarios para cubrir las horas requeridas
            empleados_asignados = []
            for emp in empleados_disponibles:
                if horas_requeridas <= 0:
                    break
                
                horas_disponibles = Decimal(emp.disponibilidad)
                horas_diarias = horas_disponibles / duracion_proyecto

                if horas_diarias >= horas_requeridas:
                    horas_a_asignar = horas_requeridas / duracion_proyecto
                else:
                    horas_a_asignar = horas_diarias

                horas_asignadas = horas_a_asignar * duracion_proyecto
                nueva_disponibilidad = horas_disponibles - horas_asignadas
                ocupacion = Decimal(100) * (horas_disponibles - nueva_disponibilidad) / horas_disponibles
                utilizacion = Decimal(100) * horas_asignadas / horas_disponibles

                empleados_asignados.append(emp)

                # Crear la asignación
                with transaction.atomic():
                    asignacion.objects.create(
                        empleado=emp,
                        proyecto=proyecto,
                        horas_asignadas=horas_asignadas,
                        categoria=emp.categoria,
                        estado_empleado='Disponible',
                        disponibilidad_restante=nueva_disponibilidad,
                        ocupacion=ocupacion,
                        disponibilidad=nueva_disponibilidad,
                        utilizacion=utilizacion
                    )

                horas_requeridas -= horas_asignadas

            # Asegurar que al menos 4 empleados sean asignados
            if len(empleados_asignados) < 4:
                print(f"El proyecto {proyecto.proyecto} no tiene suficientes empleados asignados. Asignando más.")
                for _ in range(4 - len(empleados_asignados)):
                    if horas_requeridas <= 0:
                        break
                    # Asignar empleados adicionales aquí si es necesario

            if horas_requeridas > 0:
                print(f"El proyecto {proyecto.proyecto} no pudo ser completamente asignado.")

        mensaje = "Recursos asignados exitosamente."

    else:
        mensaje = ""

    # Filtrar proyectos que necesitan asignación para mostrar
    proyectos_necesitan_asignacion = proyectos.objects.filter(
        ocupacionInicio__lt=80.00,  # Ocupación menor al 80%
        disponibilidad__gt=0        # Debe tener disponibilidad
    )

    # Contexto para renderizar
    context = {
        'proyectos': proyectos_necesitan_asignacion,
        'asignaciones': asignacion.objects.all(),
        'mensaje': mensaje
    }

    return render(request, 'core/proyectos_a_asignar.html', context)

def proyectos_a_asignar(request):
    # Filtrar proyectos que necesitan asignación para mostrar
    proyectos_necesitan_asignacion = proyectos.objects.filter(
        ocupacionInicio__lt=80.00,  # Ocupación menor al 80%
        disponibilidad__gt=0        # Debe tener disponibilidad
    )

    # Contexto para renderizar
    context = {
        'proyectos': proyectos_necesitan_asignacion,
        'asignaciones': asignacion.objects.all()
    }

    return render(request, 'core/proyectos_a_asignar.html', context)

def limpiar_asignaciones(request):
    # Limpiar asignaciones previas
    asignacion.objects.all().delete()
    return redirect('proyectos_a_asignar')

def limpiar_proyectos(request):
    if request.method == 'POST':
        proyectos.objects.all().delete()
        messages.success(request, "Todos los proyectos han sido eliminados exitosamente.")
        return redirect('asignar_recursos')
    
def pruebas(request):
    # Puedes incluir lógica aquí si es necesario
    # Por ahora, esta vista simplemente renderiza la plantilla con el contexto recibido
    return render(request, 'core/pruebas.html')