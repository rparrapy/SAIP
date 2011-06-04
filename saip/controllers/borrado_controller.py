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
    id_fase = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        pklist = pklist[0:-2]+ "-" + pklist[-1]
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="revivir_link" href="revivir?id_item='+pklist[0:-2]+'" style="text-decoration:none">revivir</a>'\
              '</div>'
       
        value = value + '</div>'
        return value
    
    def init(self, buscado, id_fase):
        self.buscado = buscado
        self.id_fase = id_fase
    def _do_get_provider_count_and_objs(self, buscado = "", id_fase = "", **kw):
        items = DBSession.query(Item).filter(Item.nombre.contains(self.buscado)).filter(Item.id_tipo_item.contains(self.id_fase)).filter(Item.borrado == True).all()
                
        return len(items), items 
item_table_filler = ItemTableFiller(DBSession)


class BorradoController(CrudRestController):
    relaciones = RelacionController(DBSession)
    archivos = ArchivoController(DBSession)
    model = Item
    table = item_table
    table_filler = item_table_filler  

    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-4])
        super(BorradoController, self)._before(*args, **kw)
    
    def get_one(self, item_id):
        tmpl_context.widget = item_table
        item = DBSession.query(Item).get(item_id)
        value = item_table_filler.get_value(item = item)
        return dict(item = item, value = value, accion = "./buscar")

    @without_trailing_slash
    @expose()
    @require(TienePermiso("manage"))
    def revivir(self, *args, **kw):
        id_item = kw["id_item"]
        item = DBSession.query(Item).filter(Item.id == id_item).one()
        item.borrado = False
        transaction.commit()
        raise redirect('./')


    @with_trailing_slash
    @expose("saip.templates.get_all_borrado")
    @expose('json')
    @paginate('value_list', items_per_page=3)
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        d = super(BorradoController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        for item in reversed(d["value_list"]):
            id_fase_item = DBSession.query(TipoItem.id_fase).filter(TipoItem.id == item["tipo_item"]).scalar()
            #if item['borrado'] == u'True':
            #    d["value_list"].remove(item)
            #else:
            if not (id_fase_item == self.id_fase) or item["borrado"] == u"False":
                d["value_list"].remove(item)            
            
        return d
   

    @with_trailing_slash
    @expose('saip.templates.get_all_item')
    @expose('json')
    @paginate('value_list', items_per_page = 3)
    @require(TienePermiso("manage"))
    def buscar(self, **kw):
        id_fase = unicode(request.url.split("/")[-3])
        buscar_table_filler = ItemTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], id_fase)
        else:
            buscar_table_filler.init("", id_fase)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "item", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["tipos_item"] = DBSession.query(TipoItem).filter(TipoItem.id_fase == self.id_fase)
        return d

   