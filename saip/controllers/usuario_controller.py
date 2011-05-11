from tgext.crud import CrudRestController
from saip.model import DBSession, Usuario
from sprox.tablebase import TableBase #para manejar datos de prueba
from sprox.fillerbase import TableFiller #""
from sprox.formbase import AddRecordForm #para creacion
from tg import tmpl_context #templates
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash  
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso
from tg import request
from sqlalchemy import func

class UsuarioTable(TableBase): #para manejar datos de prueba
	__model__ = Usuario
	__omit_fields__ = ['id', 'fichas','_password','password','roles']
usuario_table = UsuarioTable(DBSession)

class UsuarioTableFiller(TableFiller):#para manejar datos de prueba
    __model__ = Usuario
    buscado=""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="edit_link" href="'+pklist+'/edit" style="text-decoration:none">edit</a>'\
              '</div>'
        if TienePermiso("eliminar usuario").is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm(\'Are you sure?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        '</form>'\
        '</div>'
        value = value + '</div>'
        return value
    
    def init(self,buscado):
        self.buscado=buscado
    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        usuarios = DBSession.query(Usuario).filter(Usuario.nombre.contains(self.buscado)).all()
        return len(usuarios), usuarios 
usuario_table_filler = UsuarioTableFiller(DBSession)

class AddUsuario(AddRecordForm):
    __model__ = Usuario
    __omit_fields__ = ['id', 'fichas','_password','roles']
add_usuario_form = AddUsuario(DBSession)

class EditUsuario(EditableForm):
    __model__ = Usuario
    __omit_fields__ = ['id', 'fichas','_password','roles']
edit_usuario_form = EditUsuario(DBSession)

class UsuarioEditFiller(EditFormFiller):
    __model__ = Usuario
usuario_edit_filler = UsuarioEditFiller(DBSession)

class UsuarioController(CrudRestController):
    model = Usuario
    table = usuario_table
    table_filler = usuario_table_filler  
    edit_filler = usuario_edit_filler
    edit_form = edit_usuario_form
    new_form = add_usuario_form
    
    def get_one(self, usuario_id):
        tmpl_context.widget = usuario_table
        usuario = DBSession.query(Usuario).get(usuario_id)
        value = proyecto_table_filler.get_value(usuario=usuario)
        return dict(usuario=usuario, value=value, accion = "/usuarios/buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    #@require(TienePermiso("listar usuarios"))
    def get_all(self, *args, **kw):       
        d = super(UsuarioController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "/usuarios/buscar"
        print d["value_list"] 
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    #@require(TienePermiso("crear usuario"))
    def new(self, *args, **kw):
        return super(UsuarioController, self).new(*args, **kw)        
    
    #@require(TienePermiso("modificar usuario"))
    @expose('tgext.crud.templates.edit')
    def edit(self, *args, **kw):
        print args
        return super(UsuarioController, self).edit(*args, **kw)        

    
    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page=7)
    #@require(TienePermiso("listar usuarios"))
    def buscar(self, **kw):
        buscar_table_filler = UsuarioTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list=value, model="usuario", accion = "/usuarios/buscar")
        d["permiso_crear"] = TienePermiso("crear usuario").is_met(request.environ)
        return d
    
    @expose()
    def post(self, **kw):
        u = Usuario()
        u.nombre_usuario = kw['nombre_usuario']
        u.nombre = kw['nombre']
        u.apellido = kw['apellido']
        u.email = kw['email']
        u.direccion = kw['direccion']
        u.telefono = kw['telefono']
        u.password = kw['password']
        maximo_id = DBSession.query(func.max(Usuario.id)).scalar()
        maximo_id = int(str(maximo_id)[2:]) + 1
        u.id = u"US" + unicode(maximo_id)
        DBSession.add(u)
        raise redirect('./')
