# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de listado de ítems pertenecientes a una
línea base

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from sprox.tablebase import TableBase
from saip.model import DBSession, Item, TipoItem, Caracteristica, Relacion
from saip.model import Revision
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect, validate
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from tg import request, flash
from saip.controllers.fase_controller import FaseController
from saip.controllers.relacion_controller import RelacionController
from saip.controllers.archivo_controller import ArchivoController
from saip.controllers.borrado_controller import BorradoController
from saip.controllers.version_controller import VersionController
from saip.controllers.revision_controller import RevisionController
from sqlalchemy import func, desc, or_
from tw.forms.fields import SingleSelectField, MultipleSelectField
from copy import *
import json
import os
import pydot
from saip.lib.func import *
from formencode.validators import NotEmpty

errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class ItemTable(TableBase):
    __model__ = Item
    __omit_fields__ = ['id', 'id_tipo_item', 'id_fase', 'id_linea_base', \
                      'archivos', 'borrado', 'relaciones_a', 'relaciones_b', \
                      'anexo', 'linea_base', 'revisiones', "__actions__"]
item_table = ItemTable(DBSession)

class ItemTableFiller(TableFiller):
    """ Clase que se utiliza para llenar las tablas de ítems pertenecientes
        a una línea base.
    """
    __model__ = Item
    buscado = ""
    id_fase = ""

    def tipo_item(self, obj):
        return obj.tipo_item.nombre

    def __actions__(self, obj):
        """ Define las acciones posibles para cada ítem (ver características).
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        pklist = pklist.split('/')
        id_item = pklist[0]
        version_item = pklist[1]
        pklist = '-'.join(pklist)
        item = DBSession.query(Item).filter(Item.id == id_item) \
                .filter(Item.version == version_item).one()
        value = '<div>'
        if item.anexo != "{}":
            value = value + '<div><a class="caracteristica_link" href=' \
                '"listar_caracteristicas?pk_item='+pklist+ \
                '" style="text-decoration:none" TITLE =' \
                ' "Ver caracteristicas"></a></div>'

        value = value + '</div>'
        return value
    
    def init(self, buscado, id_fase):
        self.buscado = buscado
        self.id_fase = id_fase

    def _do_get_provider_count_and_objs(self, **kw):
        """ Se utiliza para listar los ítems que cumplan ciertas condiciones y
            ciertos permisos.
        """
        id_linea_base = unicode(request.url.split("/")[-3])
        items = DBSession.query(Item)\
            .filter(Item.id_tipo_item.contains(self.id_fase)) \
            .filter(Item.borrado == False).filter(Item.id_linea_base  == \
            id_linea_base).order_by(Item.id).all()
        for item in reversed(items):
            buscado = self.buscado in item.id or \
                      self.buscado in item.nombre or \
                      self.buscado in str(item.version) or \
                      self.buscado in item.descripcion or \
                      self.buscado in item.estado or \
                      self.buscado in item.observaciones or \
                      self.buscado in str(item.complejidad) or \
                      self.buscado in str(item.prioridad) or \
                      self.buscado in item.tipo_item.nombre
            if item.linea_base:
                buscado = buscado or self.buscado in item.linea_base.id

            if not buscado: items.remove(item)
        aux = []
        for item in items:
            for item_2 in items:
                if item.id == item_2.id : 
                    if item.version > item_2.version: 
                        aux.append(item_2)
                    elif item.version < item_2.version :
                        aux.append(item)
        items = [i for i in items if i not in aux]
        return len(items), items 
item_table_filler = ItemTableFiller(DBSession)

class AddItem(AddRecordForm):
    __model__ = Item
    __omit_fields__ = ['id', 'codigo',  'archivos', 'fichas', 'revisiones', \
                    'id_tipo_item, id_linea_base', 'tipo_item', 'linea_base', \
                    'relaciones_a', 'relaciones_b']
    complejidad = SingleSelectField('complejidad', options = range(11)[1:])
    prioridad = SingleSelectField('prioridad', options = range(11)[1:])
add_item_form = AddItem(DBSession)

class EditItem(EditableForm):
    __model__ = Item
    __omit_fields__ = ['id', 'codigo', 'archivos', 'fichas', 'revisiones', \
                    'id_tipo_item, id_linea_base', 'tipo_item', 'linea_base', \
                    'relaciones_a', 'relaciones_b']
edit_item_form = EditItem(DBSession)

class ItemEditFiller(EditFormFiller):
    __model__ = Item
item_edit_filler = ItemEditFiller(DBSession)

class ItemControllerListado(CrudRestController):
    """ Controlador de ítem para el listado de los pertenecientes a una
        línea base.
    """
    model = Item
    table = item_table
    table_filler = item_table_filler  
    edit_filler = item_edit_filler
    edit_form = edit_item_form
    new_form = add_item_form

    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-5])
        super(ItemControllerListado, self)._before(*args, **kw)
    
    @with_trailing_slash
    @expose("saip.templates.get_all_item")
    @expose('json')
    @paginate('value_list', items_per_page=3)
    def get_all(self, *args, **kw):
        """ Lista los ítems de acuerdo a lo establecido en
            L{ItemTableFiller._do_get_provider_count_and_objs}.
        """
        item_table_filler.init("", self.id_fase)
        d = super(ItemControllerListado, self).get_all(*args, **kw)
        items_borrados = DBSession.query(Item).filter(Item.id.contains( \
                        self.id_fase)).filter(Item.borrado == True).count()
        d["permiso_recuperar"] = False
        d["permiso_crear"] = False
        d["accion"] = "./buscar"   
        d["tipos_item"] = DBSession.query(TipoItem).filter( \
                            TipoItem.id_fase == self.id_fase)
        d["direccion_anterior"] = "../.."
        d["model"] = "Items"
        return d

    @without_trailing_slash
    def new(self, *args, **kw):
        pass
        
    @without_trailing_slash
    def edit(self, *args, **kw):
        pass

    @with_trailing_slash
    @expose('saip.templates.get_all_item')
    @expose('json')
    @paginate('value_list', items_per_page = 3)
    def buscar(self, **kw):
        """ Lista los ítems pertenecientes a una línea base de acuerdo a un 
            criterio de búsqueda introducido por el usuario.
        """
        buscar_table_filler = ItemTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_fase)
        else:
            buscar_table_filler.init("", self.id_fase)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Items", accion = "./buscar")
        items_borrados = DBSession.query(Item) \
            .filter(Item.id.contains(self.id_fase)) \
            .filter(Item.borrado == True).count()
        d["permiso_crear"] = False
        d["permiso_recuperar"] = False
        d["tipos_item"] = DBSession.query(TipoItem)\
                        .filter(TipoItem.id_fase == self.id_fase)
        d["direccion_anterior"] = "../.."
        return d

    @expose('saip.templates.get_all_caracteristicas_item')
    @paginate('value_list', items_per_page=7)
    def listar_caracteristicas(self, **kw):
        """ Muestra las características de un ítem seleccionado que pertenece
            a una línea base.
        """
        if TieneAlgunPermiso(tipo = u"Fase", recurso = u"Item", id_fase = \
                            self.id_fase).is_met(request.environ):
            pk = kw["pk_item"]
            pk_id = unicode(pk.split("-")[0] + "-" + pk.split("-")[1] + "-" + \
                    pk.split("-")[2] + "-" + pk.split("-")[3])
            pk_version = pk.split("-")[4]
            anexo = DBSession.query(Item.anexo).filter(Item.id == pk_id) \
                    .filter(Item.version == pk_version).one()
            anexo = json.loads(anexo.anexo)
            d = dict()
            d['anexo'] = anexo
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            redirect('./')
