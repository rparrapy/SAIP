# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash
from tg import expose, flash
from saip.model import DBSession
from saip.model.app import TipoItem
from tg import request, redirect
import datetime
from sqlalchemy import func
from saip.model.app import Proyecto, TipoItem, Fase

class TipoItemControllerNuevo(RestController):   
    @with_trailing_slash
    @expose('saip.templates.importar_tipo_item')
    def get_one(self, fase_id):
        tipos_item = DBSession.query(TipoItem).filter(TipoItem.id_fase == fase_id).all()
        return dict(tipos_item = tipos_item)
    
    @with_trailing_slash
    @expose('saip.templates.importar_tipo_item')
    def get_all(self):
        id_fase = unicode(request.url.split("/")[-3])#verificar posicion
        tipos_item = DBSession.query(TipoItem).filter(TipoItem.id_fase == id_fase).all()
        print "id_fase"
        print id_fase 
        return dict(tipos_item = tipos_item)

    @with_trailing_slash
    @expose('saip.templates.importar_tipo_item')
    def importar_tipo_item(self, *args, **kw):
        id_fase = unicode(request.url.split("/")[-10])#verificar!
        print "id fase en importar_tipo_item de tipoitemcontroller2"
        print id_fase
        t = TipoItem()
        id_tipo_item = unicode(request.url.split("/")[-2])#verificar
        print id_tipo_item
        tipo_item_a_importar = DBSession.query(TipoItem).filter(TipoItem.id == id_tipo_item).one()
                
        t.nombre = tipo_item_a_importar.nombre
        t.descripcion = tipo_item_a_importar.descripcion
        maximo_id_tipo_item = DBSession.query(func.max(TipoItem.id)).filter(TipoItem.id_fase == id_fase).scalar()        
        if not maximo_id_tipo_item:
            maximo_id_tipo_item = "FA0-" + id_fase
        tipo_item_maximo = maximo_id_tipo_item.split("-")[0]
        nro_maximo = int(tipo_item_maximo[2:])
        t.id = "TI" + str(nro_maximo + 1) + "-" + id_fase
        t.fase = DBSession.query(Fase).filter(Fase.id == id_fase).one()        
        DBSession.add(t)
        flash("Se importo de forma exitosa")
        raise redirect('./../../../../../../..')#verificar
