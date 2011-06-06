# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash
from tg import expose, flash
from saip.model import DBSession
from saip.model.app import Fase
from tg import request, redirect
from tg import tmpl_context #templates
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
import datetime
from sqlalchemy import func
from saip.model.app import Proyecto, Caracteristica, TipoItem
from saip.lib.auth import TienePermiso
from saip.controllers.linea_base_controller import LineaBaseController

class FaseTable(TableBase):
	__model__ = Fase
	__omit_fields__ = ['id', 'proyecto', 'lineas_base', 'fichas', 'tipos_item', 'id_proyecto']
fase_table = FaseTable(DBSession)

class FaseTableFiller(TableFiller):
    __model__ = Fase
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="linea_base_link" href="'+pklist+'/lineas_base" style="text-decoration:none">Lineas base</a>'\
                    '</div>'
        value = value + '</div>'
        return value

    def _do_get_provider_count_and_objs(self, **kw):
        id_proyecto = unicode(request.url.split("/")[-3])
        fases = DBSession.query(Fase).filter(Fase.id_proyecto == id_proyecto).all()
        return len(fases), fases
fase_table_filler = FaseTableFiller(DBSession)


class GestionFaseController(RestController):
    lineas_base = LineaBaseController(DBSession)
    table = fase_table
    fase_filler = fase_table_filler

    @with_trailing_slash
    #@expose('saip.templates.get_all_desarrollo_fase')
    def get_one(self, proyecto_id):
        fases = DBSession.query(Fase).filter(Fase.id_proyecto == proyecto_id).all()
        return dict(value = value, model = "Fases")
    
    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    def get_all(self):
        tmpl_context.widget = self.table
        value = self.fase_filler.get_value()
        return dict(value = value, model = "Fases")
