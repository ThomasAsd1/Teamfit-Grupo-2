from dataclasses import field
from msilib.schema import CheckBox
from pyexpat import model
from django import forms
from django.forms import ModelForm, fields, Form
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from pkg_resources import require
from datetime import date, timedelta
from django.core.exceptions import ValidationError

class UploadFileForm(forms.Form):
    file = forms.FileField( label='Selecciona un archivo CSV o XLSX',
                            help_text=' <br> Solo se permiten archivos CSV y XLSX',
                            widget=forms.ClearableFileInput(attrs={'accept': '.csv, .xlsx', 'class':'btn btn-primary'}))
    class Meta:
        fields = ['file']
