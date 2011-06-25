# -*- coding: utf-8 -*-
"""
Módulo que define el controlador del módulo de gestión.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tg import expose, flash, require, url, request, redirect

from saip.lib.base import BaseController
from saip.model import DBSession, metadata
from saip import model

from saip.controllers.gestion_proyecto_controller import \
GestionProyectoController


class GestionController(BaseController):
    """Controlador del módulo de gestión.
    """
    proyectos = GestionProyectoController()    

    @expose('saip.templates.index')
    def index(self):
        """Muestra la página del módulo de gestión."""
        return dict(page='index', direccion_anterior = "../")

