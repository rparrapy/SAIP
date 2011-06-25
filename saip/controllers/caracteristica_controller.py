# -*- coding: utf-8 -*-
"""
Controlador de características de un tipo de ítem en el módulo de 
administración.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, TipoItem, Item
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
import json
from saip.lib.func import proximo_id
from sqlalchemy import or_

errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass


class CaracteristicaTable(TableBase):
    """ Define el formato de la tabla """
    __model__ = Caracteristica
    __omit_fields__ = ['id', 'tipo_item', '__actions__', 'id_tipo_item']
caracteristica_table = CaracteristicaTable(DBSession)

class CaracteristicaTableFiller(TableFiller):
    """
    Clase que se utiliza para llenar las tablas.
    """
    __model__ = Caracteristica
    buscado = ""
    id_tipo_item = ""

    def init(self, buscado, id_tipo_item):
        self.buscado = buscado
        self.id_tipo_item = id_tipo_item

    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        """
        Se utiliza para listar solo las características que cumplan ciertas
        condiciones.
        """
        if self.id_tipo_item == "":
            caracteristicas = DBSession.query(Caracteristica).filter(or_( \
                        Caracteristica.nombre.contains(self.buscado), \
                        Caracteristica.descripcion.contains(self.buscado), \
                        Caracteristica.tipo.contains(self.buscado))).all()    
        else:
            caracteristicas = DBSession.query(Caracteristica).filter( \
                        Caracteristica.id_tipo_item == self.id_tipo_item) \
                        .filter(or_(Caracteristica.nombre.contains( \
                        self.buscado), Caracteristica.descripcion.contains( \
                        self.buscado), Caracteristica.tipo.contains( \
                        self.buscado))).all()  
        return len(caracteristicas), caracteristicas 

caracteristica_table_filler = CaracteristicaTableFiller(DBSession)

class AddCaracteristica(AddRecordForm):
    """ 
    Define el formato del formulario para crear una nueva característica de
    un tipo de ítem
    """
    __model__ = Caracteristica
    __omit_fields__ = ['id', 'tipo_item', 'actions']
    tipo = SingleSelectField("tipo", options = ['cadena','entero','fecha'])
add_caracteristica_form = AddCaracteristica(DBSession)

class CaracteristicaController(CrudRestController):
    """ Controlador de Características"""
    model = Caracteristica
    table = caracteristica_table
    table_filler = caracteristica_table_filler  
    new_form = add_caracteristica_form
    id_tipo_item = None

    def _before(self, *args, **kw):
        self.id_tipo_item = unicode(request.url.split("/")[-3])
        super(CaracteristicaController, self)._before(*args, **kw)

    def get_one(self, caracteristica_id):
        tmpl_context.widget = tipo_item_table
        caracteristica = DBSession.query(Caracteristica).get(caracteristica_id)
        value = caracteristica_table_filler.get_value(caracteristica = \
                caracteristica)
        return dict(caracteristica = caracteristica, value = value, model = \
                    "Caracteristica", accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def get_all(self, *args, **kw):
        """
        Lista las características existentes de un tipo de ítem de acuerdo a 
        condiciones establecidas en el 
        L{caracteristica_controller.TipoItemTableFiller
        ._do_get_provider_count_and_objs}.
        """
        caracteristica_table_filler.init("", self.id_tipo_item)
        d = super(CaracteristicaController, self).get_all(*args, **kw)
        tipo_item = DBSession.query(TipoItem).filter(TipoItem.id == \
                    self.id_tipo_item).one()
        d["permiso_crear"] = TienePermiso("modificar tipo de item", id_fase = \
                            tipo_item.fase.id).is_met(request.environ)
        d["accion"] = "./buscar"
        d["model"] = "Caracteristicas"
        d["direccion_anterior"] = "../.."
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    def new(self, *args, **kw):
        """
        Despliega una página para la creación de una nueva característica de 
        un tipo de ítem.
        """
        tipo_item = DBSession.query(TipoItem).filter(TipoItem.id == \
                    self.id_tipo_item).one()
        if TienePermiso("modificar tipo de item", id_fase = \
                        tipo_item.fase.id).is_met(request.environ        """
        Lista los tipos de ítem de acuerdo a un criterio de búsqueda 
        introducido por el usuario.
        """):
            d = super(CaracteristicaController, self).new(*args, **kw)
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')

    def edit(self, *args, **kw):
        pass        
 
    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        """
        Lista las características de un tipo de ítem de acuerdo a un criterio 
        de búsqueda introducido por el usuario.
        """
        buscar_table_filler = CaracteristicaTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_tipo_item)
        else:
            buscar_table_filler.init("", self.id_tipo_item)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Caracteristicas", accion = \
                "./buscar")
        tipo_item = DBSession.query(TipoItem).filter(TipoItem.id == \
                self.id_tipo_item).one()
        d["permiso_crear"] = TienePermiso("modificar tipo de item", id_fase = \
                    tipo_item.fase.id).is_met(request.environ)
        d["direccion_anterior"] = "../.."
        return d

    def set_null(self, c):
        items = DBSession.query(Item).filter(Item.id_tipo_item == \
            self.id_tipo_item).all()
        for item in items:
            anexo = item.anexo
            anexo = json.loads(anexo)
            anexo[c.nombre] = None
            anexo = json.dumps(anexo)
            item.anexo = anexo

    @catch_errors(errors, error_handler=new)
    @expose()
    @registered_validate(error_handler=new)
    def post(self, **kw):
        c = Caracteristica()
        c.descripcion = kw['descripcion']
        c.nombre = kw['nombre']
        c.tipo = kw['tipo']
        ids_caracteristicas = DBSession.query(Caracteristica.id).filter( \
                    Caracteristica.id_tipo_item == self.id_tipo_item).all()
        if ids_caracteristicas:        
            proximo_id_caracteristica = proximo_id(ids_caracteristicas)
        else:
            proximo_id_caracteristica = "CA1-" + self.id_tipo_item
        c.id = proximo_id_caracteristica
        c.tipo_item = DBSession.query(TipoItem).filter(TipoItem.id == \
                self.id_tipo_item).one()        
        DBSession.add(c)
        self.set_null(c)
        raise redirect('./')
