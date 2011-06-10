# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, LineaBase, TipoItem, Item, Fase
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context #templates
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso
from tg import request, flash
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func

from sprox.dojo.formbase import DojoEditableForm
from sprox.widgets.dojo import SproxDojoSelectShuttleField

from formencode.validators import NotEmpty

from saip.lib.func import consistencia_lb, proximo_id

errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class LineaBaseTable(TableBase):
    __model__ = LineaBase
    __omit_fields__ = ['fase']
linea_base_table = LineaBaseTable(DBSession)

class LineaBaseTableFiller(TableFiller):
    __model__ = LineaBase
    buscado = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        #if TienePermiso("manage").is_met(request.environ):#borrar despues
        #    value = value + '<div>'\
        #      '<form method="POST" action="'+pklist+'" class="button-to">'\
        #    '<input type="hidden" name="_method" value="DELETE" />'\
        #    '<input class="delete-button" onclick="return confirm(\'¿Está seguro?\');" value="delete" type="submit" '\
        #    'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        #'</form>'\
        '</div>'

        id_proyecto = pklist.split("-")[2]
        id_fase = pklist.split("-")[0] + "-" + pklist.split("-")[1]
        linea_base = DBSession.query(LineaBase).filter(LineaBase.id == pklist).one()
        cant_items = DBSession.query(Item).filter(Item.id_linea_base == pklist).count()
        if linea_base.cerrado:
            if TienePermiso("abrir linea base", id_proyecto = id_proyecto, id_fase = id_fase).is_met(request.environ):
                value = value + '<div><a class="abrir_link" href="abrir?pk_linea_base='+pklist+'" style="text-decoration:none">Abrir</a></div>'

        if not linea_base.cerrado:
            if TienePermiso("separar linea base", id_proyecto = id_proyecto, id_fase = id_fase).is_met(request.environ) and cant_items > 1:
                value = value + '<div><a class="dividir_link" href="dividir?pk_linea_base='+pklist+'" style="text-decoration:none">Dividir</a></div>'

            if linea_base.consistente:
                if TienePermiso("cerrar linea base", id_proyecto = id_proyecto, id_fase = id_fase).is_met(request.environ):
                    value = value + '<div><a class="cerrar_link" href="cerrar?pk_linea_base='+pklist+'" style="text-decoration:none">Cerrar</a></div>'

        value = value + '</div>'
        return value
    
    def init(self,buscado):
        self.buscado = buscado

    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        lineas_base = DBSession.query(LineaBase).filter(LineaBase.descripcion.contains(self.buscado)).all()
        return len(lineas_base), lineas_base 
    
linea_base_table_filler = LineaBaseTableFiller(DBSession)


class ItemsField(SproxDojoSelectShuttleField):
    
    def update_params(self, d):
        super(ItemsField, self).update_params(d)
        id_fase = unicode(request.url.split("/")[-3])
        ids_tipos_item = DBSession.query(TipoItem.id).filter(TipoItem.id_fase == id_fase)
        ids_item = DBSession.query(Item.id).filter(Item.id_tipo_item.in_(ids_tipos_item)).filter(Item.estado == u"Aprobado").filter(Item.id_linea_base == None).filter(Item.borrado == False).all()
        lista_ids = list()
        for id_item in ids_item:
            print lista_ids.append(id_item.id)
        a_eliminar = list()
        for opcion in reversed (d['options']):
            if not opcion[1] in lista_ids:
                d['options'].remove(opcion)
        print "OPCIONES"
        print d['options']

class AddLineaBase(AddRecordForm):
    __model__ = LineaBase
    items = ItemsField
    __hide_fields__ = ['fase', 'consistente', 'cerrado']
add_linea_base_form = AddLineaBase(DBSession)

class LineaBaseController(CrudRestController):
    model = LineaBase
    table = linea_base_table
    table_filler = linea_base_table_filler  
    new_form = add_linea_base_form

    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        super(LineaBaseController, self)._before(*args, **kw)
    
    def get_one(self, linea_base_id):
        tmpl_context.widget = linea_base_table
        linea_base = DBSession.query(LineaBase).get(linea_base_id)
        value = linea_base_table_filler.get_value(linea_base = linea_base)
        return dict(linea_base = linea_base, value = value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all_linea_base")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    #@require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        id_fase = unicode(request.url.split("/")[-3])
        d = super(LineaBaseController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("crear linea base").is_met(request.environ)
        d["permiso_unir"] = TienePermiso("unir lineas base").is_met(request.environ)
        d["model"] = "Lineas Base"
        cant = DBSession.query(LineaBase).filter(LineaBase.cerrado == False).filter(LineaBase.id_fase == id_fase).count()
        items = DBSession.query(Item).filter(Item.id_tipo_item.contains(id_fase)).filter(Item.borrado == False).filter(Item.id_linea_base == None).filter(Item.estado == u"Aprobado").all()
        
        aux = []
        for item in items:
            for item_2 in items:
                if item.id == item_2.id : 
                    if item.version > item_2.version: 
                        aux.append(item_2)
                    elif item.version < item_2.version :
                        aux.append(item)
        items = [i for i in items if i not in aux] 
        cant_items = len(items)
        if cant < 2:
            d["lineas_base"] = False
        else:
            d["lineas_base"] = True
        if cant_items == 0: d["permiso_crear"] = False
        d["accion"] = "./buscar"
        for linea_base in reversed(d["value_list"]):
            if not (linea_base["id_fase"] == self.id_fase):
                d["value_list"].remove(linea_base)
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    #@require(TienePermiso("manage"))
    def new(self, *args, **kw):
        id_fase = unicode(request.url.split("/")[-4])
        id_proyecto = id_fase.split("-")[1]
        if TienePermiso("crear lineas base", id_proyecto = id_proyecto, id_fase = id_fase).is_met(request.environ):
            tmpl_context.widget = self.new_form
            d = dict(value=kw, model=self.model.__name__)
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')


    @with_trailing_slash
    @expose('saip.templates.get_all_linea_base')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    #@require(TienePermiso("manage"))
    def buscar(self, **kw):
        id_fase = unicode(request.url.split("/")[-3])
        print id_fase
        buscar_table_filler = LineaBaseTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Lineas Base", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ).is_met(request.environ)
        d["permiso_unir"] = TienePermiso("manage").is_met(request.environ).is_met(request.environ)
        cant = DBSession.query(LineaBase).filter(LineaBase.cerrado == False).filter(LineaBase.id_fase == id_fase).count()
        print cant
        if cant < 2:
            d["lineas_base"] = False
        else:
            d["lineas_base"] = True
        return d

    @catch_errors(errors, error_handler=new)
    @registered_validate(error_handler=new)
    @expose('json')
    def post(self, **kw):
        id_fase = unicode(request.url.split("/")[-3])
        lista_ids_item = list()
        l = LineaBase()
        l.descripcion = kw['descripcion']
        ids_lineas_base = DBSession.query(LineaBase.id).filter(LineaBase.id_fase == id_fase).all()
        if ids_lineas_base:        
            proximo_id_linea_base = proximo_id(ids_lineas_base)
        else:
            proximo_id_linea_base = "LB1-" + id_fase
        l.id = proximo_id_linea_base
        l.fase = DBSession.query(Fase).filter(Fase.id == id_fase).one()
        l.cerrado = True
        l.consistente = True
        for item in kw['items']:
            lista_ids_item.append(item.split("/")[0]) #se saca la versión
        for id_item in lista_ids_item:
            item = DBSession.query(Item).filter(Item.id == id_item).one()
            l.items.append(item)

        DBSession.add(l)
        flash(u"Creación realizada de forma exitosa")
        raise redirect('./')

    @expose()
    #@require(TienePermiso("manage"))
    def abrir(self, **kw):
        id_fase = unicode(request.url.split("/")[-4])
        id_proyecto = id_fase.split("-")[1]
        if TienePermiso("abrir linea base", id_proyecto = id_proyecto, id_fase = id_fase).is_met(request.environ):
            pk = kw["pk_linea_base"]
            linea_base = DBSession.query(LineaBase).filter(LineaBase.id == pk).one()
            linea_base.cerrado = False
            flash(u"La línea base seleccionada se encuentra abierta")
            redirect('./')
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')

    @expose()
    #@require(TienePermiso("manage"))
    def cerrar(self, **kw):
        id_fase = unicode(request.url.split("/")[-4])
        id_proyecto = id_fase.split("-")[1]
        if TienePermiso("cerrar linea base", id_proyecto = id_proyecto, id_fase = id_fase).is_met(request.environ):
            pk = kw["pk_linea_base"]
            linea_base = DBSession.query(LineaBase).filter(LineaBase.id == pk).one()
            linea_base.cerrado = True
            flash(u"La línea base seleccionada se encuentra cerrada")
            redirect('./')
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')

    @with_trailing_slash
    @expose('saip.templates.unir_linea_base')
    #@expose('json')
    #@paginate('value_list', items_per_page = 7)
    #@require(TienePermiso("manage"))
    def unir(self, **kw):
        id_fase = unicode(request.url.split("/")[-4])
        id_proyecto = id_fase.split("-")[1]
        if TienePermiso("unir lineas base", id_proyecto = id_proyecto, id_fase = id_fase).is_met(request.environ):
            if "seleccionados" in kw:
                lb = LineaBase()
                lb.descripcion = kw["descripcion"]
                ids_lineas_base = DBSession.query(LineaBase.id).filter(LineaBase.id_fase == id_fase).all()
                proximo_id_linea_base = proximo_id(ids_lineas_base)
                lb.id = proximo_id_linea_base
                lb.fase = DBSession.query(Fase).filter(Fase.id == id_fase).one()
                lb.cerrado = False
                lb.consistente = False
                DBSession.add(lb)
                consistente = True
                for lb_seleccionada in kw["seleccionados"]:
                    items = DBSession.query(Item).filter(Item.id_linea_base == lb_seleccionada).all()
                    a_eliminar = DBSession.query(LineaBase).filter(LineaBase.id == lb_seleccionada).one()
                    DBSession.delete(a_eliminar)
                    for item in items:
                        item.linea_base = DBSession.query(LineaBase).filter(LineaBase.id == lb.id).one()
                consistencia_lb(lb)
                DBSession.add(lb)
                redirect('./..')
            lineas_base = DBSession.query(LineaBase.id).filter(LineaBase.id_fase == id_fase).filter(LineaBase.cerrado == False).all()
            
            d = dict(model = "Linea Base", accion = "./", lineas_base = lineas_base)
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')

    
    id_primera_lb = ""
    @with_trailing_slash
    @expose('saip.templates.dividir_linea_base')
    #@require(TienePermiso("manage"))
    def dividir(self, **kw):
        id_fase = unicode(request.url.split("/")[-3])
        id_proyecto = id_fase.split("-")[1]
        if TienePermiso("separar linea base", id_proyecto = id_proyecto, id_fase = id_fase).is_met(request.environ):
            if "pk_linea_base" in kw:
                self.id_primera_lb = kw["pk_linea_base"]
                items = DBSession.query(Item).filter(Item.id_linea_base == self.id_primera_lb)

            if "seleccionados" in kw:
                print kw["seleccionados"]
                lb = LineaBase()
                lb.descripcion = kw["descripcion"]
                ids_lineas_base = DBSession.query(LineaBase.id).filter(LineaBase.id_fase == id_fase).all()
                proximo_id_linea_base = proximo_id(ids_lineas_base)
                lb.id = proximo_id_linea_base
                lb.fase = DBSession.query(Fase).filter(Fase.id == id_fase).one()
                lb.cerrado = False
                lb.consistente = True
                DBSession.add(lb)
                
                if type(kw["seleccionados"]).__name__ == "unicode":
                    item = DBSession.query(Item).filter(Item.id == kw["seleccionados"]).one()
                    item.linea_base = DBSession.query(LineaBase).filter(LineaBase.id == lb.id).one()
                    consistencia_lb(lb)
                else:
                    for item_seleccionado in kw["seleccionados"]:
                        items = DBSession.query(Item).filter(Item.id == item_seleccionado).all()
                        for item in items:
                            item.linea_base = DBSession.query(LineaBase).filter(LineaBase.id == lb.id).one()
                primera_lb = DBSession.query(LineaBase).filter(LineaBase.id == self.id_primera_lb).one()
                consistencia_lb(primera_lb)
                redirect('./.')
            d = dict(items = items, model = "Lineas Base", accion = 'dividir')
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')
