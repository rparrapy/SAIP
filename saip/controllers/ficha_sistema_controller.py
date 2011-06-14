# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Ficha, Usuario, Rol, Proyecto, Fase
from sprox.tablebase import TableBase #para manejar datos de prueba
from sprox.fillerbase import TableFiller #""
from sprox.formbase import AddRecordForm #para creacion
from tg import tmpl_context #templates
from tg import expose, require, request, redirect, flash
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash  
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso
from tg import request
from sqlalchemy import func
from sprox.widgets import PropertySingleSelectField
from saip.lib.func import proximo_id


class FichaTable(TableBase): #para manejar datos de prueba
    __model__ = Ficha
    __field_order__ = ['id','usuario', 'rol', 'proyecto', 'fase']
    __omit_fields__ = ['id_proyecto','id_fase','id_usuario','id_rol']
ficha_table = FichaTable(DBSession)

class FichaTableFiller(TableFiller):#para manejar datos de prueba
    __model__ = Ficha
    buscado=""
    def init(self,buscado, id_usuario):
        self.buscado=buscado

    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("asignar rol sistema").is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm(\'Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        '</form>'\
        '</div>'
        value = value + '</div>'
        return value
    
    def rol(self, obj):
        return obj.rol.nombre

    def usuario(self, obj):
        return obj.usuario.nombre_usuario

    def proyecto(self, obj):
        if obj.proyecto: return obj.proyecto.nombre

    def fase(self, obj):
        if obj.fase: return obj.fase.nombre

    def _do_get_provider_count_and_objs(self, buscado = "", **kw):
        if TienePermiso("asignar rol sistema").is_met(request.environ):
            fichas = DBSession.query(Ficha).all()
            for ficha in reversed(fichas):
                if ficha.rol.tipo != u"Sistema": fichas.remove(ficha)
        else: fichas = list()
        return len(fichas), fichas 
ficha_table_filler = FichaTableFiller(DBSession)

class RolesField(PropertySingleSelectField):

        def _my_update_params(self, d, nullable=False):
             roles = DBSession.query(Rol).filter(Rol.tipo == "Sistema").all()
             d['options'] = [(rol.id, '%s'%(rol.nombre)) for rol in roles]
             return d
            

class AddFicha(AddRecordForm):
    __model__ = Ficha
    __omit_fields__ = ['proyecto','fase','id']
    rol = RolesField
    __dropdown_field_names__ = {'rol':'nombre', 'usuario':'nombre_usuario'}
add_ficha_form = AddFicha(DBSession)


class FichaSistemaController(CrudRestController):
    model = Ficha
    table = ficha_table
    table_filler = ficha_table_filler  
    new_form = add_ficha_form


    def _before(self, *args, **kw):
        super(FichaSistemaController, self)._before(*args, **kw)
    
    def get_one(self, Ficha_id):
        tmpl_context.widget = Ficha_table
        ficha = DBSession.query(Ficha).get(Ficha_id)
        value = proyecto_table_filler.get_value(Ficha=ficha)
        return dict(Ficha=ficha, value=value, accion = "./")

    @with_trailing_slash
    @expose("saip.templates.get_all_sin_buscar")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):       
        d = super(FichaSistemaController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("asignar rol sistema").is_met(request.environ)
        #d["accion"] = "./"
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    def new(self, *args, **kw):
        if TienePermiso("asignar rol sistema").is_met(request.environ):
            return super(FichaSistemaController, self).new(*args, **kw)
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            raise redirect('./')        
    
    def edit(self, *args, **kw):
        pass 
    #@with_trailing_slash
    #@expose('saip.templates.get_all')
    #@expose('json')
    #@paginate('value_list', items_per_page=7)
    #@require(TienePermiso("listar Fichas"))
    #def buscar(self, **kw):
    #    buscar_table_filler = FichaTableFiller(DBSession)
    #    if "parametro" in kw:
    #        buscar_table_filler.init(kw["parametro"])
    #    else:
    #       buscar_table_filler.init("")
    #    tmpl_context.widget = self.table
    #    value = buscar_table_filler.get_value()
    #    d = dict(value_list=value, model="Ficha", accion = "./buscar")
    #    d["permiso_crear"] = TienePermiso("crear ficha").is_met(request.environ)
    #    return d
    
    @expose()
    def post(self, **kw):
        if not DBSession.query(Ficha).filter(Ficha.id_usuario == kw['usuario']).filter(Ficha.id_rol == kw['rol']).count():
            f = Ficha()
            ids_fichas = DBSession.query(Ficha.id).filter(Ficha.id_usuario == kw['usuario']).all()
            if ids_fichas:        
                proximo_id_ficha = proximo_id(ids_fichas)
            else:
                proximo_id_ficha = "FI1-" + kw['usuario']
            f.id = proximo_id_ficha
            usuario = DBSession.query(Usuario).filter(Usuario.id == kw['usuario']).one()
            rol = DBSession.query(Rol).filter(Rol.id ==  kw['rol']).one()
            f.usuario = usuario
            f.rol = rol 
            DBSession.add(f)
        else:
            flash(u"La ficha ya existe", u"error")
        raise redirect('./')
