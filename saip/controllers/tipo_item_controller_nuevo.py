# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash, paginate
from tg import expose, flash
from saip.model import DBSession
from saip.model.app import TipoItem
from tg import request, redirect
from tg import tmpl_context #templates
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
import datetime
from sqlalchemy import func
from saip.lib.auth import TienePermiso
from saip.model.app import Proyecto, TipoItem, Fase, Caracteristica
from saip.lib.func import proximo_id
from sqlalchemy import or_

class TipoItemTable(TableBase):
	__model__ = TipoItem
	__omit_fields__ = ['id', 'fase', 'id_fase', 'items', 'caracteristicas']
tipo_item_table = TipoItemTable(DBSession)


class TipoItemTableFiller(TableFiller):
    __model__ = TipoItem
    buscado = ""
    id_fase = ""
    id_fase_que_importa = ""

    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'   
        value = value + '<div><a class="importar_link" href="importar_tipo_item/'+pklist+'" style="text-decoration:none" TITLE= "Importar"></a></div>'
        value = value + '</div>'
        return value
    def init(self, buscado):
        self.buscado = buscado

    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        self.id_fase_que_importa = unicode(request.url.split("/")[-8])
        if TienePermiso("importar tipo de item", id_fase = self.id_fase_que_importa):
            tipos_item = DBSession.query(TipoItem).filter(TipoItem.id_fase == self.id_fase).filter(or_(TipoItem.nombre.contains(self.buscado), TipoItem.descripcion.contains(self.buscado))).filter(~TipoItem.id.contains("TI1")).all()
        else:
            tipos_item = list() 
        return len(tipos_item), tipos_item 
tipo_item_table_filler = TipoItemTableFiller(DBSession)


class TipoItemControllerNuevo(RestController):
    table = tipo_item_table
    tipo_item_filler = tipo_item_table_filler
    
    @with_trailing_slash
    def get_one(self, fase_id):
        tipos_item = DBSession.query(TipoItem).filter(TipoItem.id_fase == fase_id).all()
        return dict(tipos_item = tipos_item)
    
    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)
    def get_all(self):
        tipo_item_table_filler.init("")
        tmpl_context.widget = self.table
        d = dict()
        d["value_list"] = self.tipo_item_filler.get_value()
        d["model"] = "Tipos de item"
        d["accion"] = "./buscar"
        d["direccion_anterior"] = "../.."
        return d

    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)
    def buscar(self, **kw):
        buscar_table_filler = TipoItemTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Tipos de Item", accion = "./buscar")
        d["direccion_anterior"] = "../.."
        return d

    def importar_caracteristica(self, id_tipo_item_viejo, id_tipo_item_nuevo):
        caracteristicas = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_item == id_tipo_item_viejo).all()
        for caracteristica in caracteristicas:
            c = Caracteristica()
            c.nombre = caracteristica.nombre
            c.tipo = caracteristica.tipo
            c.descripcion = caracteristica.descripcion
            ids_caracteristicas = DBSession.query(Caracteristica.id).filter(Caracteristica.id_tipo_item == id_tipo_item_nuevo).all()
            if ids_caracteristicas:        
                proximo_id_caracteristica = proximo_id(ids_caracteristicas)
            else:
                proximo_id_caracteristica = "CA1-" + id_tipo_item_nuevo
            c.id = proximo_id_caracteristica
            c.tipo_item = DBSession.query(TipoItem).filter(TipoItem.id == id_tipo_item_nuevo).one()
            DBSession.add(c)

    @with_trailing_slash
    @expose()
    def importar_tipo_item(self, *args, **kw):
        id_fase = unicode(request.url.split("/")[-10])#verificar!
        t = TipoItem()
        id_tipo_item = unicode(request.url.split("/")[-2])#verificar
        tipo_item_a_importar = DBSession.query(TipoItem).filter(TipoItem.id == id_tipo_item).one()
        existe_nombre = DBSession.query(TipoItem).filter(TipoItem.id_fase == id_fase).filter(TipoItem.nombre == tipo_item_a_importar.nombre).count()
        existe_codigo = DBSession.query(TipoItem).filter(TipoItem.id_fase == id_fase).filter(TipoItem.codigo == tipo_item_a_importar.codigo).count()    
        t.nombre = tipo_item_a_importar.nombre
        t.codigo = tipo_item_a_importar.codigo
        if existe_nombre:  
            t.nombre = t.nombre + "'"
        if existe_codigo:  
            t.codigo = t.codigo + "'"
        t.descripcion = tipo_item_a_importar.descripcion
        ids_tipos_item = DBSession.query(TipoItem.id).filter(TipoItem.id_fase == id_fase).all()
        if ids_tipos_item:        
            proximo_id_tipo_item = proximo_id(ids_tipos_item)
        else:
            proximo_id_tipo_item = "TI1-" + id_fase
        t.id = proximo_id_tipo_item
        t.fase = DBSession.query(Fase).filter(Fase.id == id_fase).one()        
        DBSession.add(t)
        self.importar_caracteristica(id_tipo_item, t.id)
        flash("Se importo de forma exitosa")
        raise redirect('./../../../../../../..')#verificar
