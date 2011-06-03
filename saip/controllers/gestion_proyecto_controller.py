# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash
from tg import expose, request
from saip.model import DBSession
from saip.model.app import Proyecto
from saip.controllers.gestion_fase_controller import GestionFaseController

class GestionProyectoController(RestController):
    fases = GestionFaseController()
    @with_trailing_slash
    @expose('saip.templates.get_all_proyecto')
    def get_all(self):
        proyectos = DBSession.query(Proyecto).all()
        return dict(proyectos=proyectos)

    @expose('json')
    def get_one(self, id_proyecto):
        proyecto = DBSession.query(Proyecto).get(id_proyecto).one()
        return dict(proyecto = proyecto)
