# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Relacion, TipoRelacion, Caracteristica
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context #templates
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from saip.lib.auth import TienePermiso
from tg import request, flash
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func, _or
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class RelacionTable(TableBase):
    __model__ = Relacion
    __omit_fields__ = ['id_item_1', 'id_item_2']
    __xml_fields__ = ['fase']
relacion_table = RelacionTable(DBSession)

class RelacionTableFiller(TableFiller):
    __model__ = Relacion
    buscado = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to">'\
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
        relacions = DBSession.query(Relacion).filter(Relacion.id.contains(self.buscado)).all()
        return len(relacions), relacions 
    
    def fase(self, obj):
        fase = unicode(obj.item_2.tipo_item.id_fase)
        return fase

relacion_table_filler = RelacionTableFiller(DBSession)

class AddRelacion(AddRecordForm):
    __model__ = Relacion
    __omit_fields__ = ['id_item_1', 'id_item_2']
add_relacion_form = AddRelacion(DBSession)


class RelacionController(CrudRestController):
    fases = FaseController(DBSession)
    model = Relacion
    table = relacion_table
    table_filler = relacion_table_filler  
    edit_filler = relacion_edit_filler
    edit_form = edit_relacion_form
    new_form = add_relacion_form

    def _before(self, *args, **kw):
        self.id_item = unicode(request.url.split("/")[-3])
        super(RelacionController, self)._before(*args, **kw)
    
    def get_one(self, relacion_id):
        tmpl_context.widget = relacion_table
        relacion = DBSession.query(Relacion).get(relacion_id)
        value = relacion_table_filler.get_value(relacion = relacion)
        return dict(relacion = relacion, value = value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all_relacion")
    @expose('json')
    @paginate('value_list', relacions_per_page=7)
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        d = super(RelacionController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        for relacion in reversed(d["value_list"]):
            if not (relacion["item_1"] == self.id_fase or relacion["item_2"] == self.id_fase)  :
                d["value_list"].remove(relacion)
        return d

    @without_trailing_slash
    @expose('saip.templates.new_relacion')
    @require(TienePermiso("manage"))
    def new(self, *args, **kw):
        super(RelacionController, self).new(*args, **kw)
    
    @without_trailing_slash
    @require(TienePermiso("manage"))
    @expose('saip.templates.edit_relacion')
    #@expose('tgext.crud.templates.edit')
    #def edit(self, *args, **kw):
    #    """Display a page to edit the record."""
    #    id_tipo_relacion = unicode(request.url.split("/")[-2])
    #    print "id_tipo_relacion"
    #    print id_tipo_relacion
    #    tmpl_context.widget = self.edit_form
    #    pks = self.provider.get_primary_fields(self.model)
    #    kw = {}
    #    for i, pk in  enumerate(pks):
    #        kw[pk] = args[i]
    #    value = self.edit_filler.get_value(kw)
    #    value['_method'] = 'PUT'
    #    print "kw"
    #    print kw
    #    caracteristicas = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_relacion == id_tipo_relacion)
    #    return dict(value=value, model=self.model.__name__, pk_count=len(pks), caracteristicas = caracteristicas, tipo_relacion = tipo_relacion)
    def edit(self, *args, **kw):
        d = super(RelacionController, self).edit(*args, **kw)
        id_relacion = unicode(request.url.split("/")[-2])
        id_relacion = id_relacion.split("-")
        id_tipo_relacion = id_relacion[1] + "-" + id_relacion[2] + "-" + id_relacion[3]
        caracteristicas = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_relacion == id_tipo_relacion).all()
        d['caracteristicas'] = caracteristicas
        print "caract"
        print caracteristicas
        d['tipo_relacion'] = id_tipo_relacion
        return d

    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', relacions_per_page = 7)
    @require(TienePermiso("manage"))
    def buscar(self, **kw):
        buscar_table_filler = RelacionTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "relacion", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

    #@catch_errors(errors, error_handler=new)
    @expose('json')
    #@registered_validate(error_handler=new)
    def post(self, **kw):
        print kw
        i = Relacion()
        i.descripcion = kw['descripcion']
        i.nombre = kw['nombre']
        i.estado = 'En desarrollo'
        i.observaciones = kw['observaciones']
        i.prioridad = kw['prioridad']
        i.complejidad = kw['complejidad']
        nombre_caract = DBSession.query(Caracteristica.nombre).filter(Caracteristica.id_tipo_relacion == kw['tipo_relacion']).all()
        anexo = dict()
        for nom_car in nombre_caract:
            anexo[nom_car.nombre] = kw[nom_car.nombre]
        i.anexo = json.dumps(anexo)
        maximo_id_relacion = DBSession.query(func.max(Relacion.id)).scalar()
        print maximo_id_relacion
        if not maximo_id_relacion:
            maximo_id_relacion = "IT0-" + kw["tipo_relacion"]
        relacion_maximo = maximo_id_relacion.split("-")[0]
        nro_maximo = int(relacion_maximo[2:])
        i.id = "IT" + str(nro_maximo + 1) + "-" + kw["tipo_relacion"]
        i.tipo_relacion = DBSession.query(TipoRelacion).filter(TipoRelacion.id == kw["tipo_relacion"]).one()
        DBSession.add(i)
        print "guarda"
        #flash("Creación realizada de forma exitosa")
        raise redirect('./')
