from tgext.crud import CrudRestController
from saip.model import DBSession, Rol
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

class RolTable(TableBase): #para manejar datos de prueba
	__model__ = Rol
	__omit_fields__ = ['id', 'fichas','usuarios','permisos']
Rol_table = RolTable(DBSession)

class RolTableFiller(TableFiller):#para manejar datos de prueba
    __model__ = Rol
    buscado=""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="edit_link" href="'+pklist+'/edit" style="text-decoration:none">edit</a>'\
              '</div>'
        if TienePermiso("eliminar Rol").is_met(request.environ):
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
        Roles = DBSession.query(Rol).filter(Rol.nombre.contains(self.buscado)).all()
        return len(Roles), Roles 
Rol_table_filler = RolTableFiller(DBSession)

class AddRol(AddRecordForm):
    __model__ = Rol
    __omit_fields__ = ['id', 'fichas','usuarios']
add_Rol_form = AddRol(DBSession)

class EditRol(EditableForm):
    __model__ = Rol
    __omit_fields__ = ['id', 'fichas','usuarios','permisos']
edit_Rol_form = EditRol(DBSession)

class RolEditFiller(EditFormFiller):
    __model__ = Rol
Rol_edit_filler = RolEditFiller(DBSession)

class RolController(CrudRestController):
    model = Rol
    table = Rol_table
    table_filler = Rol_table_filler  
    edit_filler = Rol_edit_filler
    edit_form = edit_Rol_form
    new_form = add_Rol_form
    
    def get_one(self, Rol_id):
        tmpl_context.widget = Rol_table
        Rol = DBSession.query(Rol).get(Rol_id)
        value = proyecto_table_filler.get_value(Rol=Rol)
        return dict(Rol=Rol, value=value, accion = "/Roles/buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    #@require(TienePermiso("listar Rols"))
    def get_all(self, *args, **kw):       
        d = super(RolController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "/Roles/buscar"
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    #@require(TienePermiso("crear Rol"))
    def new(self, *args, **kw):
        return super(RolController, self).new(*args, **kw)        
    
    #@require(TienePermiso("modificar Rol"))
    @expose('tgext.crud.templates.edit')
    def edit(self, *args, **kw):
        return super(RolController, self).edit(*args, **kw)        

    
    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page=7)
    #@require(TienePermiso("listar Rols"))
    def buscar(self, **kw):
        buscar_table_filler = RolTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list=value, model="Rol", accion = "/Roles/buscar")
        d["permiso_crear"] = TienePermiso("crear Rol").is_met(request.environ)
        return d
    
    @expose()
    def post(self, **kw):
        r = Rol()
        r.nombre = kw['nombre']
        r.descripcion = kw['descripcion']
        r.tipo = kw['tipo']
        maximo_id = DBSession.query(func.max(Rol.id)).scalar()
        maximo_id = int(str(maximo_id)[2:]) + 1
        u.id = u"RL" + unicode(maximo_id)
        DBSession.add(u)
        raise redirect('./')