# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Proyecto
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
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func

class ProyectoTable(TableBase): #para manejar datos de prueba
	__model__ = Proyecto
	__omit_fields__ = ['id', 'fases', 'fichas']
proyecto_table = ProyectoTable(DBSession)

class ProyectoTableFiller(TableFiller):#para manejar datos de prueba
    __model__ = Proyecto
    buscado=""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="edit_link" href="'+pklist+'/edit" style="text-decoration:none">edit</a>'\
              '</div>'+'<div><a class="toma_link" href="'+pklist+'/fases" style="text-decoration:none">fase</a></div>'
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
    
    def init(self,buscado):
        self.buscado=buscado
    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        proyectos = DBSession.query(Proyecto).filter(Proyecto.nombre.contains(self.buscado)).all()
        return len(proyectos), proyectos 
proyecto_table_filler = ProyectoTableFiller(DBSession)

class AddProyecto(AddRecordForm):
    __model__ = Proyecto
    __omit_fields__ = ['id', 'fases', 'fichas', 'estado']
add_proyecto_form = AddProyecto(DBSession)

class EditProyecto(EditableForm):
    __model__ = Proyecto
    __omit_fields__ = ['id', 'fases', 'fichas', 'estado']
edit_proyecto_form = EditProyecto(DBSession)

class ProyectoEditFiller(EditFormFiller):
    __model__ = Proyecto
proyecto_edit_filler = ProyectoEditFiller(DBSession)

class ProyectoController(CrudRestController):
    fases = FaseController(DBSession)
    model = Proyecto
    table = proyecto_table
    table_filler = proyecto_table_filler  
    edit_filler = proyecto_edit_filler
    edit_form = edit_proyecto_form
    new_form = add_proyecto_form
    
    def get_one(self, proyecto_id):
        tmpl_context.widget = proyecto_table
        proyecto = DBSession.query(Proyecto).get(proyecto_id)
        value = proyecto_table_filler.get_value(proyecto=proyecto)
        return dict(proyecto=proyecto, value=value, accion = "/proyectos/buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):       
        d = super(ProyectoController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "/proyectos/buscar"
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    @require(TienePermiso("manage"))
    def new(self, *args, **kw):
        return super(ProyectoController, self).new(*args, **kw)        
    
    @require(TienePermiso("manage"))
    @expose('tgext.crud.templates.edit')
    def edit(self, *args, **kw):
        return super(ProyectoController, self).edit(*args, **kw)        

    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page=7)
    @require(TienePermiso("manage"))
    def buscar(self, **kw):
        buscar_table_filler = ProyectoTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list=value, model="proyecto", accion = "/proyectos/buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

    @expose()
    def post(self, **kw):
        p = Proyecto()
        p.descripcion = kw['descripcion']
        p.nombre = kw['nombre']
        p.fecha_inicio = datetime.date(int(kw['fecha_inicio'][0:4]),int(kw['fecha_inicio'][5:7]),int(kw['fecha_inicio'][8:10]))
        p.fecha_fin = datetime.date(int(kw['fecha_fin'][0:4]),int(kw['fecha_fin'][5:7]),int(kw['fecha_fin'][8:10]))
        p.estado = 'Nuevo'
        p.nro_fases = int(kw['nro_fases'])
        maximo_id_proyecto = DBSession.query(func.max(Proyecto.id)).scalar()  
        maximo_nro_proyecto = int(maximo_id_proyecto[2:])
        p.id = "PR" + str(maximo_nro_proyecto + 1)
        DBSession.add(p)
        raise redirect('./')
