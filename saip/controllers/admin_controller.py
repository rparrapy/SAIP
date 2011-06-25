# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de fases en el módulo de administración
a la hora de importar fases o tipos de ítem.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
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
    """Controlador del módulo de administración.
    """
    proyectos = ProyectoController(DBSession)  
    roles = RolController(DBSession)
    usuarios = UsuarioController(DBSession)  
    responsables = FichaSistemaController(DBSession)

    @expose('saip.templates.admin')
    def index(self):
        """Muestra la página del módulo de administración."""
        p_proy = TieneAlgunPermiso(tipo = u"Sistema", recurso = u"Proyecto") \
                .is_met(request.environ)
        p_d_p = TieneAlgunPermiso(tipo = u"Proyecto").is_met(request.environ)
        p_fic = TieneAlgunPermiso(tipo = u"Fase", recurso = u"Ficha") \
                .is_met(request.environ)
        p_t_it = TieneAlgunPermiso(tipo = u"Fase", recurso = u"Tipo de Item") \
                .is_met(request.environ)
        d = dict(direccion_anterior = "../", page='index admin')
        d["permiso_proyectos"] = p_proy or p_fic or p_t_it or p_d_p
        d["permiso_responsables"] = TieneAlgunPermiso(tipo = u"Sistema", \
                                    recurso = u"Ficha").is_met(request.environ)
        d["permiso_roles"] = TieneAlgunPermiso(tipo = u"Sistema", \
                             recurso = u"Rol").is_met(request.environ)
        d["permiso_usuarios"] = TieneAlgunPermiso(tipo = u"Sistema", \
                                recurso = u"Usuario").is_met(request.environ)
        return d

