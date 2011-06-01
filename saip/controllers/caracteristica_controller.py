# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, TipoItem
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
from sqlalchemy import func
from saip.model.app import Caracteristica
from formencode.validators import Regex
from saip.controllers.proyecto_controller_2 import ProyectoControllerNuevo
from tw.forms.fields import SingleSelectField

errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass


class CaracteristicaTable(TableBase):
    __model__ = Caracteristica
    __omit_fields__ = ['id', 'tipo_item']
caracteristica_table = CaracteristicaTable(DBSession)

class CaracteristicaTableFiller(TableFiller):
    __model__ = Caracteristica
    buscado = ""
    id_tipo_item = ""

    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        #if TienePermiso("manage").is_met(request.environ):
        #    value = value + '<div><a class="edit_link" href="'+pklist+'/edit" style="text-decoration:none">edit</a>'\
        #      '</div>'
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

    def init(self, buscado, id_tipo_item):
        self.buscado = buscado
        self.id_tipo_item = id_tipo_item
    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        if self.id_tipo_item == "":
            caracteristicas = DBSession.query(Caracteristica).filter(Caracteristica.nombre.contains(self.buscado)).all()    
        else:
            caracteristicas = DBSession.query(Caracteristica).filter(Caracteristica.nombre.contains(self.buscado)).filter(Caracteristica.id_tipo_item == self.id_tipo_item).all()  
        return len(caracteristicas), caracteristicas 

caracteristica_table_filler = CaracteristicaTableFiller(DBSession)

class AddCaracteristica(AddRecordForm):
    __model__ = Caracteristica
    __omit_fields__ = ['id', 'tipo_item']
    tipo = SingleSelectField("tipo", options = ['cadena','entero','fecha'])
add_caracteristica_form = AddCaracteristica(DBSession)

class CaracteristicaController(CrudRestController):
    model = Caracteristica
    table = caracteristica_table
    table_filler = caracteristica_table_filler  
    new_form = add_caracteristica_form
    id_tipo_item = None
    def _before(self, *args, **kw):
        self.id_tipo_item = unicode(request.url.split("/")[-3])
        super(CaracteristicaController, self)._before(*args, **kw)

    def get_one(self, caracteristica_id): #verificar nombre tipo_item_id
        tmpl_context.widget = tipo_item_table
        caracteristica = DBSession.query(Caracteristica).get(caracteristica_id)
        value = caracteristica_table_filler.get_value(caracteristica = caracteristica)
        return dict(caracteristica = caracteristica, value = value, model = "Caracteristica", accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def get_all(self, *args, **kw):
        #falta TienePermiso
        d = super(CaracteristicaController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        d["model"] = "Caracteristicas"
        for caracteristica in reversed (d["value_list"]):
            if not (caracteristica["tipo_item"] == self.id_tipo_item):
                d["value_list"].remove(caracteristica)
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    @require(TienePermiso("manage"))
    def new(self, *args, **kw):
        return super(CaracteristicaController, self).new(*args, **kw)

    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        buscar_table_filler = CaracteristicaTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_tipo_item)
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Caracteristica", accion = "./buscar")#verificar valor de model
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

    @catch_errors(errors, error_handler=new)
    @expose()
    @registered_validate(error_handler=new)
    @require(TienePermiso("manage"))
    def post(self, **kw):
        c = Caracteristica()
        c.descripcion = kw['descripcion']
        c.nombre = kw['nombre']
        c.tipo = kw['tipo']

        maximo_id_caract = DBSession.query(func.max(Caracteristica.id)).filter(Caracteristica.id_tipo_item == self.id_tipo_item).scalar()        
        if not maximo_id_caract:
            maximo_id_caract = "CA0-" + self.id_tipo_item    
        caract_maxima = maximo_id_caract.split("-")[0]
        nro_maximo = int(caract_maxima[2:])
        c.id = "CA" + str(nro_maximo + 1) + "-" + self.id_tipo_item
        c.tipo_item = DBSession.query(TipoItem).filter(TipoItem.id == self.id_tipo_item).one()        
        DBSession.add(c)
        raise redirect('./')
