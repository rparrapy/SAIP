# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Ficha, Usuario, Rol, Proyecto, Fase
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect, flash
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash  
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from tg import request
from sqlalchemy import func
from sprox.widgets import PropertySingleSelectField
from saip.lib.func import proximo_id


class FichaTable(TableBase):
    __model__ = Ficha
    __field_order__ = ['id','usuario', 'rol', 'proyecto', 'fase']
    __omit_fields__ = ['id_proyecto','id_fase','id_usuario','id_rol', '__actions__']
ficha_table = FichaTable(DBSession)

class FichaTableFiller(TableFiller):
    __model__ = Ficha
    buscado=""
    id_usuario = ""    
    def init(self,buscado, id_usuario):
        self.buscado=buscado
        self.id_usuario = id_usuario
    
    def rol(self, obj):
        return obj.rol.nombre

    def usuario(self, obj):
        return obj.usuario.nombre_usuario

    def proyecto(self, obj):
        if obj.proyecto: return obj.proyecto.nombre

    def fase(self, obj):
        if obj.fase: return obj.fase.nombre

    def _do_get_provider_count_and_objs(self, buscado = "", **kw):
        if self.id_usuario == "":
            fichas = DBSession.query(Ficha).filter(Ficha.id \
                .contains(self.buscado)).all()    
        elif TieneAlgunPermiso(tipo = u"Sistema", recurso = u"Usuario"):            
            fichas = DBSession.query(Ficha).filter(Ficha.id_usuario == \
                self.id_usuario).all()
            for ficha in reversed(fichas):
                if not (self.buscado in ficha.usuario.nombre_usuario or \
                        self.buscado in ficha.rol.nombre or self.buscado in \
                        ficha.id): fichas.remove(ficha)
        return len(fichas), fichas 


ficha_table_filler = FichaTableFiller(DBSession)


class FichaUsuarioController(CrudRestController):
    model = Ficha
    table = ficha_table
    table_filler = ficha_table_filler  



    def _before(self, *args, **kw):
        self.id_usuario = unicode(request.url.split("/")[-3])
        super(FichaUsuarioController, self)._before(*args, **kw)
    
    def get_one(self, Ficha_id):
        tmpl_context.widget = ficha_table
        ficha = DBSession.query(Ficha).get(Ficha_id)
        value = ficha_table_filler.get_value(Ficha=ficha)
        return dict(Ficha=ficha, value=value, accion = "./")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):       
        ficha_table_filler.init("", self.id_usuario)
        d = super(FichaUsuarioController, self).get_all(*args, **kw)
        usuario = DBSession.query(Usuario).get(self.id_usuario)
        d["permiso_crear"] = False
        d["model"] = "Responsabilidades" 
        d["accion"] = "./buscar"
        d["direccion_anterior"] = "../.."
        return d

    @without_trailing_slash
    def new(self, *args, **kw):
        pass

    def edit(self, *args, **kw):
        pass        

    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def buscar(self, **kw):
        buscar_table_filler = FichaTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_usuario)
        else:
           buscar_table_filler.init("", self.id_usuario)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list=value, accion = "./buscar")
        usuario = DBSession.query(Usuario).get(self.id_usuario)
        d["permiso_crear"] = False
        d["model"] = "Responsabilidades"
        d["direccion_anterior"] = "../.."
        return d
    
    def post(self, **kw):
        pass
    
    def put(self, *args, **kw):
        pass

    def post_delete(self, *args, **kw):
        pass
