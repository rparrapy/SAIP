# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de listado de archivos de un ítem borrado o de
una versión anterior.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, Archivo, Item, Fase, TipoItem, Relacion
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from saip.lib.auth import TienePermiso
from tg import request, flash, response
from tg.controllers import CUSTOM_CONTENT_TYPE 
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func, desc, or_
from tw.forms.fields import FileField
from saip.lib.func import *
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class ArchivoTable(TableBase):
    __model__ = Archivo
    __omit_fields__ = ['contenido', 'items', '__actions__']
archivo_table = ArchivoTable(DBSession)

class ArchivoTableFiller(TableFiller):
    """ Clase que se utiliza para llenar las tablas de listado de archivos de
        ítems borrados o de versiones anteriores.
    """
    __model__ = Archivo
    __omit_fields__ = ['contenido']
    buscado = ""
    id_item = ""
    version = ""
    
    def init(self,buscado, id_item, version):
        self.buscado = buscado
        self.id_item = id_item
        self.version = version

    def _do_get_provider_count_and_objs(self, buscado="", id_item = "", \
                                        version = "", **kw):
        """ Se utiliza para listar los archivos de ítems borrados o de
            versiones anteriores que cumplan ciertas condiciones y
            ciertos permisos.
        """
        archivos = DBSession.query(Archivo).filter(or_(Archivo.id.contains( \
                self.buscado), Archivo.nombre.contains(self.buscado))).all()
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
               .filter(Item.version == self.version).one()
        print item
        for archivo in reversed(archivos):
            if item not in archivo.items: archivos.remove(archivo)
        return len(archivos), archivos 

archivo_table_filler = ArchivoTableFiller(DBSession)

class AddArchivo(AddRecordForm):
    __model__ = Archivo
    __omit_fields__ = ['id', 'items', 'nombre']
    contenido = FileField('archivo')
add_archivo_form = AddArchivo(DBSession)


class ArchivoControllerListado(CrudRestController):
    """ Controlador del modelo Archivo para ítems borrados o de versiones
        anteriores.
    """
    model = Archivo
    table = archivo_table
    table_filler = archivo_table_filler  
    new_form = add_archivo_form

    def _before(self, *args, **kw):
        self.id_item = unicode("-".join(request.url.split("/")[-3] \
                .split("-")[0:-1]))
        self.version_item = unicode(request.url.split("/")[-3].split("-")[-1])
        super(ArchivoControllerListado, self)._before(*args, **kw)
    
    def get_one(self, archivo_id):
        tmpl_context.widget = archivo_table
        archivo = DBSession.query(Archivo).get(archivo_id)
        value = archivo_table_filler.get_value(archivo = archivo)
        return dict(archivo = archivo, value = value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all_comun")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):
        """Lista los archivos de acuerdo a lo establecido en
           L{archivo_controller_listado.ArchivoTableFiller._do_get_provider_count_and_objs}.
        """
        archivo_table_filler.init("", self.id_item, self.version_item)
        d = super(ArchivoControllerListado, self).get_all(*args, **kw)
        d["accion"] = "./buscar"
        d["model"] = "Archivos"
        item = DBSession.query(Item).filter(Item.id == self.id_item)\
            .filter(Item.version == self.version_item).one()       
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True
        d["direccion_anterior"] = "../.."                  
        return d



    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        """ Lista los archivos de acuerdo a un criterio de búsqueda introducido
            por el usuario.
        """
        buscar_table_filler = ArchivoTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_item, \
                                    self.version_item)
        else:
            buscar_table_filler.init("", self.id_item, self.version_item)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Archivos", accion = "./buscar")
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
                .filter(Item.version == self.version_item).one()      
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True 
        d["direccion_anterior"] = "../.."
        return d

