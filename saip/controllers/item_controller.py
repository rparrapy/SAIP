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
from tg import request
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func

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
        return dict(item = item, value = value, accion = "/items/buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all_item")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        d = super(ItemController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "/items/buscar"
        for item in reversed(d["value_list"]):
            if not (item["fase"] == self.id_fase):
                d["value_list"].remove(item)
        d["tipos_item"] = DBSession.query(TipoItem).filter(TipoItem.id_fase == self.id_fase)
        return d

    @without_trailing_slash
    @expose('saip.templates.new_item')
    @require(TienePermiso("manage"))
    def new(self, *args, **kw):
        tmpl_context.wtidget = self.new_form
        d = dict(value=kw, model=self.model.__name__)
        d["caracteristicas"] = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_item == kw['tipo_item'])
        d["tipo_item"] = kw['tipo_item']
        return d
    
    @require(TienePermiso("manage"))
    @expose('tgext.crud.templates.edit')
    def edit(self, *args, **kw):
        return super(ItemController, self).edit(*args, **kw)        

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
        d = dict(value_list = value, model = "item", accion = "/items/buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

    @catch_errors(errors, error_handler=new)
    @expose()
    @registered_validate(error_handler=new)
    def post(self, **kw):
        p = Item()
        p.descripcion = kw['descripcion']
        p.nombre = kw['nombre']
        fecha_inicio = datetime.datetime.now()
        p.fecha_inicio = datetime.date(int(fecha_inicio.year),int(fecha_inicio.month),int(fecha_inicio.day))
        p.fecha_fin = datetime.date(int(kw['fecha_fin'][0:4]),int(kw['fecha_fin'][5:7]),int(kw['fecha_fin'][8:10]))
        p.estado = 'Nuevo'
        p.nro_fases = int(kw['nro_fases'])
        maximo_id_item = DBSession.query(func.max(Item.id)).scalar()
        print maximo_id_item
        if maximo_id_item == None: 
            maximo_nro_item = 0
        else:
            maximo_nro_item = int(maximo_id_item[2:])
            
        p.id = "PR" + str(maximo_nro_item + 1)
        DBSession.add(p)
        raise redirect('./')
