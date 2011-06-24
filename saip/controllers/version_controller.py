# -*- coding: utf-8 -*-
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
    __model__ = Item
    __omit_fields__ = ['id_tipo_item', 'id_fase', 'id_linea_base', \
                    'archivos', 'borrado', 'relaciones_a', 'relaciones_b', \
                    'anexo', 'linea_base', 'estado']
item_table = ItemTable(DBSession)

class ItemTableFiller(TableFiller):
    __model__ = Item
    buscado = ""
    id_item = ""
    version = ""
    def __actions__(self, obj):
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
            '/ver_relaciones" style="text-decoration:none" TITLE =' \
            '"Relaciones"></a></div>'
        value = value + '<div><a class="archivo_link" href="'+pklist+ \
         '/ver_archivos" style="text-decoration:none" TITLE = "Archivos"></a>'\
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

    def _do_get_provider_count_and_objs(self, buscado = "", id_item = "", **kw):
        items = DBSession.query(Item).filter(Item.id == \
            self.id_item).filter(Item.borrado == False) \
            .order_by(desc(Item.version)).all()
        items = items[1:]
        for item in reversed(items):
            buscado = self.buscado in item.id or \
                      self.buscado in item.nombre or \
                      self.buscado in str(version) or \
                      self.buscado in item.descripcion or \
                      self.buscado in item.estado or \
                      self.buscado in item.observaciones or \
                      self.buscado in str(item.complejidad) or \
                      self.buscado in str(item.prioridad) or \
                      self.buscado in item.tipo_item.nombre or \
                      self.buscado in item.linea_base

            if not buscado: items.remove(item)
        return len(items), items 
item_table_filler = ItemTableFiller(DBSession)


class VersionController(CrudRestController):
    ver_relaciones = RelacionControllerListado(DBSession)
    ver_archivos = ArchivoControllerListado(DBSession)
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


    def crear_relacion(self, item_1, item_2):
        r = Relacion()
        r.id = "RE-" + item_1.id + "-" + unicode(item_1.version) + "+" + \
                item_2.id + "-" + unicode(item_2.version)
        r.item_1 = item_1
        r.item_2 = item_2      
        if forma_ciclo(r.item_1):
            DBSession.delete(r)
            return False
        else:
            DBSession.add(r)
            return True        

    def crear_revision(self, item, msg):
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
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
                .filter(Item.version == self.version_item).one()
        if TienePermiso("reversionar item", id_fase = item.tipo_item.fase.id) \
                .is_met(request.environ):
            id_item = kw["item"][0:-2]
            version_item = kw["item"][-1]
            it = DBSession.query(Item).filter(Item.id == id_item) \
                .filter(Item.version == version_item).one()
            nueva_version = self.crear_version_sin_relaciones(it, id_item)
            ruta = './../../' + nueva_version.id + '-' + \
                unicode(nueva_version.version) + '/' + 'versiones/'
            relaciones = relaciones_a_recuperar(it.relaciones_a) + \
                relaciones_b_recuperar(it.relaciones_b)
            huerfano = True
            for relacion in relaciones:
                print relacion.id
                aux = opuesto(relacion,it)
                aux_act = DBSession.query(Item).filter(Item.id == aux.id) \
                    .order_by(desc(Item.version)).first()
                band = False
                band_p = False
                if aux.tipo_item.fase < it.tipo_item.fase:
                    item_1 = aux_act
                    item_2 = nueva_version
                    if aux.linea_base:
                        if not aux_act.borrado and \
                                aux_act.linea_base.consistente and \
                                aux_act.linea_base.cerrado: 
                            band = True
                            band_p = True
                elif aux.tipo_item.fase == it.tipo_item.fase: 
                    if aux == relacion.item_1:
                        item_1 = aux_act
                        item_2 = nueva_version
                    else:
                        item_1 = nueva_version
                        item_2 = self.crear_version(aux_act)                                   
                    if not aux_act.borrado: band = True
                else:
                    item_1 = nueva_version
                    item_2 = self.crear_version(aux_act)  
                    if it.linea_base:
                        if not it.borrado and it.linea_base.consistente and \
                            it.linea_base.cerrado: band = True
                if band:
                    print "ENTRO"
                    exito = self.crear_relacion(item_1, item_2)
                    if not exito:
                        msg = u"No se pudo recuperar la relación" + relacion.id
                        self.crear_revision(nueva_version, msg)
                    elif band_p: 
                        huerfano = False
            if huerfano:
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
    
