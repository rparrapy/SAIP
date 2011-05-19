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
from saip.controllers.item_controller import ItemController

class DesarrolloFaseController(RestController):   
    items = ItemController(DBSession)
    @with_trailing_slash
    @expose('saip.templates.get_all_desarrollo_fase')
    def get_one(self, proyecto_id):
        fases = DBSession.query(Fase).filter(Fase.id_proyecto == proyecto_id).all()
        return dict(fases=fases)
    
    @with_trailing_slash
    @expose('saip.templates.get_all_desarrollo_fase')
    def get_all(self):
        id_proyecto = unicode(request.url.split("/")[-3])
        fases = DBSession.query(Fase).filter(Fase.id_proyecto == id_proyecto).all()     
        return dict(fases = fases)

