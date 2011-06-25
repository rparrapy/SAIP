# -*- coding: utf-8 -*-
"""
Controlador de proyectos en el módulo de gestión.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tg.controllers import RestController
from tg.decorators import with_trailing_slash, paginate
from tg import expose, request, require
from tg import tmpl_context
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from saip.model import DBSession
from saip.model.app import Proyecto
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from saip.controllers.gestion_fase_controller import GestionFaseController
from sqlalchemy import or_
from saip.lib.func import estado_proyecto

class ProyectoTable(TableBase):
    """ 
    Define el formato de la tabla. 
    """
    __model__ = Proyecto
    __omit_fields__ = ['id', 'fases', 'fichas', 'lider']
proyecto_table = ProyectoTable(DBSession)

class ProyectoTableFiller(TableFiller):
    """
    Clase que se utiliza para llenar las tablas.
    """
    __model__ = Proyecto
    buscado = ""
    def __actions__(self, obj):
        """
        Define las acciones posibles para cada proyecto.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        value = value + '<div><a class="fase_link" href="'+pklist+'/fases" '\
            'style="text-decoration:none" TITLE = "Fases"></a></div>'
        value = value + '</div>'
        pr = DBSession.query(Proyecto).get(pklist)
        estado_proyecto(pr)
        return value

    def init(self, buscado):
        self.buscado = buscado   

    def fase_apta(self, proyecto):
        """ 
        Verifica si existe alguna fase en el proyecto que cumpla con los
        requisitos para poder gestionar las líneas base.
        @param proyecto: Tiene el proyecto a verificar.
        @type proyecto: L{Proyecto}. 
        @return: Retorna True o False de acuerdo a si la fase es o no apta.
        @rtype: Boolean 
        """
        fases = proyecto.fases
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
        if fases:
            return True
        else:
            return False 
        

    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se utiliza para listar solo los proyectos que cumplan ciertas
        condiciones y de acuerdo a ciertos permisos.
        """
        if TieneAlgunPermiso(tipo = u"Fase", recurso = u"Linea Base"):
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
                if not (TieneAlgunPermiso(tipo = u"Fase", recurso = \
                        u"Linea Base", id_proyecto = proyecto.id) \
                        .is_met(request.environ) and self.fase_apta(proyecto)): 
                    proyectos.remove(proyecto)
                
        else: proyectos = list()       
        return len(proyectos), proyectos 

proyecto_table_filler = ProyectoTableFiller(DBSession)

class GestionProyectoController(RestController):
    """ 
    Controlador de proyectos utilizado en el módulo de gestión del sistema
    """
    fases = GestionFaseController()
    table = proyecto_table
    proyecto_filler = proyecto_table_filler
    
    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)
    def get_all(self):
        """
        Lista los proyectos existentes de acuerdo a condiciones establecidas 
        en el L{gestion_proyecto_controller.ProyectoTableFiller
        ._do_get_provider_count_and_objs}.
        """ 
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
        return dict(value_list = value, model = "Proyectos", \
                accion = "./buscar", direccion_anterior = "../..")
