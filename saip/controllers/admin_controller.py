from tg import expose, flash, require, url, request, redirect

from saip.lib.base import BaseController
from saip.model import DBSession, metadata
from saip import model

from saip.controllers.proyecto_controller import ProyectoController
from saip.controllers.usuario_controller import UsuarioController
from saip.controllers.rol_controller import RolController
from saip.controllers.ficha_sistema_controller import FichaSistemaController

class AdminController(BaseController):
    proyectos = ProyectoController(DBSession)  
    roles = RolController(DBSession)
    usuarios = UsuarioController(DBSession)  
    responsables = FichaSistemaController(DBSession)

    @expose('saip.templates.admin')
    def index(self):
        """Handle the front-page."""
        return dict(page='index admin', direccion_anterior = "../")

