# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, LineaBase, TipoItem, Item, Fase
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
from tg import request
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func

from sprox.dojo.formbase import DojoEditableForm
from sprox.widgets.dojo import SproxDojoSelectShuttleField

from formencode.validators import NotEmpty

errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class LineaBaseTable(TableBase):
    __model__ = LineaBase
    __omit_fields__ = ['fase']
linea_base_table = LineaBaseTable(DBSession)

class LineaBaseTableFiller(TableFiller):
    __model__ = LineaBase
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
        lineas_base = DBSession.query(LineaBase).filter(LineaBase.id.contains(self.buscado)).all()
        return len(lineas_base), lineas_base 
    
linea_base_table_filler = LineaBaseTableFiller(DBSession)


class ItemsField(SproxDojoSelectShuttleField):
    
    def update_params(self, d):
        super(ItemsField, self).update_params(d)
        id_fase = unicode(request.url.split("/")[-3])
        ids_tipos_item = DBSession.query(TipoItem.id).filter(TipoItem.id_fase == id_fase)
        ids_item = DBSession.query(Item.id).filter(Item.id_tipo_item.in_(ids_tipos_item)).all() #Agregar que esté aprobado
        lista_ids = list()
        for id_item in ids_item:
            print lista_ids.append(id_item.id)
        a_eliminar = list()
        for opcion in reversed (d['options']):
            if not opcion[1] in lista_ids:
                d['options'].remove(opcion)
        print "OPCIONES"
        print d['options']

class AddLineaBase(AddRecordForm):
    __model__ = LineaBase
    items = ItemsField
    __hide_fields__ = ['fase', 'consistente', 'cerrado']
add_linea_base_form = AddLineaBase(DBSession)

class LineaBaseController(CrudRestController):
    #fases = FaseController(DBSession)
    model = LineaBase
    table = linea_base_table
    table_filler = linea_base_table_filler  
    new_form = add_linea_base_form

    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])#[0:-2]) #verificar
        super(LineaBaseController, self)._before(*args, **kw)
    
    def get_one(self, linea_base_id):
        tmpl_context.widget = linea_base_table
        linea_base = DBSession.query(LineaBase).get(linea_base_id)
        value = linea_base_table_filler.get_value(linea_base = linea_base)
        return dict(linea_base = linea_base, value = value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all") #verificar el html
    @expose('json')
    @paginate('value_list', items_per_page=7)
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        d = super(LineaBaseController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        for linea_base in reversed(d["value_list"]):
            if not (linea_base["id_fase"] == self.id_fase):
                d["value_list"].remove(linea_base)
        #item = DBSession.query(Item).filter(Item.id == self.id_item).filter(Item.version == self.version_item).one()
        #d["fases"] = list()
        #d["fases"].append(DBSession.query(Fase).filter(Fase.id == item.tipo_item.id_fase).one())
        #fase_sgte = DBSession.query(Fase).filter(Fase.id_proyecto == item.tipo_item.fase.id_proyecto).filter(Fase.orden == item.tipo_item.fase.orden +1).first()
        #if fase_sgte:
        #    d["fases"].append(fase_sgte)
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new') #verificar
    @require(TienePermiso("manage"))
    def new(self, *args, **kw):
        tmpl_context.widget = self.new_form
        d = dict(value=kw, model=self.model.__name__)
        #d["items"] = DBSession.query(Item).join(TipoItem).filter(TipoItem.id_fase == kw["fase"]).filter(Item.id != self.id_item).all()
        return d


    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    @require(TienePermiso("manage"))
    def buscar(self, **kw):
        buscar_table_filler = LineaBaseTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Linea Base", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

    @catch_errors(errors, error_handler=new)
    @registered_validate(error_handler=new)
    @expose('json')
    def post(self, **kw):
        lista_ids_item = list()
        l = LineaBase()
        l.descripcion = kw['descripcion']
        maximo_id_linea_base = DBSession.query(func.max(LineaBase.id)).scalar()
        if not maximo_id_linea_base:
            maximo_id_linea_base = "LB0-" + self.id_fase
        linea_base_maxima = maximo_id_linea_base.split("-")[0]
        nro_maximo = int(linea_base_maxima[2:])
        l.id = "LB" + str(nro_maximo + 1) + "-" + self.id_fase
        l.fase = DBSession.query(Fase).filter(Fase.id == self.id_fase).one()
        l.cerrado = True
        l.consistente = True
        for item in kw['items']:
            lista_ids_item.append(item.split("/")[0])
        for id_item in lista_ids_item:
            item = DBSession.query(Item).filter(Item.id == id_item).one()
            print type(item)
            l.items.append(item)
        print "LISTA"
        print l.items

        DBSession.add(l)
        #flash("Creación realizada de forma exitosa")
        raise redirect('./')
