# -*- coding: utf-8 -*-
"""
Controlador de proyectos en el módulo de administración.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, Rol, Permiso
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash 
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from sprox.formbase import EditableForm
from sprox.dojo.formbase import DojoEditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from tg import request, flash
from sqlalchemy import func
from tw.forms.fields import SingleSelectField, MultipleSelectField
from sprox.widgets.dojo import SproxDojoSelectShuttleField
from saip.lib.func import proximo_id
from formencode.validators import Regex, NotEmpty
from formencode.compound import All

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

class RolTable(TableBase):
    """ Define el formato de la tabla"""
    _model__ = Rol
    __omit_fields__ = ['id', 'fichas','usuarios','permisos']
rol_table = RolTable(DBSession)

class RolTableFiller(TableFiller):
    """
    Clase que se utiliza para llenar las tablas.
    """
    __model__ = Rol
    buscado=""
    def __actions__(self, obj):
        """
        Define las acciones posibles para cada proyecto.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("asignar permiso").is_met(request.environ):
            value = value + '<div><a class="edit_link" href="'+pklist+ \
                '/edit/" style="text-decoration:none">edit</a>'\
              '</div>'
        
        if TienePermiso("eliminar rol").is_met(request.environ):
            value = value + '<div>'\
            '<form method="POST" action="'+pklist+'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm' \
            '(\'¿Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0;' \
            ' color: #286571; display: inline; margin: 0; padding: 0;"/>'\
            '</form>'\
            '</div>'
        value = value + '</div>'
        return value
    
    def init(self,buscado):
        self.buscado=buscado
    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        """
        Se utiliza para listar solo los roles que cumplan ciertas
        condiciones y de acuerdo a ciertos permisos.
        """
        if TieneAlgunPermiso(tipo = "Sistema", recurso = "Rol") \
                            .is_met(request.environ):
            roles = DBSession.query(Rol).filter(Rol.nombre.contains( \
                    self.buscado)).all()
        else: roles = list()
        return len(roles), roles 
rol_table_filler = RolTableFiller(DBSession)

class AddRol(AddRecordForm):
    """ Define el formato del formulario para crear un nuevo rol"""
    __model__ = Rol
    __omit_fields__ = ['id', 'fichas','usuarios','permisos']
    nombre = All(NotEmpty(), ValidarExpresion(r'^[A-Za-z][A-Za-z0-9 ]*$'))
    tipo = SingleSelectField("tipo", options = ['Sistema','Proyecto','Fase'])
add_rol_form = AddRol(DBSession)

class PermisosField(SproxDojoSelectShuttleField):
    """ 
    Clase para obtener los permisos disponibles para la creación de un rol.
    """

    template = 'saip.templates.selectshuttle'
    def update_params(self, d):
        super(PermisosField, self).update_params(d)
        id_rol = unicode(request.url.split("/")[-2])
        rol = DBSession.query(Rol).filter(Rol.id == id_rol).one()
        permisos_tipo = DBSession.query(Permiso.id).filter(Permiso.tipo == \
                rol.tipo).all()  
        id_permisos_tipo = list()
        for permiso in permisos_tipo: id_permisos_tipo.append(permiso[0])
        a_eliminar = list()
        for permiso in d['options']:
                if not permiso[0] in id_permisos_tipo:
                    a_eliminar.append(permiso)
        for elemento in a_eliminar:
            d['options'].remove(elemento)


class EditRol(DojoEditableForm):
    """
    Define el formato de la tabla para editar roles.
    """
    __model__ = Rol
    permisos = PermisosField
    __limit_fields__ = ['permisos']
    __hide_fields__ = ['id']
    __dropdown_field_names__ = {'permisos':'nombre'} 

            
edit_rol_form = EditRol(DBSession)

class RolEditFiller(EditFormFiller):
    """
    Completa la tabla para editar roles.
    """
    __model__ = Rol
rol_edit_filler = RolEditFiller(DBSession)

class RolController(CrudRestController):
    """
    Controlador de Rol para el módulo de administración.
    """
    model = Rol
    table = rol_table
    table_filler = rol_table_filler  
    edit_filler = rol_edit_filler
    edit_form = edit_rol_form
    new_form = add_rol_form

    def get_one(self, Rol_id):
        tmpl_context.widget = Rol_table
        rol = DBSession.query(Rol).get(Rol_id)
        value = proyecto_table_filler.get_value(Rol=Rol)
        return dict(Rol=rol, value=value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw): 
        """
        Lista los roles existentes de acuerdo a condiciones establecidas 
        en el L{rol_controller.RolTableFiller._do_get_provider_count_and_objs}.
        """ 
        d = super(RolController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("crear rol").is_met(request.environ)
        d["accion"] = "./buscar"
        d["model"] = "roles"
        d["direccion_anterior"] = "../"
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    def new(self, *args, **kw):
        """
        Despliega una página para la creación de un nuevo rol.
        """
        if TienePermiso("crear rol").is_met(request.environ):
            d = super(RolController, self).new(*args, **kw)
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')
                   
    @without_trailing_slash
    @expose('tgext.crud.templates.edit')
    def edit(self, *args, **kw):
        """
        Despliega una página para la modificación de un rol.
        """
        if TienePermiso("asignar permiso").is_met(request.environ):
            d = super(RolController, self).edit(*args, **kw)
            d["direccion_anterior"] = "../"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')
            
    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def buscar(self, **kw):
        """
        Lista los roles de acuerdo a un criterio de búsqueda introducido
        por el usuario.
        """
        buscar_table_filler = RolTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list=value, model="roles", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("crear rol").is_met(request.environ)
        d["direccion_anterior"] = "../"
        return d
    

    @catch_errors(errors, error_handler=new)
    @expose()
    @registered_validate(error_handler=new)
    def post(self, **kw):
        """ Registra el nuevo rol creado. """
        r = Rol()
        r.nombre = kw['nombre']
        r.descripcion = kw['descripcion']
        r.tipo = kw['tipo']
        ids_roles = DBSession.query(Rol.id).all()
        if ids_roles:        
            proximo_id_rol = proximo_id(ids_roles)
        else:
            proximo_id_rol = "RL1"
        r.id = proximo_id_rol
        DBSession.add(r)
        raise redirect('./')
