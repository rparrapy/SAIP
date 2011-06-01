# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Item, TipoItem, Caracteristica
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
from sqlalchemy import func, desc
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
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        pklist = pklist[0:-2]+ "-" + pklist[-1]
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="costo_link" href="costo?id_item='+pklist[0:-2]+'" style="text-decoration:none">costo impacto</a>'\
              '</div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="edit_link" href="'+pklist+'/edit" style="text-decoration:none">edit</a>'\
              '</div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="toma_link" href="'+pklist+'/archivos" style="text-decoration:none">archivos</a>'\
              '</div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="toma_link" href="'+pklist+'/relaciones" style="text-decoration:none">relaciones</a>'\
              '</div>'         
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm(\'¿Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        '</form>'\
        '</div>'
        value = value + '</div>'
        return value
    
    def init(self,buscado):
        self.buscado = buscado
    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        items = DBSession.query(Item).filter(Item.nombre.contains(self.buscado)).all()
        return len(items), items 
item_table_filler = ItemTableFiller(DBSession)

class AddItem(AddRecordForm):
    __model__ = Item
    __omit_fields__ = ['id', 'archivos', 'fichas', 'revisiones', 'id_tipo_item, id_linea_base', 'tipo_item', 'linea_base','relaciones_a', 'relaciones_b']
add_item_form = AddItem(DBSession)

class EditItem(EditableForm):
    __model__ = Item
    __omit_fields__ = ['id', 'archivos', 'fichas', 'revisiones', 'id_tipo_item, id_linea_base', 'tipo_item', 'linea_base', 'relaciones_a', 'relaciones_b']
edit_item_form = EditItem(DBSession)

class ItemEditFiller(EditFormFiller):
    __model__ = Item
item_edit_filler = ItemEditFiller(DBSession)

class ItemController(CrudRestController):
    relaciones = RelacionController(DBSession)
    model = Item
    table = item_table
    table_filler = item_table_filler  
    edit_filler = item_edit_filler
    edit_form = edit_item_form
    new_form = add_item_form

    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        super(ItemController, self)._before(*args, **kw)
    
    def get_one(self, item_id):
        tmpl_context.widget = item_table
        item = DBSession.query(Item).get(item_id)
        value = item_table_filler.get_value(item = item)
        return dict(item = item, value = value, accion = "./buscar")

    @without_trailing_slash
    @expose()
    @require(TienePermiso("manage"))
    def costo(self, *args, **kw):
        id_item = kw["id_item"]
        if os.path.isfile('saip/public/images/grafo.png'): os.remove('saip/public/images/grafo.png')            
        item = DBSession.query(Item).filter(Item.id == id_item).order_by(desc(Item.version)).first()
        grafo = pydot.Dot(graph_type='digraph')
        valor, grafo = costo_impacto(item, grafo)
        grafo.write_png('saip/public/images/grafo.png')

    @with_trailing_slash
    @expose("saip.templates.get_all_item")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        d = super(ItemController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        aux = list()
        for item in reversed(d["value_list"]):
            id_fase_item = DBSession.query(TipoItem.id_fase).filter(TipoItem.id == item["tipo_item"]).scalar()
            if not (id_fase_item == self.id_fase):
                d["value_list"].remove(item)
        for item in reversed(d["value_list"]):
            for item_2 in reversed(d["value_list"]):
                if item is not item_2  and item["id"] == item_2["id"] : 
                    if item["version"] > item_2["version"]: 
                        d["value_list"].remove(item_2)
                    else:
                        d["value_list"].remove(item) 

        d["tipos_item"] = DBSession.query(TipoItem).filter(TipoItem.id_fase == self.id_fase)
        return d

    @without_trailing_slash
    @expose('saip.templates.new_item')
    @require(TienePermiso("manage"))
    def new(self, *args, **kw):
        tmpl_context.widget = self.new_form
        d = dict(value=kw, model=self.model.__name__)
        d["caracteristicas"] = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_item == kw['tipo_item'])
        d["tipo_item"] = kw['tipo_item']
        return d
    
    @without_trailing_slash
    @require(TienePermiso("manage"))
    @expose('saip.templates.edit_item')
    def edit(self, *args, **kw):

        """Display a page to edit the record."""
        tmpl_context.widget = self.edit_form
        pks = self.provider.get_primary_fields(self.model)
        clave_primaria = args[0]
        pk_version = clave_primaria[-1:]
        pk_id = clave_primaria[0:-2]
        clave = {}
        clave[0] = pk_id
        clave[1] = pk_version        
        kw = {}        
        for i, pk in  enumerate(pks):
            kw[pk] = clave[i]     
        value = self.edit_filler.get_value(kw)
        value['anexo'] = json.loads(value['anexo'])
        d = dict()
        d['value'] = value
        d['model'] = self.model.__name__
        d['pk_count'] = len(pks)

        id_item = unicode(request.url.split("/")[-2])
        id_item = id_item.split("-")
        id_tipo_item = id_item[1] + "-" + id_item[2] + "-" + id_item[3]
        caracteristicas = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_item == id_tipo_item).all()
        d['caracteristicas'] = caracteristicas
        d['tipo_item'] = id_tipo_item
        return d

    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    @require(TienePermiso("manage"))
    def buscar(self, **kw):
        buscar_table_filler = ItemTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "item", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

    #@catch_errors(errors, error_handler=new)
    @expose('json')
    #@registered_validate(error_handler=new)
    def post(self, **kw):
        i = Item()
        i.descripcion = kw['descripcion']
        i.nombre = kw['nombre']
        i.estado = 'En desarrollo'
        i.observaciones = kw['observaciones']
        i.prioridad = kw['prioridad']
        i.complejidad = kw['complejidad']
        i.version = 1
        nombre_caract = DBSession.query(Caracteristica.nombre).filter(Caracteristica.id_tipo_item == kw['tipo_item']).all()
        anexo = dict()
        for nom_car in nombre_caract:
            anexo[nom_car.nombre] = kw[nom_car.nombre]
        i.anexo = json.dumps(anexo)
        maximo_id_item = DBSession.query(func.max(Item.id)).scalar()
        if not maximo_id_item:
            maximo_id_item = "IT0-" + kw["tipo_item"]
        item_maximo = maximo_id_item.split("-")[0]
        nro_maximo = int(item_maximo[2:])
        i.id = "IT" + str(nro_maximo + 1) + "-" + kw["tipo_item"]
        i.tipo_item = DBSession.query(TipoItem).filter(TipoItem.id == kw["tipo_item"]).one()
        DBSession.add(i)
        #flash("Creación realizada de forma exitosa")
        raise redirect('./')
    
    @expose()
    #@registered_validate(error_handler=edit)
    #@catch_errors(errors, error_handler=edit)
    def put(self, *args, **kw):
        """update"""
        clave_primaria = args[0]
        pk_version = clave_primaria[-1:]
        pk_id = clave_primaria[0:-2]
        clave = {}
        clave[0] = pk_id
        clave[1] = pk_version        

        pks = self.provider.get_primary_fields(self.model)
        for i, pk in enumerate(pks):
            if pk not in kw and i < len(clave):
                kw[pk] = clave[i]
        
        nombre_caract = DBSession.query(Caracteristica.nombre).filter(Caracteristica.id_tipo_item == kw['tipo_item']).all()
        anexo = dict()
        for nom_car in nombre_caract:
            anexo[nom_car.nombre] = kw[nom_car.nombre]
        kw["anexo"] = json.dumps(anexo)
        self.provider.update(self.model, params=kw)
        redirect('.../' * len(pks))
