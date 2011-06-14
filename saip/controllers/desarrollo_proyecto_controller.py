# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash
from tg import expose, request
from tg import tmpl_context #templates
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from saip.model import DBSession
from saip.model.app import Proyecto
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from saip.controllers.desarrollo_fase_controller import DesarrolloFaseController

class ProyectoTable(TableBase):
	__model__ = Proyecto
	__omit_fields__ = ['id', 'fases', 'fichas']
proyecto_table = ProyectoTable(DBSession)

class ProyectoTableFiller(TableFiller):
    __model__ = Proyecto
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        value = value + '<div><a class="fase_link" href="'+pklist+'/fases" style="text-decoration:none">Fases</a>'\
                '</div>'
        value = value + '</div>'
        return value

    def _do_get_provider_count_and_objs(self, **kw):
        if TieneAlgunPermiso(tipo = u"Fase", recurso = u"Item"):
            proyectos = DBSession.query(Proyecto).filter(Proyecto.estado == u"En desarrollo").all()
            for proyecto in reversed(proyectos):
                if not TieneAlgunPermiso(tipo = u"Fase", recurso = u"Item", id_proyecto = proyecto.id).is_met(request.environ) : proyectos.remove(proyecto)
        else: proyectos = list()       
        return len(proyectos), proyectos 
proyecto_table_filler = ProyectoTableFiller(DBSession)

class DesarrolloProyectoController(RestController):
    fases = DesarrolloFaseController()
    table = proyecto_table
    proyecto_filler = proyecto_table_filler
    
    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    def get_all(self):
        tmpl_context.widget = self.table
        value = self.proyecto_filler.get_value()
        return dict(value = value, model = "Proyectos")

    @expose('json')
    def get_one(self, id_proyecto):
        proyecto = DBSession.query(Proyecto).get(id_proyecto).one()
        return dict(proyecto = proyecto, model = "Proyectos")
