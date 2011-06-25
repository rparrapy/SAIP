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

from saip.controllers.desarrollo_proyecto_controller import \
DesarrolloProyectoController


class DesarrolloController(BaseController):
    """Controlador del módulo de desarrollo.
    """
    proyectos = DesarrolloProyectoController()    

    @expose('saip.templates.index')
    def index(self):
        """Muestra la página del módulo de desarrollo."""
        return dict(page='index desarrollo', direccion_anterior = "../")

