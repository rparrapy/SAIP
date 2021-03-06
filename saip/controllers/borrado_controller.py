# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de ítems borrados.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, Item, TipoItem, Caracteristica, Relacion
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
from saip.controllers.archivo_controller_listado import \
ArchivoControllerListado
from sqlalchemy import func, desc, or_
import transaction
import json
import os
import pydot
from saip.lib.func import *
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class ItemTable(TableBase):
    """ Define el formato de la tabla"""
    __model__ = Item
    __omit_fields__ = ['id', 'id_tipo_item', 'id_fase', 'id_linea_base', \
                      'archivos','borrado', 'relaciones_a', 'relaciones_b', \
                      'anexo','revisiones', 'linea_base']
item_table = ItemTable(DBSession)

class ItemTableFiller(TableFiller):
    """ Clase que se utiliza para llenar las tablas de ítems borrados a ser
        potencialmente recuperados.
    """
    __model__ = Item
    buscado = ""
    id_fase = ""

    def tipo_item(self, obj):
        return obj.tipo_item.nombre

    def __actions__(self, obj):
        """ Define las acciones posibles para cada ítem borrado.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        id_item = pklist.split("/")[0] 
        version_item = pklist.split("/")[1]
        pklist = id_item+ "-" + version_item
        item = DBSession.query(Item).filter(Item.id == id_item) \
                .filter(Item.version == version_item).one()
        value = '<div>'
        if TienePermiso("recuperar item", id_fase = self.id_fase) \
                        .is_met(request.environ):
            value = value + '<div><a class="revivir_link"' \
                    ' href="revivir?id_item='+pklist+ \
                    '" style="text-decoration:none" TITLE = "Revivir"></a>'\
                    '</div>'
        value = value + '<div><a class="archivo_link" href="'+pklist+ \
                '/archivos" style="text-decoration:none" TITLE =' \
                ' "Archivos"></a>'\
                '</div>'
        if item.anexo != "{}":
            value = value + '<div><a class="caracteristica_link" href=' \
                '"listar_caracteristicas?pk_item='+pklist+ \
                '" style="text-decoration:none" TITLE =' \
                ' "Ver caracteristicas"></a></div>'
        value = value + '</div>'
        return value
    
    def init(self, buscado, id_fase):
        self.buscado = buscado
        self.id_fase = id_fase
    def _do_get_provider_count_and_objs(self, buscado = "", \
                                        id_fase = "", **kw):
        """ Se utiliza para listar los ítems borrados que cumplan ciertas
            condiciones y ciertos permisos.
        """
        items = DBSession.query(Item).filter(Item \
                .id_tipo_item.contains(self.id_fase)).filter(Item.borrado == \
                True).all()

        for item in reversed(items):
            buscado = self.buscado in item.id or \
                      self.buscado in item.nombre or \
                      self.buscado in str(item.version) or \
                      self.buscado in item.descripcion or \
                      self.buscado in item.estado or \
                      self.buscado in item.observaciones or \
                      self.buscado in str(item.complejidad) or \
                      self.buscado in str(item.prioridad) or \
                      self.buscado in item.tipo_item.nombre
            if item.linea_base:
                buscado = buscado or self.buscado in item.linea_base
            if not buscado: items.remove(item)
        a_borrar = list()
        for item_1 in items:
            for item_2 in items:
                if item_1.id == item_2.id and item_1.version > item_2.version:
                    a_borrar.append(item_2)
                elif item_1.version < item_2.version:
                    a_borrar.append(item_1)

        items_aux = [i for i in items if i not in a_borrar]
        items = items_aux                    
        return len(items), items 
item_table_filler = ItemTableFiller(DBSession)


class BorradoController(CrudRestController):
    """ Controlador del modelo Item para los que se encuentran borrados.
    """
    model = Item
    table = item_table
    table_filler = item_table_filler
    archivos = ArchivoControllerListado(DBSession)

    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-4])
        super(BorradoController, self)._before(*args, **kw)
    
    def get_one(self, item_id):
        tmpl_context.widget = item_table
        item = DBSession.query(Item).get(item_id)
        value = item_table_filler.get_value(item = item)
        return dict(item = item, value = value, accion = "./buscar")

    @without_trailing_slash
    @expose()
    def revivir(self, *args, **kw):
        """Permite realizar la recuperación de ítems borrados con sus
            respectivos atributos y las relaciones que sea posible recuperar.
        """
        if TienePermiso("recuperar item", id_fase = self.id_fase):
            pk = kw["id_item"]
            pk_id = unicode(pk.split("-")[0] + "-" + pk.split("-")[1] + "-" + \
                    pk.split("-")[2] + "-" + pk.split("-")[3])
            pk_version = pk.split("-")[4]
            it = DBSession.query(Item).filter(Item.id == pk_id) \
                    .filter(Item.version == pk_version).one()
            it.estado = u"En desarrollo"
            it.borrado = False
            it.linea_base = None
            items = DBSession.query(Item).filter(Item.id == pk_id).all()
            for item in items:
                item.borrado = False
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")            
        raise redirect('./')


    @with_trailing_slash
    @expose("saip.templates.get_all_comun")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):
        """Lista los ítems borrados de acuerdo a lo establecido en
           L{borrado_controller.ItemTableFiller._do_get_provider_count_and_objs}.
        """
        item_table_filler.init("",self.id_fase)      
        d = super(BorradoController, self).get_all(*args, **kw)
        d["accion"] = "./buscar"
        d["model"] = "borrados"
        d["direccion_anterior"] = "../"
        return d
   

    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        """ Lista los ítems borrados de acuerdo a un criterio de búsqueda
            introducido por el usuario.
        """
        buscar_table_filler = ItemTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_fase)
        else:
            buscar_table_filler.init("", self.id_fase)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "borrados", accion = \
                "./buscar")
        d["direccion_anterior"] = "../"
        return d

    @expose('saip.templates.get_all_caracteristicas_item')
    @paginate('value_list', items_per_page=7)
    def listar_caracteristicas(self, **kw):
        """ Permite al usuario visualizar las características de un ítem
            borrado.
        """
        id_fase = unicode(request.url.split("/")[-4])
        if TieneAlgunPermiso(tipo = u"Fase", recurso = u"Item", id_fase = \
                            id_fase).is_met(request.environ):
            pk = kw["pk_item"]
            pk_id = unicode(pk.split("-")[0] + "-" + pk.split("-")[1] + "-" + \
                    pk.split("-")[2] + "-" + pk.split("-")[3])
            pk_version = pk.split("-")[4]
            anexo = DBSession.query(Item.anexo).filter(Item.id == pk_id) \
                    .filter(Item.version == pk_version).one()
            anexo = json.loads(anexo.anexo)
            d = dict()
            d['anexo'] = anexo
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            redirect('./')
   
