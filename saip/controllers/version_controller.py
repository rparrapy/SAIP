# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de versiones anteriores de un ítem.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, Item, TipoItem, Caracteristica, Relacion
from saip.model import Revision
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
from saip.controllers.relacion_controller_listado import \
RelacionControllerListado
from saip.controllers.archivo_controller_listado import \
ArchivoControllerListado
from sqlalchemy import func, desc, or_, and_
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
                    'archivos', 'borrado', 'relaciones_a', 'relaciones_b', \
                    'anexo', 'linea_base', 'estado', 'revisiones']
item_table = ItemTable(DBSession)

class ItemTableFiller(TableFiller):
    """
    Clase que se utiliza para llenar las tablas.
    """
    __model__ = Item
    buscado = ""
    id_item = ""
    version = ""

    def tipo_item(self, obj):
        return obj.tipo_item.nombre

    def __actions__(self, obj):
        """
        Define las acciones posibles para cada ítem.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        id_item = pklist.split("/")[0]
        version_item = pklist.split("/")[1]
        pklist = id_item+ "-" + version_item
        item = DBSession.query(Item).filter(Item.id == id_item) \
                .filter(Item.version == version_item).one()
        value = '<div>'
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True
        if TienePermiso("reversionar item", id_fase = item.tipo_item.fase.id) \
                        .is_met(request.environ) and not bloqueado:
            value = value + '<div><a class="reversion_link" href=' \
             '"revertir?item='+pklist+'" style="text-decoration:none" TITLE ='\
             ' "Revertir"></a>'\
              '</div>'
        value = value + '<div><a class="relacion_link" href="'+pklist+ \
            '/relaciones" style="text-decoration:none" TITLE =' \
            '"Relaciones"></a></div>'
        value = value + '<div><a class="archivo_link" href="'+pklist+ \
         '/archivos" style="text-decoration:none" TITLE = "Archivos"></a>'\
         '</div>'
        if item.anexo != "{}":
            value = value + '<div><a class="caracteristica_link" href=' \
                '"listar_caracteristicas?pk_item='+pklist+ \
                '" style="text-decoration:none" TITLE =' \
                ' "Ver caracteristicas"></a></div>'
        value = value + '</div>'
        return value
    
    def init(self, buscado, id_item, version):
        self.buscado = buscado
        self.id_item = id_item
        self.version = version

    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se utiliza para listar solo las versiones anteriores 
        que cumplan ciertas condiciones y de acuerdo a ciertos permisos.
        """
        items = DBSession.query(Item).filter(Item.id == \
            self.id_item).filter(Item.borrado == False) \
            .order_by(desc(Item.version)).all()
        items = items[1:]
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
        return len(items), items 
item_table_filler = ItemTableFiller(DBSession)


class VersionController(CrudRestController):
    """ Controlador de versiones anteriores de un ítem. """
    relaciones = RelacionControllerListado(DBSession)
    archivos = ArchivoControllerListado(DBSession)
    model = Item
    table = item_table
    table_filler = item_table_filler  

    def _before(self, *args, **kw):
        self.id_item = unicode("-".join(request.url.split("/")[-3] \
                    .split("-")[0:-1]))
        self.version_item = unicode(request.url.split("/")[-3].split("-")[-1])
        super(VersionController, self)._before(*args, **kw)
    
    def get_one(self, item_id):
        tmpl_context.widget = item_table
        item = DBSession.query(Item).get(item_id)
        value = item_table_filler.get_value(item = item)
        return dict(item = item, value = value, accion = "./buscar")


    def crear_version_sin_relaciones(self, it, id_item):
        """
        Crea una nueva versión de un ítem dado sin sus relaciones.

        @param it: Item a partir del cual se creará una nueva versión.
        @type it: L{Item}
        @param id_item: Id del ítem a reversionar.
        @type id_item: String
        """
        actual = DBSession.query(Item).filter(Item.id == id_item) \
            .order_by(desc(Item.version)).first()
        nueva_version = Item()
        nueva_version.id = it.id
        nueva_version.codigo = it.codigo
        nueva_version.version = actual.version + 1
        nueva_version.nombre = it.nombre
        nueva_version.descripcion = it.descripcion
        nueva_version.estado = u"En desarrollo"
        nueva_version.observaciones = it.observaciones
        nueva_version.prioridad = it.prioridad
        nueva_version.complejidad = it.complejidad
        nueva_version.borrado = it.borrado
        nueva_version.anexo = it.anexo
        nueva_version.tipo_item = it.tipo_item
        nueva_version.revisiones = actual.revisiones
        nueva_version.linea_base = actual.linea_base
        nueva_version.archivos = it.archivos
        return nueva_version    

    def crear_version(self, it, borrado = None):
        """
        Crea una nueva versión de un ítem dado. Permite también borrar
        una relación de esta nueva versión si se especifica.

        @param it: Item a partir del cual se creará una nueva versión.
        @type it: L{Item}
        @param borrado: Relación a eliminar.
        @type borrado: L{Relacion}
        """
        nueva_version = Item()
        nueva_version.id = it.id
        nueva_version.codigo = it.codigo
        nueva_version.version = it.version + 1
        nueva_version.nombre = it.nombre
        nueva_version.descripcion = it.descripcion
        nueva_version.estado = it.estado
        nueva_version.observaciones = it.observaciones
        nueva_version.prioridad = it.prioridad
        nueva_version.complejidad = it.complejidad
        nueva_version.borrado = it.borrado
        nueva_version.anexo = it.anexo
        nueva_version.revisiones = it.revisiones
        nueva_version.tipo_item = it.tipo_item
        nueva_version.linea_base = it.linea_base
        nueva_version.archivos = it.archivos
        for relacion in relaciones_a_actualizadas(it.relaciones_a):
            if not relacion == borrado:
                aux = relacion.id.split("+")
                r = Relacion()
                r.id = "-".join(aux[0].split("-")[0:-1]) + "-" + \
                        unicode(nueva_version.version) + "+" +aux[1] 
                r.item_1 = nueva_version
                r.item_2 = relacion.item_2
        for relacion in relaciones_b_actualizadas(it.relaciones_b):
            if not relacion == borrado:
                r = Relacion()
                aux = relacion.id.split("+")
                r.id = aux[0] + "+" + "-".join(aux[1].split("-")[0:-1]) + \
                        "-" + unicode(nueva_version.version)
                r.item_1 = relacion.item_1
                r.item_2 = nueva_version
        return nueva_version


    def crear_relacion(self, item_1, item_2, nueva_version):
        """
        Crea una relación entre dos ítems.

        @param item_1: Item antecesor/padre de la relación a ser creada.
        @type item_1: L{Item}
        @param item_2: Item sucesor/hijo de la relación a ser creada.
        @type item_2: L{Item}
        @return: True si la relación se creó exitosamente, 
                 False en caso contrario.
        @rtype: Bool
        """
        r = Relacion()
        r.id = "RE-" + item_1.id + "-" + unicode(item_1.version) + "+" + \
                item_2.id + "-" + unicode(item_2.version)
        r.item_1 = item_1
        r.item_2 = item_2
        a = forma_ciclo(r.item_1)
        DBSession.add(r)      
        if a:
            if nueva_version == r.item_1:
                DBSession.delete(r.item_2)
            DBSession.delete(r)
            return False
        else:
            return True        

    def crear_revision(self, item, msg):
        """
        Crea una nueva revisión y la agrega a un item dado.
        
        @param item: Item al cual se agregará la revisión
        @type item: L{Item}
        @param msg: Mensaje de la revisión
        @type msg: String
        """
        rv = Revision()
        ids_revisiones = DBSession.query(Revision.id) \
                .filter(Revision.id_item == item.id).all()
        if ids_revisiones:
            proximo_id_revision = proximo_id(ids_revisiones)
        else:
            proximo_id_revision = "RV1-" + item.id
        rv.id = proximo_id_revision
        rv.item = item
        rv.descripcion = msg
        DBSession.add(rv)        

    @without_trailing_slash
    @expose()
    def revertir(self, *args, **kw):
        """
        Revierte un ítem a una versión especificada en los parámetros.
        """
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
                .filter(Item.version == self.version_item).one()
        if TienePermiso("reversionar item", id_fase = item.tipo_item.fase.id) \
                .is_met(request.environ):
            id_item = unicode("-".join(kw["item"] \
                    .split("-")[0:-1]))
            version_item = unicode(kw["item"].split("-")[-1])
            it = DBSession.query(Item).filter(Item.id == id_item) \
                .filter(Item.version == version_item).one()
            it_actual = DBSession.query(Item).filter(Item.id == id_item) \
                    .order_by(desc(Item.version)).first()
            nueva_version = self.crear_version_sin_relaciones(it, id_item)
            ruta = './../../' + nueva_version.id + '-' + \
                unicode(nueva_version.version) + '/' + 'versiones/'
            hijos_ant = list()
            for relacion in relaciones_a_actualizadas(it_actual.relaciones_a):
                hijos_ant.append(relacion.id_item_2)
            relaciones = relaciones_a_recuperar(it.relaciones_a) + \
                relaciones_b_recuperar(it.relaciones_b)
            huerfano = True
            for relacion in relaciones:
                aux = opuesto(relacion,it)
                aux_act = DBSession.query(Item).filter(Item.id == aux.id) \
                    .order_by(desc(Item.version)).first()
                if not aux.borrado:
                    band = False
                    band_p = False
                    if aux.tipo_item.fase.orden < it.tipo_item.fase.orden:
                        item_1 = aux_act
                        item_2 = nueva_version
                        if aux.linea_base:
                            if not aux_act.borrado and \
                                    aux_act.linea_base.consistente and \
                                    aux_act.linea_base.cerrado: 
                                band = True
                                band_p = True
                    elif aux.tipo_item.fase.orden == it.tipo_item.fase.orden: 
                        if aux == relacion.item_1:
                            if aux.estado == u"Aprobado" and \
                               not aux.revisiones:
                                item_1 = aux_act
                                item_2 = nueva_version
                        else:
                            item_1 = nueva_version
                            item_2 = self.crear_version(aux_act)                                   
                        if not aux_act.borrado: band = True
                    else:
                        item_1 = nueva_version
                        item_2 = self.crear_version(aux_act)  
                        if it_actual.linea_base:
                            band = True
                    if band:
                        exito = self.crear_relacion(item_1, item_2, \
                                nueva_version)
                        if not exito:
                            msg = u"No se pudo recuperar la relación " + \
                                  relacion.id
                            self.crear_revision(nueva_version, msg)
                        elif band_p: 
                            huerfano = False
                    if not band:
                        msg = u"No se pudo recuperar la relación " + relacion.id
                        self.crear_revision(nueva_version, msg)                                        
                else:
                    msg = u"No se pudo recuperar la relación " + relacion.id
                    self.crear_revision(nueva_version, msg)        
                            
            for h in hijos_ant:
                    h_act = DBSession.query(Item).filter(Item.id == h) \
                    .order_by(desc(Item.version)).first()
                    msg = u"Item huerfano"
                    if h_act.tipo_item.fase != it.tipo_item.fase:
                        if es_huerfano(h_act) and \
                           (h_act.estado == u"Aprobado" or \
                            h_act.linea_base):
                            h_act.estado = u"En desarrollo"
                            self.crear_revision(h_act, msg)                                        
                
                                
            
            if huerfano and it.tipo_item.fase.orden != 1:
                msg = u"Item huerfano"
                if nueva_version.linea_base:
                    self.crear_revision(nueva_version, msg)
            DBSession.add(nueva_version)
            transaction.commit()
            raise redirect(ruta)
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            redirect('./')            



    @with_trailing_slash
    @expose("saip.templates.get_all_comun")
    @expose('json')
    @paginate('value_list', items_per_page=3)
    def get_all(self, *args, **kw):
        """
        Lista las versiones de un ítem de acuerdo a condiciones establecidas 
        en el L{version_controller.ItemTableFiller
        ._do_get_provider_count_and_objs}.
        """    
        item_table_filler.init("", self.id_item, self.version_item)      
        d = super(VersionController, self).get_all(*args, **kw)
        d["accion"] = "./buscar" 
        d["model"] = "versiones"
        d["direccion_anterior"] = "../.."                  
        return d
   

    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @expose('json')
    @paginate('value_list', items_per_page = 3)
    def buscar(self, **kw):
        """
        Lista las versiones de un ítem de acuerdo a un criterio de búsqueda 
        introducido por el usuario.
        """
        buscar_table_filler = ItemTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_item, \
                    self.version_item)
        else:
            buscar_table_filler.init("", self.id_item, self.version_item)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "versiones", accion = "./buscar")
        d["direccion_anterior"] = "../.."
        return d

    @expose('saip.templates.get_all_caracteristicas_item')
    @paginate('value_list', items_per_page=7)
    def listar_caracteristicas(self, **kw):
        """
        Despliega el valor de las características propias del tipo de ítem de
        una versión de un ítem dado, siempre que el ítem no sea 
        del tipo 'Default'
        """
        id_fase = unicode(request.url.split("/")[-5])
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
    
