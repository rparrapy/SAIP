# -*- coding: utf-8 -*-
"""
Controlador de revisiones de un ítem dado en el módulo de desarrollo.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, Revision, Item, Fase, TipoItem
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from saip.lib.auth import TienePermiso
from tg import request, flash, response
from tg.controllers import CUSTOM_CONTENT_TYPE 
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func, desc, or_
from tw.forms.fields import FileField
from saip.lib.func import *
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class RevisionTable(TableBase):
    """ Define el formato de la tabla."""
    __model__ = Revision
    __omit_fields__ = ['id_item', 'item']
revision_table = RevisionTable(DBSession)

class RevisionTableFiller(TableFiller):
    """
    Clase que se utiliza para llenar las tablas.
    """
    __model__ = Revision
    id_item = ""
    buscado = ""
    version = ""
    def __actions__(self, obj):
        """
        Define las acciones posibles para cada revisión.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version).one()
        if TienePermiso("eliminar revisiones", id_fase = \
                        item.tipo_item.fase.id).is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+ pklist +'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm' \
            '¿Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0;' \
            ' color: #286571; display: inline; margin: 0; padding: 0;"/>'\
            '</form>'\
            '</div>'
        value = value + '</div>'
        return value
    
    def init(self,buscado, id_item, version):
        self.id_item = id_item
        self.buscado = buscado
        self.version = version

    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        """
        Se utiliza para listar solo las revisiones que cumplan ciertas
        condiciones y de acuerdo a ciertos permisos.
        """
        revisiones = DBSession.query(Revision).filter(or_(Revision.id \
            .contains(self.buscado), Revision.descripcion.contains( \
            self.buscado))).filter(Revision.id_item == self.id_item).all()
        return len(revisiones), revisiones 
    

revision_table_filler = RevisionTableFiller(DBSession)


class RevisionController(CrudRestController):
    """ Controlador de revisiones de un ítem dado. """
    model = Revision
    table = revision_table
    table_filler = revision_table_filler  

    def _before(self, *args, **kw):
        self.id_item = unicode("-".join(request.url.split("/")[-3] \
                            .split("-")[0:-1]))
        self.version_item = unicode(request.url.split("/")[-3].split("-")[-1])
        super(RevisionController, self)._before(*args, **kw)
    
    def get_one(self, revision_id):
        tmpl_context.widget = revision_table
        revision = DBSession.query(Revision).get(revision_id)
        value = revision_table_filler.get_value(revision = revision)
        return dict(revision = revision, value = value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):
        """
        Lista las revisiones de un ítem de acuerdo a condiciones establecidas 
        en el L{revision_controller.RevisionTableFiller
        ._do_get_provider_count_and_objs}.
        """ 
        revision_table_filler.init("", self.id_item, self.version_item)      
        d = super(RevisionController, self).get_all(*args, **kw)
        d["permiso_crear"] = False
        d["accion"] = "./buscar"
        d["model"] = "Revisiones"
        d["direccion_anterior"] = "../.."
        return d



    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    @require(TienePermiso("manage"))
    def buscar(self, **kw):
        """
        Lista las revisiones de acuerdo a un criterio de búsqueda introducido
        por el usuario.
        """
        buscar_table_filler = RevisionTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_item, \
                self.version_item)
        else:
            buscar_table_filler.init("", self.id_item, self.version_item)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Revisiones", accion = "./buscar")
        d["permiso_crear"] = False
        d["direccion_anterior"] = "../.."
        return d

    @expose()
    def post_delete(self, *args, **kw):
        """ Elimina una revisión"""
        revision = DBSession.query(Revision).get(args[0])
        if revision.item.linea_base:
            consistencia_lb(revision.item.linea_base)
        super(RevisionController, self).post_delete(*args, **kw)
