# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash
from tg import expose, request
from saip.model import DBSession
from saip.model.app import Proyecto
from saip.controllers.fase_controller_2 import FaseControllerNuevo

class ProyectoControllerNuevo(RestController):
    fases = FaseControllerNuevo()
    @with_trailing_slash
    @expose('saip.templates.get_all_proyecto')
    def get_all(self):
        id_proyecto = unicode(request.url.split("/")[-4])
        proyectos = DBSession.query(Proyecto).filter(Proyecto.id != id_proyecto).all()
        return dict(proyectos=proyectos)

    @expose('json')
    def get_one(self, id_proyecto):
        proyecto = DBSession.query(Proyecto).get(id_proyecto).one()
        return dict(proyecto = proyecto)
