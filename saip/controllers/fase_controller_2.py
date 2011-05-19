# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash
from tg import expose, flash
from saip.model import DBSession
from saip.model.app import Fase
from tg import request, redirect
import datetime
from sqlalchemy import func
from saip.model.app import Proyecto
from saip.model.app import TipoItem

class FaseControllerNuevo(RestController):   
    @with_trailing_slash
    @expose('saip.templates.importarfase')
    def get_one(self, proyecto_id):
        fases = DBSession.query(Fase).filter(Fase.id_proyecto == proyecto_id).all()
        return dict(fases=fases)
    
    @with_trailing_slash
    @expose('saip.templates.importarfase')
    def get_all(self):
        id_proyecto = unicode(request.url.split("/")[-3])
        fases = DBSession.query(Fase).filter(Fase.id_proyecto == id_proyecto).all()     
        return dict(fases = fases)
    
    def obtener_orden(self, id_proyecto):
        cantidad_fases = DBSession.query(Proyecto.nro_fases).filter(Proyecto.id == id_proyecto).scalar()
        ordenes = DBSession.query(Fase.orden).filter(Fase.id_proyecto == id_proyecto).order_by(Fase.orden).all()
        vec = list()
        list_ordenes = list()
        for elem in ordenes:
            list_ordenes.append(elem.orden)
        for elem in xrange(cantidad_fases):
            if not (elem+1) in list_ordenes:
                vec.append(elem+1)        
        return vec[0]

    def importar_tipo_item(self, id_fase_vieja,id_fase_nueva):
        t = TipoItem()
        tipos_item = DBSession.query(TipoItem).filter(TipoItem.id_fase == id_fase_vieja).all()
        for tipo_item in tipos_item:
            t.nombre = tipo_item.nombre
            t.descripcion = tipo_item.descripcion

            maximo_id_tipo_item = DBSession.query(func.max(TipoItem.id)).filter(TipoItem.id_fase == id_fase_nueva).scalar()        
            if not maximo_id_tipo_item:
                maximo_id_tipo_item = "TI0-" + id_fase_nueva    
            tipo_item_maximo = maximo_id_tipo_item.split("-")[0]
            nro_maximo = int(tipo_item_maximo[2:])
            t.id = "TI" + str(nro_maximo + 1) + "-" + id_fase_nueva
            t.fase = DBSession.query(Fase).filter(Fase.id == id_fase_nueva).one()
            DBSession.add(t)



        
    @with_trailing_slash
    @expose('saip.templates.importarfase')
    def importar_fase(self, *args, **kw):
        id_proyecto = unicode(request.url.split("/")[-8])
        f = Fase()
        id_fase = unicode(request.url.split("/")[-2])
        fase_a_importar = DBSession.query(Fase).filter(Fase.id == id_fase).one()
                
        f.nombre = fase_a_importar.nombre  
        f.orden = self.obtener_orden(id_proyecto)
        fecha_inicio = datetime.datetime.now()
        f.fecha_inicio = datetime.date(int(fecha_inicio.year),int(fecha_inicio.month),int(fecha_inicio.day))
        
        f.descripcion = fase_a_importar.descripcion
        f.estado = 'Inicial'
        maximo_id_fase = DBSession.query(func.max(Fase.id)).filter(Fase.id_proyecto == id_proyecto).scalar()        
        if not maximo_id_fase:
            maximo_id_fase = "FA0-" + id_proyecto    
        fase_maxima = maximo_id_fase.split("-")[0]
        nro_maximo = int(fase_maxima[2:])
        f.id = "FA" + str(nro_maximo + 1) + "-" + id_proyecto
        f.proyecto = DBSession.query(Proyecto).filter(Proyecto.id == id_proyecto).one()        
        DBSession.add(f)
        self.importar_tipo_item(id_fase, f.id)
        flash("Se importo de forma exitosa")
        raise redirect('./../../../../..')
       

            

