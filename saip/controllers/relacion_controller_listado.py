# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Relacion, Item, Fase, TipoItem
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context #templates
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from saip.lib.auth import TienePermiso
from tg import request, flash
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func, desc, or_, and_
from sqlalchemy.orm import aliased
from saip.lib.func import *
import pydot
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class RelacionTable(TableBase):
    __model__ = Relacion
    __omit_fields__ = ['id_item_1', 'id_item_2', '__actions__']
    __xml_fields__ = ['fase']
    #__dropdown_field_names__ = {'tipo_item':'nombre'}    
relacion_table = RelacionTable(DBSession)

class RelacionTableFiller(TableFiller):
    __model__ = Relacion
    buscado = ""
    id_item = ""
    version_item = ""
    
    def item_1(self, obj):
        return obj.item_1.codigo + "(" + obj.item_1.tipo_item.fase.nombre + ")"

    def item_2(self, obj):
        return obj.item_2.codigo + "(" + obj.item_2.tipo_item.fase.nombre + ")"
      
    def init(self,buscado, id_item, version_item):
        self.buscado = buscado
        self.id_item = id_item
        self.version_item = version_item

    def _do_get_provider_count_and_objs(self, buscado="", **kw): #PROBAR BUSCAR
        item_1 = aliased(Item)
        item_2 = aliased(Item)                
        raux = DBSession.query(Relacion).join((item_1, Relacion.id_item_1 == \
            item_1.id)).join((item_2, Relacion.id_item_2 == item_2.id)) \
            .filter(or_(and_(Relacion.id_item_1 == self.id_item, \
            Relacion.version_item_1 == self.version_item), \
            and_(Relacion.id_item_2 == self.id_item, \
            Relacion.version_item_2 == self.version_item))) \
            .filter(or_(Relacion.id.contains(self.buscado), \
            item_1.nombre.contains(self.buscado), \
            item_2.nombre.contains(self.buscado))).all()
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version_item).one()
        lista = [x for x in relaciones_a_actualizadas(item.relaciones_a) + \
            relaciones_b_actualizadas(item.relaciones_b)]
        relaciones = [r for r in raux if r in lista]
        return len(relaciones), relaciones 
    

relacion_table_filler = RelacionTableFiller(DBSession)

class AddRelacion(AddRecordForm):
    __model__ = Relacion
    __omit_fields__ = ['id', 'id_item_1', 'id_item_2', 'item_1']
add_relacion_form = AddRelacion(DBSession)


class RelacionControllerListado(CrudRestController):
    fases = FaseController(DBSession)
    model = Relacion
    table = relacion_table
    table_filler = relacion_table_filler  
    new_form = add_relacion_form

    def _before(self, *args, **kw):
        self.id_item = unicode("-".join(request.url.split("/")[-3] \
                .split("-")[0:-1]))
        self.version_item = unicode(request.url.split("/")[-3].split("-")[-1])
        super(RelacionControllerListado, self)._before(*args, **kw)
    
    def get_one(self, relacion_id):
        tmpl_context.widget = relacion_table
        relacion = DBSession.query(Relacion).get(relacion_id)
        value = relacion_table_filler.get_value(relacion = relacion)
        return dict(relacion = relacion, value = value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all_comun")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):   
        relacion_table_filler.init("", self.id_item, self.version_item)   
        d = super(RelacionControllerListado, self).get_all(*args, **kw)
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version_item).one()
        d["accion"] = "./buscar"
        d["fases"] = list()
        lista = [x.id_item_2 for x in item.relaciones_a] + \
                [x.id_item_1 for x in item.relaciones_b]
        fase_actual = DBSession.query(Fase).filter(Fase.id == \
                item.tipo_item.id_fase).one()
        band = False
        ts_item = [t for t in fase_actual.tipos_item]
        items = list()
        for t_item in ts_item:
            items = items + t_item.items
        for it in items:
            if it.id not in lista and it.id != self.id_item:
                band = True
                break
        if band: d["fases"].append(fase_actual)
        fase_ant = DBSession.query(Fase).filter(Fase.id_proyecto == \
                item.tipo_item.fase.id_proyecto).filter(Fase.orden == \
                item.tipo_item.fase.orden - 1).first()
        if fase_ant:
            band = False
            ts_item = [t for t in fase_ant.tipos_item]
            items = list()
            for t_item in ts_item:
                items = items + t_item.items
            for it in items:
                if it.id not in lista and it.linea_base:
                    if it.linea_base.cerrado and it.linea_base.consistente:
                        band = True
                        break
            if band: d["fases"].append(fase_ant)
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True
        d["model"] = "Relaciones"
        d["direccion_anterior"] = "../.."
        return d

   


    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        buscar_table_filler = RelacionTableFiller(DBSession)
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version_item).one()
        buscar_table_filler = RelacionTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_item, \
                    self.version_item)
        else:
            buscar_table_filler.init("", self.id_item, self.version_item)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Relaciones", accion = "./buscar")
        d["fases"] = list()
        lista = [x.id_item_2 for x in item.relaciones_a] + \
                [x.id_item_1 for x in item.relaciones_b]
        fase_actual = DBSession.query(Fase).filter(Fase.id == \
                item.tipo_item.id_fase).one()
        band = False
        ts_item = [t for t in fase_actual.tipos_item]
        items = list()
        for t_item in ts_item:
            items = items + t_item.items
        for it in items:
            if it.id not in lista and it.id != self.id_item:
                band = True
                break
        if band: d["fases"].append(fase_actual)
        fase_ant = DBSession.query(Fase).filter(Fase.id_proyecto == \
                item.tipo_item.fase.id_proyecto) \
                .filter(Fase.orden == item.tipo_item.fase.orden - 1).first()
        if fase_ant:
            band = False
            ts_item = [t for t in fase_ant.tipos_item]
            items = list()
            for t_item in ts_item:
                items = items + t_item.items
            for it in items:
                if it.id not in lista and it.linea_base:
                    if it.linea_base.cerrado and it.linea_base.consistente:
                        band = True
                        break
            if band: d["fases"].append(fase_ant)        
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True
        d["direccion_anterior"] = "../.."        
        return d

