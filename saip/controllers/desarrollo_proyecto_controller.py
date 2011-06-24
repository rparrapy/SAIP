# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash, paginate
from tg import expose, request
from tg import tmpl_context
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from saip.model import DBSession
from saip.model.app import Proyecto
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from saip.controllers.desarrollo_fase_controller import \
DesarrolloFaseController
from sqlalchemy import or_
from saip.lib.func import estado_proyecto

class ProyectoTable(TableBase):
	__model__ = Proyecto
	__omit_fields__ = ['id', 'fases', 'fichas', 'lider']
proyecto_table = ProyectoTable(DBSession)

class ProyectoTableFiller(TableFiller):

    __model__ = Proyecto
    buscado = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        value = value + '<div><a class="fase_link" href="'+pklist+ \
                '/fases" style="text-decoration:none" TITLE = "Fases"></a>'\
                '</div>'
        value = value + '</div>'
        pr = DBSession.query(Proyecto).get(pklist)
        estado_proyecto(pr)
        return value

    def init(self, buscado):
        self.buscado = buscado
    def _do_get_provider_count_and_objs(self, buscado = "", **kw):
        if TieneAlgunPermiso(tipo = u"Fase", recurso = u"Item"):
            proyectos = DBSession.query(Proyecto).filter(Proyecto.estado != \
                u"Nuevo").order_by(Proyecto.id).all()

            for proyecto in reversed(proyectos):
                buscado = self.buscado in str(proyecto.nro_fases) or \
                          self.buscado in str(proyecto.fecha_inicio) or \
                          self.buscado in str(proyecto.fecha_fin) or \
                          self.buscado in proyecto.lider.nombre_usuario or \
                          self.buscado in proyecto.nombre or \
                          self.buscado in proyecto.descripcion or \
                          self.buscado in proyecto.estado
                if not buscado: proyectos.remove(proyecto)

            for proyecto in reversed(proyectos):
                if not TieneAlgunPermiso(tipo = u"Fase", recurso = u"Item", \
                                        id_proyecto = proyecto.id) \
                                        .is_met(request.environ):
                    proyectos.remove(proyecto)
        else: proyectos = list()       
        return len(proyectos), proyectos 
proyecto_table_filler = ProyectoTableFiller(DBSession)

class DesarrolloProyectoController(RestController):
    fases = DesarrolloFaseController()
    table = proyecto_table
    proyecto_filler = proyecto_table_filler

    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)    
    def get_all(self):
        proyecto_table_filler.init("")
        tmpl_context.widget = self.table
        value = self.proyecto_filler.get_value()
        return dict(value_list = value, model = "Proyectos", \
                    accion = "./buscar", direccion_anterior = "../..")

    @expose('json')
    def get_one(self, id_proyecto):
        proyecto = DBSession.query(Proyecto).get(id_proyecto).one()
        return dict(proyecto = proyecto, model = "Proyectos")

    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)
    def buscar(self, **kw):
        buscar_table_filler = ProyectoTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        return dict(value_list = value, model = "Proyectos", \
                    accion = "./buscar", direccion_anterior = "../..")
