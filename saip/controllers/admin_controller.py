from tg import expose, flash, require, url, request, redirect

from saip.lib.base import BaseController
from saip.model import DBSession, metadata
from saip import model

from saip.controllers.proyecto_controller import ProyectoController
from saip.controllers.usuario_controller import UsuarioController
from saip.controllers.rol_controller import RolController
from saip.controllers.ficha_sistema_controller import FichaSistemaController
from saip.lib.auth import TienePermiso, TieneAlgunPermiso

class AdminController(BaseController):
    proyectos = ProyectoController(DBSession)  
    roles = RolController(DBSession)
    usuarios = UsuarioController(DBSession)  
    responsables = FichaSistemaController(DBSession)

    @expose('saip.templates.admin')
    def index(self):
        """Handle the front-page."""
        d = dict(page='index admin', direccion_anterior = "../")
        p_proy = TieneAlgunPermiso(tipo = u"Proyecto").is_met(request.environ)
        p_fic = TieneAlgunPermiso(tipo = u"Fase", recurso = u"Ficha") \
                .is_met(request.environ)
        p_t_it = TieneAlgunPermiso(tipo = u"Fase", recurso = u"Tipo de Item") \
                .is_met(request.environ)
        d = dict(page='index', direccion_anterior = "../")
        d["permiso_proyectos"] = p_proy or p_fic or p_t_it
        d["permiso_responsables"] = TieneAlgunPermiso(tipo = u"Sistema", \
                                    recurso = u"Ficha").is_met(request.environ)
        d["permiso_roles"] = TieneAlgunPermiso(tipo = u"Sistema", \
                             recurso = u"Rol").is_met(request.environ)
        d["permiso_usuarios"] = TieneAlgunPermiso(tipo = u"Sistema", \
                                recurso = u"Usuario").is_met(request.environ)
        return d

