# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Item, TipoItem, Caracteristica, Relacion
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context #templates
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso
from tg import request, flash
from saip.controllers.fase_controller import FaseController
from saip.controllers.relacion_controller import RelacionController
from saip.controllers.archivo_controller import ArchivoController
from sqlalchemy import func, desc
import transaction
import json
import os
import pydot
from saip.lib.func import *
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class ItemTable(TableBase):
    __model__ = Item
    __omit_fields__ = ['id_tipo_item', 'id_linea_base', 'archivos','tipo_item', 'linea_base', 'relaciones_a', 'relaciones_b']
item_table = ItemTable(DBSession)

class ItemTableFiller(TableFiller):
    __model__ = Item
    buscado = ""
    id_item = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        pklist = pklist[0:-2]+ "-" + pklist[-1]
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="revertir_link" href="revertir?item='+pklist+'" style="text-decoration:none">revertir</a>'\
              '</div>'
       
        value = value + '</div>'
        return value
    
    def init(self, buscado, id_item):
        self.buscado = buscado
        self.id_item = id_item
    def _do_get_provider_count_and_objs(self, buscado = "", id_item = "", **kw):
        items = DBSession.query(Item).filter(Item.nombre.contains(self.buscado)).filter(Item.id.contains(self.id_item)).filter(Item.borrado == False).order_by(desc(Item.version)).all()
        return len(items), items 
item_table_filler = ItemTableFiller(DBSession)


class VersionController(CrudRestController):
    relaciones = RelacionController(DBSession)
    archivos = ArchivoController(DBSession)
    model = Item
    table = item_table
    table_filler = item_table_filler  

    def _before(self, *args, **kw):
        self.id_item = unicode(request.url.split("/")[-3][0:-2])
        super(VersionController, self)._before(*args, **kw)
    
    def get_one(self, item_id):
        tmpl_context.widget = item_table
        item = DBSession.query(Item).get(item_id)
        value = item_table_filler.get_value(item = item)
        return dict(item = item, value = value, accion = "./buscar")

    @without_trailing_slash
    @expose()
    @require(TienePermiso("manage"))
    def revertir(self, *args, **kw):
        id_item = kw["item"][0:-2]
        version_item = kw["item"][-1]
        it = DBSession.query(Item).filter(Item.id == id_item).filter(Item.version == version_item).one()
        version_max = DBSession.query(func.max(Item.version)).filter(Item.id == id_item).scalar()
        nueva_version = Item()
        nueva_version.id = it.id
        nueva_version.version = version_max + 1
        nueva_version.nombre = it.nombre
        nueva_version.descripcion = it.descripcion
        nueva_version.estado = it.estado
        nueva_version.observaciones = it.observaciones
        nueva_version.prioridad = it.prioridad
        nueva_version.complejidad = it.complejidad
        nueva_version.borrado = it.borrado
        nueva_version.anexo = it.anexo
        nueva_version.tipo_item = it.tipo_item
        nueva_version.linea_base = it.linea_base
        for relacion in it.relaciones_a:
            
        transaction.commit()
        raise redirect('./')


    @with_trailing_slash
    @expose("saip.templates.get_all_borrado")
    @expose('json')
    @paginate('value_list', items_per_page=3)
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        d = super(VersionController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        for item in reversed(d["value_list"]):
            if not item["id"] == self.id_item:
                d["value_list"].remove(item)
        mayor = d["value_list"][0]
        for item in reversed(d["value_list"]): 
            if item["version"] > mayor["version"]:
                mayor = item
        d["value_list"].remove(item)                   
        return d
   

    @with_trailing_slash
    @expose('saip.templates.get_all_item')
    @expose('json')
    @paginate('value_list', items_per_page = 3)
    @require(TienePermiso("manage"))
    def buscar(self, **kw):
        id_item = unicode(request.url.split("/")[-4][0:-2])
        buscar_table_filler = ItemTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], id_item)
        else:
            buscar_table_filler.init("", id_fase)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "item", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

   
