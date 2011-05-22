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
from sqlalchemy import func
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
    __omit_fields__ = ['item_1', 'item_2']
    __xml_fields__ = ['fase']
relacion_table = RelacionTable(DBSession)

class RelacionTableFiller(TableFiller):
    __model__ = Relacion
    buscado = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
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
        relacions = DBSession.query(Relacion).filter(Relacion.id.contains(self.buscado)).all()
        return len(relacions), relacions 
    
    def fase(self, obj):
        fase = unicode(obj.item_2.tipo_item.id_fase)
        return fase

relacion_table_filler = RelacionTableFiller(DBSession)

class AddRelacion(AddRecordForm):
    __model__ = Relacion
    __omit_fields__ = ['id', 'id_item_1', 'id_item_2', 'item_1']
add_relacion_form = AddRelacion(DBSession)


class RelacionController(CrudRestController):
    fases = FaseController(DBSession)
    model = Relacion
    table = relacion_table
    table_filler = relacion_table_filler  
    new_form = add_relacion_form

    def _before(self, *args, **kw):
        self.id_item = unicode(request.url.split("/")[-3][0:-2])
        self.version_item = unicode(request.url.split("/")[-3][-1])
        #self.id_fase = unicode(request.url.split("/")[-5])
        super(RelacionController, self)._before(*args, **kw)
    
    def get_one(self, relacion_id):
        tmpl_context.widget = relacion_table
        relacion = DBSession.query(Relacion).get(relacion_id)
        value = relacion_table_filler.get_value(relacion = relacion)
        return dict(relacion = relacion, value = value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all_relacion")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        d = super(RelacionController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        for relacion in reversed(d["value_list"]):
            if not (relacion["item_1"] == self.id_item or relacion["item_2"] == self.id_item)  :
                d["value_list"].remove(relacion)
        item = DBSession.query(Item).filter(Item.id == self.id_item).filter(Item.version == self.version_item).one()
        d["fases"] = list()
        d["fases"].append(DBSession.query(Fase).filter(Fase.id == item.tipo_item.id_fase).one())
        fase_sgte = DBSession.query(Fase).filter(Fase.id_proyecto == item.tipo_item.fase.id_proyecto).filter(Fase.orden == item.tipo_item.fase.orden +1).first()
        if fase_sgte:
            d["fases"].append(fase_sgte)
        return d

    @without_trailing_slash
    @expose('saip.templates.new_relacion')
    @require(TienePermiso("manage"))
    def new(self, *args, **kw):
        tmpl_context.widget = self.new_form
        d = dict(value=kw, model=self.model.__name__)
        d["items"] = DBSession.query(Item).join(TipoItem).filter(TipoItem.id_fase == kw["fase"]).filter(Item.id != self.id_item).all()
        return d


    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    @require(TienePermiso("manage"))
    def buscar(self, **kw):
        buscar_table_filler = RelacionTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "relacion", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

    #@catch_errors(errors, error_handler=new)
    @expose('json')
    #@registered_validate(error_handler=new)
    def post(self, **kw):
        r = Relacion()
        maximo_id_relacion = DBSession.query(func.max(Relacion.id)).scalar()
        if not maximo_id_relacion:
            maximo_id_relacion = "RE0-" + self.id_item
        relacion_maximo = maximo_id_relacion.split("-")[0]
        nro_maximo = int(relacion_maximo[2:])
        r.id = "RE" + str(nro_maximo + 1) + "-" + self.id_item
        r.item_1 = DBSession.query(Item).filter(Item.id == self.id_item).filter(Item.version == self.version_item).one()
        #r.version_item_1 = r.item_1.version
        r.item_2 = DBSession.query(Item).filter(Item.id == kw["item_2"]).order_by(Item.version).first()
        #r.version_item_2 = r.item_1.version        
        if forma_ciclo(r.item_1):
            print "Detectoooooo"
            DBSession.delete(r)
        else:
            DBSession.add(r)
        #flash("Creación realizada de forma exitosa")
        raise redirect('./')
