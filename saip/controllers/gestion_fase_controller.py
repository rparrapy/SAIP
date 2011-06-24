# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash, paginate
from tg import expose, flash
from saip.model import DBSession
from saip.model.app import Fase
from tg import request, redirect, require
from tg import tmpl_context #templates
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
import datetime
from sqlalchemy import func
from saip.model.app import Proyecto, Caracteristica, TipoItem, Item
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from saip.controllers.linea_base_controller import LineaBaseController
from sqlalchemy.sql import exists
from sqlalchemy import or_
from saip.lib.func import estado_fase

class FaseTable(TableBase):
	__model__ = Fase
	__omit_fields__ = ['id', 'proyecto', 'lineas_base', 'fichas', \
        'tipos_item' , 'id_proyecto']
fase_table = FaseTable(DBSession)

class FaseTableFiller(TableFiller):
    __model__ = Fase
    buscado = ""
    id_proyecto  = ""

    def init(self, buscado ,id_proyecto):
        self.buscado = buscado 
        self.id_proyecto = id_proyecto

    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        id_tipos = DBSession.query(TipoItem.id).filter(TipoItem.id_fase == \
            pklist).all()
        value = value + '<div><a class="linea_base_link" href="'+pklist+ \
            '/lineas_base" style="text-decoration:none" TITLE = ' \
            '"Lineas base"></a></div>'
        value = value + '</div>'
        fase = DBSession.query(Fase).filter(Fase.id == pklist).one()
        estado_fase(fase)
        return value

    def _do_get_provider_count_and_objs(self, **kw):
        if TieneAlgunPermiso(tipo = u"Fase", recurso = u"Linea Base", \
            id_proyecto = self.id_proyecto):
            fases = DBSession.query(Fase).filter(Fase.id_proyecto \
                == self.id_proyecto).all()

            for fase in reversed(fases):
                buscado = self.buscado in fase.nombre or \
                          self.buscado in fase.descripcion or \
                          self.buscado in str(fase.orden) or \
                          self.buscado in str(fase.fecha_inicio) or \
                          self.buscado in str(fase.fecha_fin) or \
                          self.buscado in fase.estado

                if not buscado: fases.remove(fase)  

            aux = list()            
            for fase in fases:
                band = False
                if fase.lineas_base: 
                    band = True
                else:
                    t_items = [t for t in fase.tipos_item]
                    items = list()
                    for t in t_items:
                        items = items + [i for i in t.items]
                    for item in items:
                        if item.estado == u"Aprobado" and not item.revisiones: 
                            band = True
                            break
                if not band:
                    aux.append(fase)
            fasesaux = [f for f in fases if f not in aux] 
            fases = fasesaux
        else: fases = list()
        return len(fases), fases

fase_table_filler = FaseTableFiller(DBSession)


class GestionFaseController(RestController):
    lineas_base = LineaBaseController(DBSession)
    table = fase_table
    fase_filler = fase_table_filler

    @with_trailing_slash
    @expose('json')
    def get_one(self, proyecto_id):
        fases = DBSession.query(Fase).filter(Fase.id_proyecto == proyecto_id) \
        .all()
        return dict(value = value, model = "Fases")
    
    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)
    def get_all(self):
        id_proyecto = unicode(request.url.split("/")[-3])
        fase_table_filler.init("", id_proyecto)
        tmpl_context.widget = self.table
        value = self.fase_filler.get_value()
        d = dict(value_list = value, model = "Fases", accion = "./buscar")
        d["direccion_anterior"] = "../.."
        return d

    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)
    def buscar(self, **kw):
        id_proyecto = unicode(request.url.split("/")[-3])
        buscar_table_filler = FaseTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], id_proyecto)
        else:
            buscar_table_filler.init("", id_proyecto)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Fases", accion = "./buscar")
        d["direccion_anterior"] = "../.."
        return d
