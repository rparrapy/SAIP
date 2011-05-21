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
from sqlalchemy import func
import json
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
        value = '<div>'
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
    fases = FaseController(DBSession)
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

    @with_trailing_slash
    @expose("saip.templates.get_all_item")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        d = super(ItemController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        for item in reversed(d["value_list"]):
            id_fase_item = DBSession.query(TipoItem.id_fase).filter(TipoItem.id == item["tipo_item"]).one()
            print "id_fase_item"
            print id_fase_item
            print "self"
            print self.id_fase
            if not (id_fase_item.id_fase == self.id_fase):
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
    #@expose('tgext.crud.templates.edit')
    #def edit(self, *args, **kw):
    #    """Display a page to edit the record."""
    #    id_tipo_item = unicode(request.url.split("/")[-2])
    #    print "id_tipo_item"
    #    print id_tipo_item
    #    tmpl_context.widget = self.edit_form
    #    pks = self.provider.get_primary_fields(self.model)
    #    kw = {}
    #    for i, pk in  enumerate(pks):
    #        kw[pk] = args[i]
    #    value = self.edit_filler.get_value(kw)
    #    value['_method'] = 'PUT'
    #    print "kw"
    #    print kw
    #    caracteristicas = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_item == id_tipo_item)
    #    return dict(value=value, model=self.model.__name__, pk_count=len(pks), caracteristicas = caracteristicas, tipo_item = tipo_item)
    def edit(self, *args, **kw):
        d = super(ItemController, self).edit(*args, **kw)
        id_item = unicode(request.url.split("/")[-2])
        id_item = id_item.split("-")
        id_tipo_item = id_item[1] + "-" + id_item[2] + "-" + id_item[3]
        caracteristicas = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_item == id_tipo_item).all()
        d['caracteristicas'] = caracteristicas
        print "caract"
        print caracteristicas
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
        print kw
        i = Item()
        i.descripcion = kw['descripcion']
        i.nombre = kw['nombre']
        i.estado = 'En desarrollo'
        i.observaciones = kw['observaciones']
        i.prioridad = kw['prioridad']
        i.complejidad = kw['complejidad']
        nombre_caract = DBSession.query(Caracteristica.nombre).filter(Caracteristica.id_tipo_item == kw['tipo_item']).all()
        anexo = dict()
        for nom_car in nombre_caract:
            anexo[nom_car.nombre] = kw[nom_car.nombre]
        i.anexo = json.dumps(anexo)
        maximo_id_item = DBSession.query(func.max(Item.id)).scalar()
        print maximo_id_item
        if not maximo_id_item:
            maximo_id_item = "IT0-" + kw["tipo_item"]
        item_maximo = maximo_id_item.split("-")[0]
        nro_maximo = int(item_maximo[2:])
        i.id = "IT" + str(nro_maximo + 1) + "-" + kw["tipo_item"]
        i.tipo_item = DBSession.query(TipoItem).filter(TipoItem.id == kw["tipo_item"]).one()
        DBSession.add(i)
        print "guarda"
        #flash("Creación realizada de forma exitosa")
        raise redirect('./')
