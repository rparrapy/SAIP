from tg import expose, flash, require, url, request, redirect

from saip.lib.base import BaseController
from saip.model import DBSession, metadata
from saip import model

from saip.controllers.gestion_proyecto_controller import GestionProyectoController


class GestionController(BaseController):
    proyectos = GestionProyectoController()    

    @expose('saip.templates.index')
    def index(self):
        """Handle the front-page."""
        return dict(page='index')

