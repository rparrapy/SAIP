# -*- coding: utf-8 -*-
"""
Controlador de proyectos en el módulo de administración utilizado para la
importación de fases o tipos de ítem.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tg.controllers import RestController
from tg.decorators import with_trailing_slash, paginate
from tg import expose, request
from tg import tmpl_context
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from saip.model import DBSession
from saip.model.app import Proyecto, Fase, TipoItem
from saip.lib.auth import TienePermiso
from saip.controllers.fase_controller_2 import FaseControllerNuevo
from sqlalchemy import or_

class ProyectoTable(TableBase):
    """ 
    Define el formato de la tabla.
    """
    __model__ = Proyecto
    __omit_fields__ = ['id', 'fases', 'fichas', 'id_lider']
proyecto_table = ProyectoTable(DBSession)

class ProyectoTableFiller(TableFiller):
    """
    Clase que se utiliza para llenar las tablas.
    """
    __model__ = Proyecto
    id = ""
    opcion = ""
    buscado = ""
    def __actions__(self, obj):
        """
        Define las acciones posibles para cada proyecto.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        value = value + '<div><a class="fase_link" href="'+pklist+ \
                '/fases" style="text-decoration:none" TITLE = "Fases"></a>'\
                '</div>'
        value = value + '</div>'
        return value

    def lider(self, obj):
        if obj.lider:
            return obj.lider.nombre_usuario
        else:
            return None

    def init(self, buscado):
        self.buscado = buscado

    def _do_get_provider_count_and_objs(self, buscado = "", **kw):
        """
        Se utiliza para listar solo los proyectos que cumplan ciertas
        condiciones y de acuerdo a ciertos permisos.
        """
        self.id_fase = unicode(request.url.split("/")[-4])
        self.opcion = unicode(request.url.split("/")[-3])
        if self.opcion == unicode("tipo_item"):
            if TienePermiso("importar tipo de item", id_fase = self.id_fase):
               proyectos = DBSession.query(Proyecto).join(Proyecto.fases) \
                        .filter(Proyecto.fases != None).order_by(Proyecto.id) \
                        .all()
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
                    band = True
                    for fase in proyecto.fases:
                        if len(fase.tipos_item) > 1 and \
                            fase.id != self.id_fase: band = False
                    if band: proyectos.remove(proyecto)
            else:
                proyectos = list()
        else:
            if TienePermiso("importar fase", id_proyecto = self.id):
                proyectos = DBSession.query(Proyecto).filter(Proyecto.id != \
                    self.id).filter(or_(Proyecto.nombre.contains( \
                    self.buscado), Proyecto.descripcion.contains( \
                    self.buscado), Proyecto.nro_fases.contains(self.buscado), \
                    Proyecto.fecha_inicio.contains(self.buscado), \
                    Proyecto.fecha_inicio.contains(self.buscado), \
                    Proyecto.id_lider.contains(self.buscado))) \
                    .filter(Proyecto.fases != None).all()
            else:
                proyectos = list()
        return len(proyectos), proyectos 

proyecto_table_filler = ProyectoTableFiller(DBSession)

class ProyectoControllerNuevo(RestController):
    """ Controlador de proyectos utilizado para la importación"""
    fases = FaseControllerNuevo()
    table = proyecto_table
    proyecto_filler = proyecto_table_filler
    
    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)
    def get_all(self):
        """
        Lista los proyectos existentes de acuerdo a condiciones establecidas en 
        el L{proyecto_controller_2.ProyectoTableFiller
        ._do_get_provider_count_and_objs}.
        """ 
        if TienePermiso("importar tipo de item").is_met(request.environ) or \
                        TienePermiso("importar fase").is_met(request.environ):
            proyecto_table_filler.init("")
            tmpl_context.widget = self.table
            d = dict()
            d["value_list"] = self.proyecto_filler.get_value()
            d["model"] = "proyectos"
            d["accion"] = "./buscar"
            d["direccion_anterior"] = "../"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                 u"error")
            raise redirect('./')

    @expose('json')
    def get_one(self, id_proyecto):
        proyecto = DBSession.query(Proyecto).get(id_proyecto).one()
        return dict(proyecto = proyecto)

    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)

    def buscar(self, **kw):
        """
        Lista los proyectos de acuerdo a un criterio de búsqueda introducido
        por el usuario.
        """
        buscar_table_filler = ProyectoTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "proyectos", accion = "./buscar")
        d["direccion_anterior"] = "../"
        return d
