# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de líneas base.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, LineaBase, TipoItem, Item, Fase
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from tg import request, flash
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func
from sprox.dojo.formbase import DojoEditableForm
from sprox.widgets.dojo import SproxDojoSelectShuttleField
from formencode.validators import NotEmpty
from saip.lib.func import consistencia_lb, proximo_id, estado_fase, es_huerfano
from saip.controllers.item_controller_listado import ItemControllerListado

errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

def UnificarItem(items):
    """Obtiene todos los ítems, cada uno con su mayor versión.
    """
    aux = list()
    for item in items:
            for item_2 in items:
                if item is not item_2  and item.id == item_2.id : 
                    if item.version > item_2.version and item_2 not in aux: 
                        aux.append(item_2) 
    items_a_mostrar = [i for i in items if i not in aux]
    return items_a_mostrar


class LineaBaseTable(TableBase):
    __model__ = LineaBase
    __omit_fields__ = ['fase', 'items', 'id_fase']
linea_base_table = LineaBaseTable(DBSession)

class LineaBaseTableFiller(TableFiller):
    """ Clase que se utiliza para llenar las tablas de líneas base en 
        administración.
    """
    __model__ = LineaBase
    buscado = ""
    id_fase = ""

    def init(self, buscado, id_fase):
        self.buscado = buscado
        self.id_fase = id_fase

    def __actions__(self, obj):
        """ Define las acciones posibles para cada línea base.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        id_proyecto = pklist.split("-")[2]
        linea_base = DBSession.query(LineaBase).filter(LineaBase.id == pklist)\
            .one()
        items = DBSession.query(Item).filter(Item.id_linea_base== pklist).all()
        items_a_mostrar = UnificarItem(items)
        cant_items = len(items_a_mostrar)
        consistencia_lb(linea_base)
        fase = DBSession.query(Fase).filter(Fase.id == self.id_fase).one()
        estado_fase(fase)
        if linea_base.cerrado:
            if TienePermiso("abrir linea base", id_proyecto = id_proyecto,
                            id_fase = self.id_fase).is_met(request.environ):
                value = value + '<div><a class="abrir_link" ' \
                'href="abrir?pk_linea_base='+pklist+'" ' \
                'style="text-decoration:none" TITLE = "Abrir"></a></div>'

        if not linea_base.cerrado:
            if TienePermiso("separar linea base", id_proyecto = id_proyecto,
                            id_fase = self.id_fase).is_met(request.environ) \
                            and cant_items > 1:
                value = value + '<div><a class="dividir_link" href=' \
                '"dividir?pk_linea_base='+pklist+'" style="text-decoration:' \
                'none" TITLE = "Dividir"></a></div>'

            if linea_base.consistente:
                if TienePermiso("cerrar linea base", id_proyecto = id_proyecto,
                               id_fase = self.id_fase).is_met(request.environ):
                    value = value + '<div><a class="cerrar_link" href=' \
                    '"cerrar?pk_linea_base='+pklist+'" style="text-' \
                    'decoration:none" TITLE = "Cerrar"></a></div>'
        if cant_items >= 1:
            value = value + '<div><a class="item_link" href=' \
                '"'+pklist+'/items" style="text-decoration:' \
                'none" TITLE = "Listar Items"></a></div>' 
        value = value + '</div>'
        return value

    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        """ Se utiliza para listar las líneas base que cumplan ciertas
            condiciones y ciertos permisos.
        """
        if TieneAlgunPermiso(tipo = "Fase", recurso = "Linea Base", id_fase = 
                            self.id_fase):
            lineas_base = DBSession.query(LineaBase).filter(LineaBase
                .descripcion.contains(self.buscado)).filter(LineaBase.id_fase 
                == self.id_fase).all()
            for lb in reversed(lineas_base):
                if not lb.items: 
                    lineas_base.remove(lb)
                    DBSession.delete(lb)
        else:
            lineas_base = list()
        return len(lineas_base), lineas_base 
    
linea_base_table_filler = LineaBaseTableFiller(DBSession)


class ItemsField(SproxDojoSelectShuttleField):
    """ Clase para obtener los posibles ítems para una nueva línea base.
    """
    template = 'saip.templates.selectshuttle'
    def update_params(self, d):
        """ @param d: diccionario con las opciones posibles de ítems.
            @return: d con los valores correctos de ítems posibles.
        """
        super(ItemsField, self).update_params(d)
        id_fase = unicode(request.url.split("/")[-3])
        ids_tipos_item = DBSession.query(TipoItem.id).filter(TipoItem.id_fase \
                        == id_fase)
        items = DBSession.query(Item).filter(Item.id_tipo_item \
            .in_(ids_tipos_item))\
            .filter(Item.id_linea_base == None).filter(Item.borrado == False) \
            .filter(Item.revisiones == None).all() 

        items_a_mostrar = UnificarItem(items)
        aux = list()
        for item in reversed(items_a_mostrar):
            if item.estado != u"Aprobado" or es_huerfano(item):
                items_a_mostrar.remove(item)
        for item in items_a_mostrar:
            aux.append(item.id + "/" + str(item.version)) 
        lista = [x for x in d['options'] if x[0] in aux]
        d['options'] = lista

class AddLineaBase(AddRecordForm):
    """ Define el formato de la tabla para agregar líneas base.
    """
    __model__ = LineaBase
    items = ItemsField
    __hide_fields__ = ['fase', 'consistente', 'cerrado']
    __dropdown_field_names__ = {'items':'codigo'} 
add_linea_base_form = AddLineaBase(DBSession)

class LineaBaseController(CrudRestController):
    """ Controlador del modelo Línea Base, módulo de gestión.
    """
    model = LineaBase
    table = linea_base_table
    table_filler = linea_base_table_filler  
    new_form = add_linea_base_form
    items = ItemControllerListado(DBSession)

    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        super(LineaBaseController, self)._before(*args, **kw)
    
    def get_one(self, linea_base_id):
        tmpl_context.widget = linea_base_table
        linea_base = DBSession.query(LineaBase).get(linea_base_id)
        value = linea_base_table_filler.get_value(linea_base = linea_base)
        d = dict(linea_base = linea_base, value = value, accion = "./buscar")
        return d

    @with_trailing_slash
    @expose("saip.templates.get_all_linea_base")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):
        """Lista las líneas base de acuerdo a lo establecido en
           L{linea_base_controller.LineaBaseTableFiller._do_get_provider_count_and_objs}.
        """
        linea_base_table_filler.init("",id_fase = self.id_fase)
        d = super(LineaBaseController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("crear linea base", id_fase = 
                                          self.id_fase).is_met(request.environ)
        d["permiso_unir"] = TienePermiso("unir lineas base", id_fase = 
                                         self.id_fase).is_met(request.environ)
        d["model"] = "Lineas Base"
        cant = DBSession.query(LineaBase).filter(LineaBase.cerrado == False) \
                .filter(LineaBase.id_fase == self.id_fase).count()
        items = DBSession.query(Item).filter(Item.id_tipo_item
                .contains(self.id_fase)).filter(Item.borrado == False) \
                .filter(Item.id_linea_base == None) \
                .filter(Item.estado == u"Aprobado").all()
        
        aux = []
        for item in items:
            for item_2 in items:
                if item.id == item_2.id : 
                    if item.version > item_2.version: 
                        aux.append(item_2)
                    elif item.version < item_2.version :
                        aux.append(item)
        items = [i for i in items if i not in aux and not es_huerfano(i)] 
        cant_items = len(items)
        if cant < 2:
            d["lineas_base"] = False
        else:
            d["lineas_base"] = True
        if cant_items == 0: d["permiso_crear"] = False
        d["direccion_anterior"] = "../.."
        d["accion"] = "./buscar"
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    def new(self, *args, **kw):
        """ Permite la creación de una nueva línea base para una determinada
            fase de un proyecto.
        """
        id_proyecto = self.id_fase.split("-")[1]
        if TienePermiso("crear linea base", id_proyecto = id_proyecto, id_fase 
                        = self.id_fase).is_met(request.environ):
            tmpl_context.widget = self.new_form
            d = dict(value=kw, model=self.model.__name__)
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", 
                  u"error")
            redirect('./')


    @with_trailing_slash
    @expose('saip.templates.get_all_linea_base')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        """ Lista las líneas base de acuerdo a un criterio de búsqueda
            introducido por el usuario.
        """
        buscar_table_filler = LineaBaseTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_fase)
        else:
            buscar_table_filler.init("", self.id_fase)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Lineas Base")
        d["accion"] = "./buscar" 
        d["permiso_crear"] = TienePermiso("crear linea base", id_fase = 
                                          self.id_fase).is_met(request.environ)
        d["permiso_unir"] = TienePermiso("unir lineas base", id_fase = 
                                          self.id_fase).is_met(request.environ)
        cant = DBSession.query(LineaBase).filter(LineaBase.cerrado == False) \
                .filter(LineaBase.id_fase == self.id_fase).count()
        if cant < 2:
            d["lineas_base"] = False
        else:
            d["lineas_base"] = True
        items = DBSession.query(Item).filter(Item.id_tipo_item
                .contains(self.id_fase)).filter(Item.borrado == False) \
                .filter(Item.id_linea_base == None).filter(Item.estado == 
                u"Aprobado").all()
        aux = []
        for item in items:
            for item_2 in items:
                if item.id == item_2.id : 
                    if item.version > item_2.version: 
                        aux.append(item_2)
                    elif item.version < item_2.version :
                        aux.append(item)
        items = [i for i in items if i not in aux and not es_huerfano(i)] 
        cant_items = len(items)
        if cant_items == 0: d["permiso_crear"] = False
        d["direccion_anterior"] = "../.."
        return d

    @catch_errors(errors, error_handler=new)
    @registered_validate(error_handler=new)
    @expose('json')
    def post(self, **kw):
        """ Registra la nueva línea base creada."""
        lista_ids_item = list()
        l = LineaBase()
        l.descripcion = kw['descripcion']
        ids_lineas_base = DBSession.query(LineaBase.id) \
                          .filter(LineaBase.id_fase == self.id_fase).all()
        if ids_lineas_base:        
            proximo_id_linea_base = proximo_id(ids_lineas_base)
        else:
            proximo_id_linea_base = "LB1-" + self.id_fase
        l.id = proximo_id_linea_base
        l.fase = DBSession.query(Fase).filter(Fase.id == self.id_fase).one()
        l.cerrado = True
        l.consistente = True
        for item in kw['items']:
            lista_ids_item.append((item.split("/")[0], item.split("/")[-1])) 
        for i in lista_ids_item:
            items = DBSession.query(Item).filter(Item.id == i[0]).all()
            for item in items:
                l.items.append(item)

        DBSession.add(l)
        flash(u"Creación realizada de forma exitosa")
        raise redirect('./')

    @expose()
    def abrir(self, **kw):
        """ Permite indicar que la línea se encuentra abierta."""
        id_proyecto = self.id_fase.split("-")[1]
        if TienePermiso("abrir linea base", id_proyecto = id_proyecto, id_fase 
                        = self.id_fase).is_met(request.environ):
            pk = kw["pk_linea_base"]
            linea_base = DBSession.query(LineaBase).filter(LineaBase.id == pk)\
                         .one()
            linea_base.cerrado = False
            flash(u"La línea base seleccionada se encuentra abierta")
            redirect('./')
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", 
                  u"error")
            redirect('./')

    @expose()
    def cerrar(self, **kw):
        """ Permite indicar que la línea base se encuentra cerrada."""
        id_proyecto = self.id_fase.split("-")[1]
        if TienePermiso("cerrar linea base", id_proyecto = id_proyecto, id_fase
                        = self.id_fase).is_met(request.environ):
            pk = kw["pk_linea_base"]
            linea_base = DBSession.query(LineaBase).filter(LineaBase.id == pk)\
                         .one()
            linea_base.cerrado = True
            flash(u"La línea base seleccionada se encuentra cerrada")
            redirect('./')
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", 
                  u"error")
            redirect('./')

    @without_trailing_slash
    @expose('saip.templates.unir_linea_base')
    def unir(self, **kw):
        """ Permite realizar la unión entre dos o más líneas base de manera
            que formen una sola.
        """
        id_proyecto = self.id_fase.split("-")[1]
        if TienePermiso("unir lineas base", id_proyecto = id_proyecto, id_fase 
                        = self.id_fase).is_met(request.environ):
            if "seleccionados" in kw:
                lb = LineaBase()
                lb.descripcion = kw["descripcion"]
                ids_lineas_base = DBSession.query(LineaBase.id) \
                                  .filter(LineaBase.id_fase == self.id_fase) \
                                  .all()
                proximo_id_linea_base = proximo_id(ids_lineas_base)
                lb.id = proximo_id_linea_base
                lb.fase = DBSession.query(Fase) \
                          .filter(Fase.id == self.id_fase).one()
                lb.cerrado = False
                lb.consistente = False
                DBSession.add(lb)
                consistente = True
                for lb_seleccionada in kw["seleccionados"]:
                    items = DBSession.query(Item).filter(Item.id_linea_base == 
                                                  lb_seleccionada).all()
                    a_eliminar = DBSession.query(LineaBase) \
                                 .filter(LineaBase.id == lb_seleccionada).one()
                    DBSession.delete(a_eliminar)
                    for item in items:
                        item.linea_base = DBSession.query(LineaBase) \
                                          .filter(LineaBase.id == lb.id).one()
                consistencia_lb(lb)
                DBSession.add(lb)
                
                redirect('./')
            lineas_base = DBSession.query(LineaBase.id) \
                          .filter(LineaBase.id_fase == self.id_fase) \
                          .filter(LineaBase.cerrado == False).all()
            
            d = dict(model = "Linea Base", accion = "./")
            d["lineas_base"] = lineas_base
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", 
                  u"error")
            redirect('./')

    
    id_primera_lb = ""
    @with_trailing_slash
    @expose('saip.templates.dividir_linea_base')
    def dividir(self, **kw):
        """ Permite formar una línea base a partir de dos o más líneas base
            existentes previamente.
        """
        id_proyecto = self.id_fase.split("-")[1]
        if TienePermiso("separar linea base", id_proyecto = id_proyecto, 
                        id_fase = self.id_fase).is_met(request.environ):
            if "pk_linea_base" in kw:
                self.id_primera_lb = kw["pk_linea_base"]
                items = DBSession.query(Item).filter(Item.id_linea_base == 
                                                     self.id_primera_lb)
                items_a_mostrar = UnificarItem(items)

            if "seleccionados" in kw:
                lb = LineaBase()
                lb.descripcion = kw["descripcion"]
                ids_lineas_base = DBSession.query(LineaBase.id) \
                                  .filter(LineaBase.id_fase == self.id_fase) \
                                  .all()
                proximo_id_linea_base = proximo_id(ids_lineas_base)
                lb.id = proximo_id_linea_base
                lb.fase = DBSession.query(Fase) \
                          .filter(Fase.id == self.id_fase).one()
                lb.cerrado = False
                lb.consistente = True
                DBSession.add(lb)
                
                if type(kw["seleccionados"]).__name__ == "unicode":
                    item = DBSession.query(Item) \
                           .filter(Item.id == kw["seleccionados"]).all()
                    for aux in item:
                        aux.linea_base = DBSession.query(LineaBase) \
                                      .filter(LineaBase.id == lb.id).one()
                    consistencia_lb(lb)
                else:
                    for item_seleccionado in kw["seleccionados"]:
                        items = DBSession.query(Item) \
                                .filter(Item.id == item_seleccionado).all()
                        for item in items:
                            item.linea_base = DBSession.query(LineaBase) \
                                              .filter(LineaBase.id == lb.id) \
                                              .one()
                primera_lb = DBSession.query(LineaBase) \
                             .filter(LineaBase.id == self.id_primera_lb).one()
                consistencia_lb(primera_lb)
                redirect('./.')
            d = dict(items = items_a_mostrar, model = "Lineas Base")
            d["accion"] = "dividir"
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", 
                  u"error")
            redirect('./')
