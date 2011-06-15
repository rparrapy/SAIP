# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash, paginate
from tg import expose, request
from tg import tmpl_context #templates
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from saip.model import DBSession
from saip.model.app import Proyecto
from saip.lib.auth import TienePermiso
from saip.controllers.fase_controller_2 import FaseControllerNuevo
from sqlalchemy import or_

class ProyectoTable(TableBase):
	__model__ = Proyecto
	__omit_fields__ = ['id', 'fases', 'fichas', 'lider']
proyecto_table = ProyectoTable(DBSession)

class ProyectoTableFiller(TableFiller):
    __model__ = Proyecto
    id = ""
    opcion = ""
    buscado = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        #if TienePermiso("manage").is_met(request.environ):
        value = value + '<div><a class="fase_link" href="'+pklist+'/fases" style="text-decoration:none">Fases</a>'\
            '</div>'
        value = value + '</div>'
        return value

    def init(self, buscado):
        self.buscado = buscado

    def _do_get_provider_count_and_objs(self, buscado = "", **kw):
        self.id = unicode(request.url.split("/")[-4])
        self.opcion = unicode(request.url.split("/")[-3])
        if self.opcion == unicode("tipo_item"):
            proyectos = DBSession.query(Proyecto).all().filter(or_(Proyecto.nombre.contains(self.buscado), Proyecto.descripcion.contains(self.buscado), Proyecto.nro_fases.contains(self.buscado), Proyecto.fecha_inicio.contains(self.buscado), Proyecto.fecha_inicio.contains(self.buscado), Proyecto.id_lider.contains(self.buscado))).all()
        else:
            proyectos = DBSession.query(Proyecto).filter(Proyecto.id != self.id).filter(or_(Proyecto.nombre.contains(self.buscado), Proyecto.descripcion.contains(self.buscado), Proyecto.nro_fases.contains(self.buscado), Proyecto.fecha_inicio.contains(self.buscado), Proyecto.fecha_inicio.contains(self.buscado), Proyecto.id_lider.contains(self.buscado))).all()       
        return len(proyectos), proyectos 

proyecto_table_filler = ProyectoTableFiller(DBSession)

class ProyectoControllerNuevo(RestController):
    fases = FaseControllerNuevo()
    table = proyecto_table
    proyecto_filler = proyecto_table_filler
    
    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)
    def get_all(self):
        if TienePermiso("importar tipo de item").is_met(request.environ) or TienePermiso("importar fase").is_met(request.environ):
            proyecto_table_filler.init("")
            tmpl_context.widget = self.table
            d = dict()
            d["value_list"] = self.proyecto_filler.get_value()
            d["model"] = "proyectos"
            d["accion"] = "./buscar"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            raise redirect('./')

    @expose('json')
    def get_one(self, id_proyecto):
        proyecto = DBSession.query(Proyecto).get(id_proyecto).one()
        return dict(proyecto = proyecto)

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
        d = dict(value_list = value, model = "proyectos", accion = "./buscar")
        return d
