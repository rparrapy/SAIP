# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de fases del módulo de desarrollo.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tg.controllers import RestController
from tg.decorators import with_trailing_slash, paginate
from tg import expose, flash
from saip.model import DBSession
from saip.model.app import Fase
from tg import request, redirect
from tg import tmpl_context
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
import datetime
from sqlalchemy import func
from saip.model.app import Proyecto, Caracteristica, TipoItem
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from saip.controllers.item_controller import ItemController
from sqlalchemy import or_
from saip.lib.func import estado_fase

class FaseTable(TableBase):
	__model__ = Fase
	__omit_fields__ = ['id', 'proyecto', 'lineas_base', 'fichas', \
        'tipos_item', 'id_proyecto']
fase_table = FaseTable(DBSession)

class FaseTableFiller(TableFiller):
    """ Clase que se utiliza para llenar las tablas de fase en el módulo de
        desarrollo.
    """
    __model__ = Fase
    buscado = ""
    def __actions__(self, obj):
        """ Define las acciones posibles para cada fase en el módulo de 
            desarrollo.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        value = value + '<div><a class="item_link" href="'+pklist+'/items" ' \
            'style="text-decoration:none" TITLE = "Items"></a></div>'
        value = value + '</div>'
        fase = DBSession.query(Fase).filter(Fase.id == pklist).one()
        estado_fase(fase)
        return value

    def init(self, buscado):
        self.buscado = buscado
    def _do_get_provider_count_and_objs(self, buscado = "", **kw):
        """ Se utiliza para listar las fases que cumplan ciertas condiciones y
            ciertos permisos.
        """
        id_proyecto = unicode(request.url.split("/")[-3])
        if TieneAlgunPermiso(tipo = u"Fase", recurso = u"Item", id_proyecto = \
                            id_proyecto):
            fases = DBSession.query(Fase).filter(Fase.id_proyecto == \
                    id_proyecto).order_by(Fase.orden).all()

            for fase in reversed(fases):
                buscado = self.buscado in fase.nombre or \
                          self.buscado in fase.descripcion or \
                          self.buscado in str(fase.orden) or \
                          self.buscado in str(fase.fecha_inicio) or \
                          self.buscado in str(fase.fecha_fin) or \
                          self.buscado in fase.estado

                if not buscado: fases.remove(fase)  
            for fase in reversed(fases):
                if not TieneAlgunPermiso(tipo = u"Fase", recurso = u"Item", \
                                    id_fase = fase.id).is_met(request.environ):
                    fases.remove(fase)
                elif fase.orden > 1:
                    fase_prev = DBSession.query(Fase).filter(Fase.id_proyecto \
                            == id_proyecto).filter(Fase.orden == \
                            fase.orden - 1).one()
                    if not fase_prev.lineas_base: fases.remove(fase)
        else: fases = list()
        return len(fases), fases
fase_table_filler = FaseTableFiller(DBSession)


class DesarrolloFaseController(RestController):
    """ Controlador del modelo Fase para el módulo de desarrollo.
    """
    items = ItemController(DBSession)   
    table = fase_table
    fase_filler = fase_table_filler

    @with_trailing_slash
    @expose('json')
    def get_one(self, proyecto_id):
        fase = DBSession.query(Fase).filter(Fase.id_proyecto == id_fase) \
                .filter(Fase.estado == u"En Desarrollo").one()
        return dict(fase = fase, model = "Fases")
    
    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 7)
    def get_all(self):
        """Lista las fases de acuerdo a lo establecido en
           L{desarrollo_fase_controller.FaseTableFiller._do_get_provider_count_and_objs}.
        """
        fase_table_filler.init("")
        tmpl_context.widget = self.table
        d = dict()
        d["value_list"] = self.fase_filler.get_value()
        d["model"] = "Fases"
        d["accion"] = "./buscar"
        d["direccion_anterior"] = "../.."
        return d

    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        """ Lista las fases de acuerdo a un criterio de búsqueda introducido
            por el usuario.
        """
        buscar_table_filler = FaseTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Fases", accion = "./buscar", \
                direccion_anterior = "../..")
        return d
