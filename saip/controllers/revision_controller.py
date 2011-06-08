# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Revision, Item, Fase, TipoItem
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context #templates
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from saip.lib.auth import TienePermiso
from tg import request, flash, response
from tg.controllers import CUSTOM_CONTENT_TYPE 
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func
from tw.forms.fields import FileField
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class RevisionTable(TableBase):
    __model__ = Revision
    __omit_fields__ = ['contenido', 'items']
revision_table = RevisionTable(DBSession)

class RevisionTableFiller(TableFiller):
    __model__ = Revision
    __omit_fields__ = ['contenido']
    buscado = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+ pklist +'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm(\'¿Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        '</form>'\
        '</div>'
        value = value + '</div>'
        return value
    
    def init(self,buscado):
        self.buscado = buscado

    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        revisions = DBSession.query(Revision).filter(Revision.id.contains(self.buscado)).all()
        return len(revisions), revisions 
    

revision_table_filler = RevisionTableFiller(DBSession)


class RevisionController(CrudRestController):
    model = Revision
    table = revision_table
    table_filler = revision_table_filler  

    def _before(self, *args, **kw):
        self.id_item = unicode(request.url.split("/")[-3][0:-2])
        self.version_item = unicode(request.url.split("/")[-3][-1])
        #self.id_fase = unicode(request.url.split("/")[-5])
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
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        d = super(RevisionController, self).get_all(*args, **kw)
        d["permiso_crear"] = False
        d["accion"] = "./buscar"
        item = DBSession.query(Item).filter(Item.id == self.id_item).filter(Item.version == self.version_item).one()
        lista = [revision.id for revision in item.revisiones]
        for revision in reversed(d["value_list"]):
            if revision["id"] not in lista:
                d["value_list"].remove(revision)
        return d



    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    @require(TienePermiso("manage"))
    def buscar(self, **kw):
        buscar_table_filler = RevisionTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "revision", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

