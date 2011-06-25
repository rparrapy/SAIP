# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de fases del módulo de administración.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, Fase, Ficha, Usuario, Rol
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
from saip.model.app import Proyecto, TipoItem
from saip.controllers.tipo_item_controller import TipoItemController
from saip.controllers.ficha_fase_controller import FichaFaseController
from formencode.validators import NotEmpty, Regex, DateConverter, DateValidator
from formencode.validators import Int
from formencode.compound import All
from formencode import FancyValidator, Invalid, Schema
from tw.forms import SingleSelectField
from sprox.widgets import PropertySingleSelectField
from saip.controllers.proyecto_controller_2 import ProyectoControllerNuevo
from saip.lib.func import proximo_id, estado_fase
from sqlalchemy import or_
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass


class ValidarExpresion(Regex):
    """ Clase para validar datos introducidos por el usuario. Recibe como
        parámetro una expresión regular.
    """
    messages = {
        'invalid': ("Introduzca un valor que empiece con una letra"),
        }

class Unico(FancyValidator):
    """ Clase para verificar que el nombre de la fase introducido por el usuario
        sea único en el proyecto correspondiente.
    """
    def _to_python(self, value, state):
        """ @param value: nombre introducido por el usuario.
            @type value: unicode
            @return: value si el nombre es único, error en caso contrario.
        """
        id_fase = unicode(request.url.split("/")[-2])
        id_proyecto = unicode(request.url.split("/")[-3])
        if id_proyecto == "fases":
            id_proyecto = unicode(request.url.split("/")[-4])
        band = DBSession.query(Fase).filter(Fase.nombre == value).filter \
                (Fase.id != id_fase).filter(Fase.id_proyecto == \
                id_proyecto).count()
        if band:
            raise Invalid(
                'El nombre de fase elegido ya está en uso',
                value, state)
        return value

class FaseTable(TableBase):
	__model__ = Fase
	__omit_fields__ = ['id', 'proyecto', 'lineas_base', 'fichas', \
                    'tipos_item', 'id_proyecto']
fase_table = FaseTable(DBSession)

class FaseTableFiller(TableFiller):
    """ Clase que se utiliza para llenar las tablas de fase en administración.
    """
    __model__ = Fase
    buscado = ""
    id_proyecto = ""
    def __actions__(self, obj):
        """ Define las acciones posibles para cada fase en administración.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        fase = DBSession.query(Fase).filter(Fase.id == pklist).one()
        estado_fase(fase)
        value = '<div>'
        if TienePermiso("modificar fase", id_proyecto = fase.id_proyecto). \
                        is_met(request.environ):
            value = value + '<div><a class="edit_link" href="'+pklist+ \
                '/edit" style="text-decoration:none" TITLE= "Modificar"></a>'\
                '</div>'
        permiso_tipo_item = TieneAlgunPermiso(tipo = u"Fase", recurso = \
                            u"Tipo de Item", id_fase = pklist). \
                            is_met(request.environ)
        permiso_asignar_rol_cualquier_fase = TienePermiso \
                            ("asignar rol cualquier fase", id_proyecto = \
                            self.id_proyecto).is_met(request.environ)
        permiso_asignar_rol_fase = TienePermiso("asignar rol fase", id_fase = \
                                    pklist).is_met(request.environ)
        if permiso_tipo_item:
            value = value + '<div><a class="tipo_item_link" href="'+pklist+ \
                    '/tipo_item" style="text-decoration:none" TITLE=' \
                    '"Tipos de item"></a></div>'
        if permiso_asignar_rol_fase or permiso_asignar_rol_cualquier_fase:
            value = value + '<div><a class="responsable_link" href="'+pklist+ \
                    '/responsables" style="text-decoration:none" TITLE=' \
                    '"Responsables"></a></div>'
        if TienePermiso("eliminar fase", id_proyecto = fase.id_proyecto). \
                        is_met(request.environ):
            value = value + '<div>'\
                '<form method="POST" action="'+pklist+ \
                '" class="button-to" TITLE= "Eliminar">'\
                '<input type="hidden" name="_method" value="DELETE" />'\
                '<input class="delete-button" onclick="return confirm' \
                '(\'¿Está seguro?\');" value="delete" type="submit" '\
                'style="background-color: transparent; float:left; border:0;' \
                ' color: #286571; display: inline; margin: 0; padding: 0;"/>'\
                '</form>'\
                '</div>'
        value = value + '</div>'
        return value
    
    def init(self, buscado, id_proyecto):
        self.buscado = buscado
        self.id_proyecto = id_proyecto
    def _do_get_provider_count_and_objs(self, **kw):
        """ Se utiliza para listar las fases que cumplan ciertas condiciones y
            ciertos permisos.
        """
        if self.id_proyecto == "":
            fases = DBSession.query(Fase).order_by(Fase.orden).all()
                    
        else:
            fases = DBSession.query(Fase).filter(Fase.id_proyecto == \
                    self.id_proyecto).order_by(Fase.orden).all()
                    
        for fase in reversed(fases):
            buscado = self.buscado in fase.nombre or \
                      self.buscado in fase.descripcion or \
                      self.buscado in str(fase.orden) or \
                      self.buscado in str(fase.fecha_inicio) or \
                      self.buscado in str(fase.fecha_fin) or \
                      self.buscado in fase.estado

            if not buscado: fases.remove(fase)   
                        
        pp = TieneAlgunPermiso(tipo = u"Proyecto", recurso = u"Fase", \
                        id_proyecto = self.id_proyecto).is_met(request.environ)
            
        if not pp:
            for fase in reversed(fases):
                pfp = TienePermiso(u"asignar rol cualquier fase", \
                      id_proyecto = fase.id_proyecto).is_met(request.environ)
                pfi = TieneAlgunPermiso(tipo = "Fase", recurso = u"Ficha", \
                       id_proyecto = fase.id_proyecto).is_met(request.environ)
                pf = TieneAlgunPermiso(tipo = u"Fase", recurso = \
                    u"Tipo de Item", id_fase = fase.id). \
                    is_met(request.environ)
                if not (pf or pfp or pfi): 
                    fases.remove(fase)
        return len(fases), fases 
fase_table_filler = FaseTableFiller(DBSession)


class OrdenFieldNew(PropertySingleSelectField):
    """ Clase para obtener los posibles números de fase (órdenes) para una
        nueva fase de un proyecto.
    """
    def obtener_fases_posibles(self):
        """ @return: Posibles órdenes para la nueva fase de un proyecto.
        """
        id_proyecto = unicode(request.url.split("/")[-3])
        cantidad_fases = DBSession.query(Proyecto.nro_fases).filter( \
                        Proyecto.id == id_proyecto).scalar()
        ordenes = DBSession.query(Fase.orden).filter(Fase.id_proyecto == \
                    id_proyecto).order_by(Fase.orden).all()
        vec = list()
        list_ordenes = list()
        for elem in ordenes:
            list_ordenes.append(elem.orden)
        for elem in xrange(cantidad_fases):
            if not (elem+1) in list_ordenes:
                vec.append(elem+1)        
        return vec
    
    def _my_update_params(self, d, nullable=False):
        """ @param d: diccionario con las opciones posibles de orden.
            @return: d con los valores correctos de órdenes posibles.
        """
        opciones = self.obtener_fases_posibles()
        d['options'] = opciones
        return d

class OrdenFieldEdit(PropertySingleSelectField):
    """ Clase para obtener los posibles números de fase (órdenes) para una fase 
        que se edita de un proyecto.
    """
    def obtener_fases_posibles(self):
        """ @return: Posibles órdenes para la fase a ser editada.
        """
        id_proyecto = unicode(request.url.split("/")[-4])
        id_fase = unicode(request.url.split("/")[-2])
        cantidad_fases = DBSession.query(Proyecto.nro_fases).filter( \
                        Proyecto.id == id_proyecto).scalar()
        ordenes = DBSession.query(Fase.orden).filter(Fase.id_proyecto == \
                        id_proyecto).order_by(Fase.orden).all()
        orden_actual = DBSession.query(Fase.orden).filter(Fase.id == \
                        id_fase).scalar()
        vec = list()
        list_ordenes = list()
        vec.append(orden_actual)
        for elem in ordenes:
            list_ordenes.append(elem.orden)
        for elem in xrange(cantidad_fases):
            if not (elem+1) in list_ordenes:
                vec.append(elem+1)     
        return vec
    
    def _my_update_params(self, d, nullable=False):
        """ @param d: diccionario con las opciones posibles de orden.
            @return: d con los valores correctos de órdenes posibles.
        """
        opciones = self.obtener_fases_posibles()
        d['options'] = opciones
        return d


class AddFase(AddRecordForm):
    """ Define el formato de la tabla para agregar fases.
    """
    __model__ = Fase
    __omit_fields__ = ['id', 'proyecto', 'lineas_base', 'fichas', \
                    'tipos_item', 'id_proyecto', 'estado', 'fecha_inicio','fecha_fin']
    orden = OrdenFieldNew
    nombre = All(NotEmpty(), ValidarExpresion(r'^[A-Za-z][A-Za-z0-9 ]*$'), \
            Unico())
add_fase_form = AddFase(DBSession)

class EditFase(EditableForm):
    """ Define el formato de la tabla para editar fases.
    """
    __model__ = Fase
    __hide_fields__ = ['id', 'lineas_base', 'fichas', 'estado', \
                    'fecha_inicio', 'id_proyecto', 'tipos_item', 'proyecto', 'fecha_fin']
    orden = OrdenFieldEdit
    nombre = All(NotEmpty(), ValidarExpresion(r'^[A-Za-z][A-Za-z0-9 ]*$'), \
            Unico())
edit_fase_form = EditFase(DBSession)

class FaseEditFiller(EditFormFiller):
    """ Completa la tabla para editar fases.
    """
    __model__ = Fase
fase_edit_filler = FaseEditFiller(DBSession)


class FaseController(CrudRestController):
    """ Controlador del modelo Fase para el módulo de administración.
    """
    proyectos = ProyectoControllerNuevo()
    tipo_item = TipoItemController(DBSession)
    responsables = FichaFaseController(DBSession)
    model = Fase
    table = fase_table
    table_filler = fase_table_filler  
    edit_filler = fase_edit_filler
    edit_form = edit_fase_form
    new_form = add_fase_form
    id_proyecto = None

    def _before(self, *args, **kw):
        self.id_proyecto = unicode(request.url.split("/")[-3])
        super(FaseController, self)._before(*args, **kw)
    
    
    def get_one(self, fase_id):
        tmpl_context.widget = fase_table
        fase = DBSession.query(Fase).get(fase_id)
        value = fase_table_filler.get_value(fase = fase)
        return dict(fase = fase, value = value, accion = "./buscar", \
                    direccion_anterior = ".")

    @with_trailing_slash
    @expose("saip.templates.get_all_fase")
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def get_all(self, *args, **kw):  
        """Lista las fases de acuerdo a lo establecido en
           L{fase_controller.FaseTableFiller._do_get_provider_count_and_objs}.
        """
        fase_table_filler.init("", self.id_proyecto)
        d = super(FaseController, self).get_all(*args, **kw)
        cant_fases = DBSession.query(Fase).filter(Fase.id_proyecto == \
                    self.id_proyecto).count()
        otroproyecto = DBSession.query(Proyecto).filter(Proyecto.id != \
                    self.id_proyecto).filter(Proyecto.fases != None).count()
        if cant_fases < DBSession.query(Proyecto.nro_fases).filter( \
                                    Proyecto.id == self.id_proyecto).scalar():
            d["suficiente"] = True
        else:
            d["suficiente"] = False
        d["model"] = "Fases"
        d["permiso_crear"] = TienePermiso("crear fase", id_proyecto = \
                            self.id_proyecto).is_met(request.environ)
        d["permiso_importar"] = TienePermiso("importar fase", id_proyecto = \
                    self.id_proyecto).is_met(request.environ) and otroproyecto
        d["accion"] = "./buscar"
        d["direccion_anterior"] = "../.."
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    def new(self, *args, **kw):
        """ Permite la creación de una nueva fase para un determinado proyecto.
        """
        if TienePermiso("crear fase", id_proyecto = self.id_proyecto). \
                        is_met(request.environ):
            d = super(FaseController, self).new(*args, **kw)
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u" El usuario no cuenta con los permisos necesarios", \
                u"error" )
            raise redirect('./')
    
    @with_trailing_slash
    @expose('saip.templates.get_all_fase')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        """ Lista las fases de acuerdo a un criterio de búsqueda introducido
            por el usuario.
        """
        buscar_table_filler = FaseTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_proyecto)
        else:
            buscar_table_filler.init("", self.id_proyecto)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "fase", accion = "./buscar")

        cant_fases = DBSession.query(Fase).filter(Fase.id_proyecto == \
                    self.id_proyecto).count()
        otroproyecto = DBSession.query(Proyecto).filter(Proyecto.id != \
                       self.id_proyecto).filter(Proyecto.fases != None).count()
        if cant_fases < DBSession.query(Proyecto.nro_fases).filter( \
                        Proyecto.id == self.id_proyecto).scalar():
            d["suficiente"] = True
        else:
            d["suficiente"] = False
        d["model"] = "Fases"
        d["permiso_crear"] = TienePermiso("crear fase", id_proyecto = \
                            self.id_proyecto).is_met(request.environ)
        d["permiso_importar"] = TienePermiso("importar fase", id_proyecto = \
                    self.id_proyecto).is_met(request.environ) and otroproyecto
        d["direccion_anterior"] = "../.."
        return d
    
    def crear_tipo_default(self, id_fase):
        """ Crea un tipo de ítem por defecto al crear una fase.
        """
        ti = TipoItem()
        ti.nombre = "Default"    
        ti.descripcion = "Default"
        ti.id = "TI1-" + id_fase
        ti.codigo = "DF"
        ti.fase = DBSession.query(Fase).filter(Fase.id == id_fase).one() 
        DBSession.add(ti)
    @without_trailing_slash
    @expose('tgext.crud.templates.edit')
    def edit(self, *args, **kw):
        """ Permite la creación de una nueva fase para un determinado proyecto.
        """

        self.id_proyecto = unicode(request.url.split("/")[-4])
        if TienePermiso("modificar fase", id_proyecto = self.id_proyecto). \
                        is_met(request.environ):
            d = super(FaseController, self).edit(*args, **kw)
            d["direccion_anterior"] = "../"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')

    @expose()
    @registered_validate(error_handler=edit)
    @catch_errors(errors, error_handler=edit)
    def put(self, *args, **kw):
        """Registra los cambios realizados en una fase."""
        pks = self.provider.get_primary_fields(self.model)
        for i, pk in enumerate(pks):
            if pk not in kw and i < len(args):
                kw[pk] = args[i]

        self.provider.update(self.model, params=kw)
        redirect('../')

    @catch_errors(errors, error_handler=new)
    @expose()
    @registered_validate(error_handler=new)
    def post(self, **kw):
        """Registra la nueva fase creada."""
        f = Fase()
        f.nombre = kw['nombre']   
        f.orden = kw['orden']
        f.descripcion = kw['descripcion']
        f.estado = 'Inicial'
        ids_fases = DBSession.query(Fase.id).filter(Fase.id_proyecto == \
                    self.id_proyecto).all()
        if ids_fases:        
            proximo_id_fase = proximo_id(ids_fases)
        else:
            proximo_id_fase = "FA1-" + self.id_proyecto
        f.id = proximo_id_fase
        proyecto = DBSession.query(Proyecto).filter(Proyecto.id == \
                    self.id_proyecto).one()
        f.proyecto = proyecto
        DBSession.add(f)
        self.crear_tipo_default(f.id)
        raise redirect('./')
