# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from repoze.what import predicates

from saip.lib.base import BaseController
from saip.model import DBSession, metadata, Proyecto
from saip import model
from saip.controllers.secure import SecureController

from saip.controllers.error import ErrorController

from saip.controllers.admin_controller import AdminController
from saip.controllers.desarrollo_controller import DesarrolloController
from saip.controllers.gestion_controller import GestionController
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the SAIP application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    desarrollo = DesarrolloController()    
    
    secc = SecureController()

    admin = AdminController()

    gestion = GestionController()

    error = ErrorController()

    def fase_apta(self, proyecto):
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

    @expose('saip.templates.index')
    def index(self):
        """Handle the front-page."""
        p_sis = TieneAlgunPermiso(tipo = u"Sistema").is_met(request.environ)
        p_proy = TieneAlgunPermiso(tipo = u"Proyecto").is_met(request.environ)
        p_fic = TieneAlgunPermiso(recurso = u"Ficha").is_met(request.environ)
        p_t_it = TieneAlgunPermiso(recurso = u"Tipo de Item") \
                .is_met(request.environ)
        proys = DBSession.query(Proyecto).filter(Proyecto.estado != \
                u"Nuevo").all()
        d = dict(page='index', direccion_anterior = "../")
        d["permiso_desarrollo"] = TieneAlgunPermiso(recurso = u"Item") \
                               .is_met(request.environ) and len(proys) != 0 
        for proyecto in reversed(proys):
            if not self.fase_apta(proyecto): proys.remove(proyecto)
        d["permiso_administracion"] = p_sis or p_proy or p_fic or p_t_it
        d["permiso_gestion"] = TieneAlgunPermiso(recurso = u"Linea Base") \
                               .is_met(request.environ) and len(proys) != 0 
         
        return d

    @expose('saip.templates.about')
    def about(self):
        """Handle the 'about' page."""
        return dict(page='about', direccion_anterior = "../")

    @expose('saip.templates.environ')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(environment=request.environ, direccion_anterior = "../")

    @expose('saip.templates.data')
    @expose('json')
    def data(self, **kw):
        """This method showcases how you can use the same controller for a 
        data page and a display page"""
        return dict(params=kw, direccion_anterior = "../")

    @expose('saip.templates.authentication')
    def auth(self):
        """Display some information about auth* on this application."""
        return dict(page='auth', direccion_anterior = "../")

    @expose('saip.templates.index')
    @require(predicates.has_permission('manage', msg=l_('Only for managers')))
    def manage_permission_only(self, **kw):
        """Illustrate how a page for managers only works."""
        return dict(page='managers stuff', direccion_anterior = "../")

    @expose('saip.templates.index')
    @require(predicates.is_user('editor', msg=l_('Only for the editor')))
    def editor_user_only(self, **kw):
        """Illustrate how a page exclusive for the editor works."""
        return dict(page='editor stuff', direccion_anterior = "../")

    @expose('saip.templates.login')
    def login(self, came_from=url('/')):
        """Start the user login."""
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from, direccion_anterior = "../")

    @expose()
    def post_login(self, came_from='/'):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect('/login', came_from=came_from, __logins=login_counter)
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)
        redirect(came_from)

    @expose()
    def post_logout(self, came_from=url('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        redirect(came_from)
