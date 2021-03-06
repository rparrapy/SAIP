# -*- coding: utf-8 -*-
"""
Controlador de tipos de ítem en el módulo de administración.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, TipoItem
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors  
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from tg import request, flash
from sqlalchemy import func
from saip.model.app import Fase
from formencode import FancyValidator, Invalid, Schema
from formencode.validators import Regex, NotEmpty, MaxLength, MinLength
from formencode.compound import All
from saip.controllers.proyecto_controller_2 import ProyectoControllerNuevo
from saip.controllers.caracteristica_controller import CaracteristicaController
from saip.lib.func import proximo_id
from sqlalchemy import or_

errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class ValidarExpresion(Regex):
    """
    Clase que se utiliza para validar datos ingresados por el usuario, recibe
    como parámetro una expresión regular.
    """
    messages = {
        'invalid': ("Introduzca un valor que empiece con una letra"),
        }

class Unico(FancyValidator):
    """
    Clase correspondiente a un validador que se utiliza para controlar que el 
    nombre ingresado para cierto tipo de item añadido o modificado no se repita 
    dentro de una fase.
    """
    def _to_python(self, value, state):
        """
        Realiza el control citado anteriormente.
        @param value: Se tiene el valor ingresado por el usuario.
        @type value: Unicode. 
        @return value: Retorna el valor ingresado por el usuario.
        """
        id_tipo_item = unicode(request.url.split("/")[-2])
        id_fase = unicode(request.url.split("/")[-3])
        if id_fase == "tipo_item":
            id_fase = unicode(request.url.split("/")[-4])
        band = DBSession.query(TipoItem).filter(TipoItem.nombre == value) \
                .filter(TipoItem.id != id_tipo_item).filter(TipoItem.id_fase \
                        == id_fase).count()
        if band:
            raise Invalid(
                'El nombre de tipo de item elegido ya está en uso',
                value, state)
        return value

class CodigoUnico(FancyValidator):
    """
    Clase correspondiente a un validador que se utiliza para controlar que el 
    código ingresado para cierto tipo de ítem añadido a una fase no se repita 
    dentro de la misma.
    """
    def _to_python(self, value, state):
        """
        Realiza el control citado anteriormente.
        @param value: Se tiene el valor ingresado por el usuario.
        @type value: Unicode. 
        @return value: Retorna el valor ingresado por el usuario.
        """
        id_fase = unicode(request.url.split("/")[-3])
        valor = value.upper()
        band = DBSession.query(TipoItem).filter(TipoItem.codigo == valor) \
                .filter(TipoItem.id_fase == id_fase).count()
        if band:
            raise Invalid(
                'El codigo de tipo de item elegido ya está en uso',
                value, state)
        return value

class TipoItemTable(TableBase):
    """ 
    Define el formato de la tabla. 
    """
    __model__ = TipoItem
    __omit_fields__ = ['id', 'fase', 'id_fase', 'items', 'caracteristicas']
tipo_item_table = TipoItemTable(DBSession)


class TipoItemTableFiller(TableFiller):
    """
    Clase que se utiliza para llenar las tablas.
    """
    __model__ = TipoItem
    buscado = ""
    id_fase = ""

    def __actions__(self, obj):
        """
        Define las acciones posibles para cada tipo de ítem.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        id_tipo_item = unicode(pklist.split("-")[0])
        value = '<div>'
        if id_tipo_item != u"TI1":
            if TienePermiso("modificar tipo de item", id_fase = self.id_fase) \
                            .is_met(request.environ):
                value = value + '<div><a class="edit_link" href="'+pklist+ \
                        '/edit" style="text-decoration:none" TITLE =' \
                        ' "Modificar"></a>'\
                        '</div>'
            
            value = value + '<div><a class="caracteristica_link" href="' \
                    +pklist+'/caracteristicas" style="text-decoration:none"' \
                    ' TITLE = "Caracteristicas"></a></div>'
            if TienePermiso("eliminar tipo de item", id_fase = self.id_fase) \
                            .is_met(request.environ):
                value = value + '<div>'\
                    '<form method="POST" action="'+pklist+ \
                    '" class="button-to" TITLE = "Eliminar">'\
                    '<input type="hidden" name="_method" value="DELETE" />'\
                    '<input class="delete-button" onclick="return confirm' \
                    '(\'¿Está seguro?\');" value="delete" type="submit" '\
                    'style="background-color: transparent; float:left;' \
                    ' border:0; color: #286571; display: inline; margin: 0;' \
                    ' padding: 0;"/>'\
                    '</form>'\
                    '</div>'
        value = value + '</div>'
        return value
    
    def init(self, buscado, id_fase):
        self.buscado = buscado
        self.id_fase = id_fase

    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        """
        Se utiliza para listar solo los tipos de ítem que cumplan ciertas
        condiciones y de acuerdo a ciertos permisos.
        """
        if self.id_fase == "":
            tiposItem = DBSession.query(TipoItem).filter(or_(TipoItem.nombre \
                    .contains(self.buscado), TipoItem.descripcion.contains( \
                    self.buscado), TipoItem.codigo.contains(self.buscado))) \
                    .all()    
        else:
            pf = TieneAlgunPermiso(tipo = u"Fase", recurso = u"Tipo de Item", \
                id_fase = self.id_fase).is_met(request.environ)  
            if pf:
                tiposItem = DBSession.query(TipoItem).filter( \
                TipoItem.id_fase == self.id_fase).filter(or_(TipoItem.nombre. \
                contains(self.buscado), TipoItem.descripcion.contains( \
                self.buscado), TipoItem.codigo.contains(self.buscado))).all()
            else: tiposItem = list()  
        return len(tiposItem), tiposItem 
tipo_item_table_filler = TipoItemTableFiller(DBSession)

class AddTipoItem(AddRecordForm):
    """ Define el formato del formulario para crear un nuevo tipo de ítem"""
    __model__ = TipoItem
    __omit_fields__ = ['id', 'fase', 'id_fase', 'items', 'caracteristicas']
    nombre = All(NotEmpty(), ValidarExpresion(r'^[A-Za-z][A-Za-z0-9 ]*$'), \
            Unico())
    codigo = All(NotEmpty(), ValidarExpresion(r'^[A-Za-z][A-Za-z]*$'), \
            MaxLength(2), MinLength(2), CodigoUnico())
add_tipo_item_form = AddTipoItem(DBSession)

class EditTipoItem(EditableForm):
    """ 
    Define el formato del formulario para la modificación de un tipo de ítem
    """
    __model__ = TipoItem
    __hide_fields__ = ['id', 'fase', 'items', 'caracteristicas', 'codigo']
    nombre = All(NotEmpty(), ValidarExpresion(r'^[A-Za-z][A-Za-z0-9 ]*$'), \
            Unico())    
edit_tipo_item_form = EditTipoItem(DBSession)

class TipoItemEditFiller(EditFormFiller):
    """ 
    Se utiliza para llenar el formulario de modificación de un tipo de ítem
    con los valores recuperados de la base de datos.
    """
    __model__ = TipoItem
tipo_item_edit_filler = TipoItemEditFiller(DBSession)

class TipoItemController(CrudRestController):
    """ Controlador de tipos de ítem"""
    proyectos = ProyectoControllerNuevo()
    caracteristicas = CaracteristicaController(DBSession)
    model = TipoItem
    table = tipo_item_table
    table_filler = tipo_item_table_filler  
    edit_filler = tipo_item_edit_filler
    edit_form = edit_tipo_item_form
    new_form = add_tipo_item_form
    id_fase = None

    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        super(TipoItemController, self)._before(*args, **kw)
    
    def get_one(self, tipo_item_id):
        tmpl_context.widget = tipo_item_table
        tipo_item = DBSession.query(TipoItem).get(tipo_item_id)
        value = tipo_item_table_filler.get_value(tipo_item = tipo_item)
        return dict(tipo_item = tipo_item, value = value, model = \
                    "Tipos de Item", accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all_tipo_item")
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def get_all(self, *args, **kw):
        """
        Lista los tipos de ítem existentes de acuerdo a condiciones 
        establecidas en el 
        L{tipo_item_controller.TipoItemTableFiller
        ._do_get_provider_count_and_objs}.
        """
        tipo_item_table_filler.init("", self.id_fase)
        d = super(TipoItemController, self).get_all(*args, **kw)
        otrafase = DBSession.query(Fase).filter(Fase.id != self.id_fase) \
                    .filter(Fase.tipos_item != None).all()
        otrafase = [f for f in otrafase if len(f.tipos_item) > 1]
        d["permiso_crear"] = TienePermiso("crear tipo de item", id_fase = \
                            self.id_fase).is_met(request.environ)
        d["permiso_importar"] = TienePermiso("importar tipo de item", \
                            id_fase = self.id_fase).is_met(request.environ) \
                            and otrafase
        d["accion"] = "./buscar"
        d["model"] = "Tipos de item"
        d["direccion_anterior"] = "../.."
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    def new(self, *args, **kw):
        """
        Despliega una página para la creación de un nuevo tipo de ítem
        """
        if TienePermiso("crear tipo de item", id_fase = self.id_fase) \
                    .is_met(request.environ):
            d = super(TipoItemController, self).new(*args, **kw) 
            d["direccion_anterior"] = "./"
            return d 
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')

    @expose('tgext.crud.templates.edit')
    def edit(self, *args, **kw):    
        """
        Despliega una página para la modificación de un tipo de ítem
        """
        self.id_fase = unicode(request.url.split("/")[-4])
        if TienePermiso("modificar tipo de item").is_met(request.environ):
            d = super(TipoItemController, self).edit(*args, **kw)  
            d["direccion_anterior"] = "../"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')
    
    @with_trailing_slash
    @expose('saip.templates.get_all_tipo_item')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        """
        Lista los tipos de ítem de acuerdo a un criterio de búsqueda 
        introducido por el usuario.
        """
        buscar_table_filler = TipoItemTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_fase)
        else:
            buscar_table_filler.init("", self.id_fase)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Tipos de item", \
                accion = "./buscar")
        otrafase = DBSession.query(Fase).filter(Fase.id != self.id_fase) \
                .filter(Fase.tipos_item != None).count()
        d["permiso_crear"] = TienePermiso("crear tipo de item", id_fase = \
                self.id_fase).is_met(request.environ)
        d["permiso_importar"] = TienePermiso("importar tipo de item", \
                id_fase = self.id_fase).is_met(request.environ) and otrafase
        d["direccion_anterior"] = "../.."
        return d

    @catch_errors(errors, error_handler=new)
    @expose()
    @registered_validate(error_handler=new)
    def post(self, **kw):
        """ Registra el nuevo tipo de ítem creado. """
        t = TipoItem()
        t.descripcion = kw['descripcion']
        t.nombre = kw['nombre']
        t.codigo = kw['codigo'].upper()
        ids_tipos_item = DBSession.query(TipoItem.id).filter(TipoItem.id_fase \
                        == self.id_fase).all()
        if ids_tipos_item:        
            proximo_id_tipo_item = proximo_id(ids_tipos_item)
        else:
            proximo_id_tipo_item = "TI1-" + self.id_fase
        t.id = proximo_id_tipo_item
        t.fase = DBSession.query(Fase).filter(Fase.id == self.id_fase).one()        
        DBSession.add(t)
        raise redirect('./')
