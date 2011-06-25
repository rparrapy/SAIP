# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de usuarios.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, Usuario
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect, flash, validate
from tgext.crud.decorators import registered_validate, catch_errors 
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash  
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from sqlalchemy import func, or_
from sprox.formbase import Field
from tw.forms.fields import PasswordField
import transaction
from saip.lib.func import proximo_id
from saip.controllers.ficha_usuario_controller import FichaUsuarioController
from formencode.compound import All
from formencode import FancyValidator, Invalid, Schema
from formencode.validators import FieldsMatch, NotEmpty

errors = ()


class UsuarioTable(TableBase):
	__model__ = Usuario
	__omit_fields__ = ['id', 'fichas','_password','password','roles', \
                    'proyectos']
usuario_table = UsuarioTable(DBSession)

class UsuarioTableFiller(TableFiller):
    """ Clase que se utiliza para llenar las tablas de usuario.
    """
    __model__ = Usuario
    buscado=""
    def __actions__(self, obj):
        """ Define las acciones posibles para cada usuario.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("modificar usuario").is_met(request.environ):
            value = value + '<div><a class="edit_link" href="'+pklist+ \
                '/edit" style="text-decoration:none">edit</a>'\
                '</div>'
            value = value + '<div><a class="responsable_link" href="'+pklist+ \
                    '/responsabilidades" style="text-decoration:none" TITLE=' \
                    '"Responsabilidades"></a></div>'
        if TienePermiso("eliminar usuario").is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm' \
            '(\'Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0;' \
            ' color: #286571; display: inline; margin: 0; padding: 0;"/>'\
            '</form>'\
            '</div>'
        value = value + '</div>'
        return value
    
    def init(self,buscado):
        self.buscado=buscado
    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        """ Se utiliza para listar los usuarios que cumplan ciertas condiciones
            y ciertos permisos.
        """
        if TieneAlgunPermiso(tipo = u"Sistema", recurso = u"Usuario")\
                            .is_met(request.environ):
            usuarios = DBSession.query(Usuario).filter(or_(Usuario \
                        .nombre_usuario.contains(self.buscado), \
                        Usuario.nombre.contains(self.buscado), \
                        Usuario.apellido.contains(self.buscado), \
                        Usuario.email.contains(self.buscado), \
                        Usuario.telefono.contains(self.buscado), \
                        Usuario.direccion.contains(self.buscado))) \
                        .filter(Usuario.id != u"US1").all()
        else:
            usuarios = list()
        return len(usuarios), usuarios 
usuario_table_filler = UsuarioTableFiller(DBSession)

class Unico(FancyValidator):
    """ Clase para verificar que el nombre de usuario introducido sea único.
    """
    def _to_python(self, value, state):
        """ @param value: nombre de usuario introducido.
            @type value: unicode
            @return: value si el nombre es único, error en caso contrario.
        """
        band = DBSession.query(Usuario).filter(Usuario.nombre_usuario == \
                value).count()
        if band:
            raise Invalid(
                'El nombre de usuario elegido ya está en uso',
                value, state)
        return value

form_validator =  Schema(password = NotEmpty(), \
                 chained_validators=(FieldsMatch('password',\
                 'confirmar_password', messages=\
                 {'invalidNoMatch':'Los passwords ingresados no coinciden'}),))

class AddUsuario(AddRecordForm):
    """ Define el formato de la tabla para agregar usuarios.
    """
    __model__ = Usuario
    __base_validator__ = form_validator
    __omit_fields__ = ['id', 'fichas','_password','roles', 'proyectos']
    nombre_usuario = All(Unico(), NotEmpty())
    password = PasswordField('password')
    password_c = PasswordField('confirmar_password')
add_usuario_form = AddUsuario(DBSession)


form_validator_2 =  Schema(chained_validators=(FieldsMatch('nuevo_password',\
                 'confirmar_password', messages=\
                 {'invalidNoMatch':'Los passwords ingresados no coinciden'}),))

class EditUsuario(EditableForm):
    """ Define el formato de la tabla para editar usuarios.
    """
    __model__ = Usuario
    __base_validator__ = form_validator_2
    __hide_fields__ = ['id', 'nombre_usuario',  'fichas','_password','roles', \
                    'proyectos', 'password']
    password_a = PasswordField('nuevo_password')
    password_c = PasswordField('confirmar_password')

edit_usuario_form = EditUsuario(DBSession)

class UsuarioEditFiller(EditFormFiller):
    """ Completa la tabla para editar usuarios.
    """
    __model__ = Usuario
usuario_edit_filler = UsuarioEditFiller(DBSession)

class UsuarioController(CrudRestController):
    """ Controlador del modelo Usuario.
    """
    model = Usuario
    table = usuario_table
    table_filler = usuario_table_filler  
    edit_filler = usuario_edit_filler
    edit_form = edit_usuario_form
    new_form = add_usuario_form
    responsabilidades = FichaUsuarioController(DBSession)
    
    def get_one(self, usuario_id):
        tmpl_context.widget = usuario_table
        usuario = DBSession.query(Usuario).get(usuario_id)
        value = usuario_table_filler.get_value(usuario=usuario)
        return dict(usuario=usuario, value=value, accion = "/usuarios/buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):
        """Lista las fases de acuerdo a lo establecido en
           L{usuario_controller.UsuarioTableFiller._do_get_provider_count_and_objs}.
        """
        d = super(UsuarioController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("crear usuario") \
                .is_met(request.environ)
        d["accion"] = "./buscar"
        d["model"] = "Usuarios"
        d["direccion_anterior"] = "../"
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    def new(self, *args, **kw):
        """ Permite la creación de nuevos usuarios en el sistema.
        """
        if TienePermiso("crear usuario").is_met(request.environ):
            d = super(UsuarioController, self).new(*args, **kw)
            d["model"] = "Usuarios"
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')
        
    
    @expose('tgext.crud.templates.edit')
    def edit(self, *args, **kw):
        """ Permite la edición de usuarios del sistema.
        """
        if TienePermiso("modificar usuario").is_met(request.environ):
            d = super(UsuarioController, self).edit(*args, **kw)
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
        """ Lista los usuarios de acuerdo a un criterio de búsqueda.
        """
        buscar_table_filler = UsuarioTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list=value, model="Usuarios", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("crear usuario") \
                    .is_met(request.environ)
        d["direccion_anterior"] = "../"
        return d

    @catch_errors(errors, error_handler=new)
    @expose()
    @registered_validate(error_handler=new)
    def post(self, **kw):
        """Registra el nuevo usuario creado."""
        u = Usuario()
        u.nombre_usuario = kw['nombre_usuario']
        u.nombre = kw['nombre']
        u.apellido = kw['apellido']
        u.email = kw['email']
        u.direccion = kw['direccion']
        u.telefono = kw['telefono']
        u.password = kw['password']
        ids_usuarios = DBSession.query(Usuario.id).all()
        if ids_usuarios:        
            proximo_id_usuario = proximo_id(ids_usuarios)
        else:
            proximo_id_usuario = "US1"
        u.id = proximo_id_usuario
        DBSession.add(u)
        raise redirect('./')


    @catch_errors(errors, error_handler=edit)
    @expose()
    @registered_validate(error_handler=edit)
    def put(self, *args, **kw):
        """Registra los cambios realizados en un usuario."""
        id_usuario = unicode(args[0])
        u = DBSession.query(Usuario).filter(Usuario.id == id_usuario).one()
        u.nombre_usuario = kw['nombre_usuario']
        u.nombre = kw['nombre']
        u.apellido = kw['apellido']
        u.email = kw['email']
        u.direccion = kw['direccion']
        u.telefono = kw['telefono']
        if kw['nuevo_password'] is not u"": 
            u.password = kw['nuevo_password']
            print kw['nuevo_password']
        transaction.commit()        
        raise redirect('../')
