# -*- coding: utf-8 -*-
from tg.controllers import RestController
from tg.decorators import with_trailing_slash, paginate
from tg import expose, flash
from saip.model import DBSession
from saip.model.app import Fase
from tg import request, redirect
from tg import tmpl_context #templates
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
import datetime
from sqlalchemy import func
from saip.model.app import Proyecto, Caracteristica, TipoItem
from saip.lib.auth import TienePermiso
from saip.controllers.tipo_item_controller_nuevo import TipoItemControllerNuevo
from saip.lib.func import proximo_id
from sqlalchemy import or_

class FaseTable(TableBase):
	__model__ = Fase
	__omit_fields__ = ['id', 'proyecto', 'lineas_base', 'fichas', \
                    'tipos_item', 'id_proyecto']
fase_table = FaseTable(DBSession)

class FaseTableFiller(TableFiller):
    __model__ = Fase
    id_proyecto = ""
    opcion = ""
    id_fase = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if self.opcion == unicode("tipo_item"):    
            value = value + '<div><a class="tipo_item_link" href="'+pklist+ \
                    '/tipos_de_item" style="text-decoration:none" TITLE =' \
                    ' "Tipos de item"></a></div>'
        else:
            value = value + '<div><a class="importar_link" href=' \
             '"importar_fase/'+pklist+'" style="text-decoration:none" TITLE=' \
             ' "Importar"></a></div>'
        value = value + '</div>'
        return value

    def init(self, buscado):
        self.buscado = buscado
    def _do_get_provider_count_and_objs(self, **kw):
        self.id_proyecto = unicode(request.url.split("/")[-3])
        self.opcion = unicode(request.url.split("/")[-5])
        self.id_fase = unicode(request.url.split("/")[-6])
        if self.opcion == unicode("tipo_item"):
            if TienePermiso("importar tipo de item", id_fase = self.id_fase):
                fases = DBSession.query(Fase).filter(Fase.id_proyecto == \
                    self.id_proyecto).filter(Fase.id != self.id_fase).all()
                fases = [f for f in fases if len(f.tipos_item) > 1]
                for fase in reversed(fases):
                    buscado = self.buscado in fase.nombre or \
                      self.buscado in fase.descripcion or \
                      self.buscado in str(fase.orden) or \
                      self.buscado in str(fase.fecha_inicio) or \
                      self.buscado in str(fase.fecha_fin) or \
                      self.buscado in fase.estado

                    if not buscado: fases.remove(fase)   
            else:
                fases = list()            
        else:
            if TienePermiso("importar fase", id_proyecto = self.id_proyecto):
                fases = DBSession.query(Fase).filter(Fase.id_proyecto == \
                self.id_proyecto).all()
                for fase in reversed(fases):
                    buscado = self.buscado in fase.nombre or \
                      self.buscado in fase.descripcion or \
                      self.buscado in str(fase.orden) or \
                      self.buscado in str(fase.fecha_inicio) or \
                      self.buscado in str(fase.fecha_fin) or \
                      self.buscado in fase.estado

                    if not buscado: fases.remove(fase)   
            else:
                proyectos = list()
        return len(fases), fases 

fase_table_filler = FaseTableFiller(DBSession)

class FaseControllerNuevo(RestController):
    tipos_de_item = TipoItemControllerNuevo()   
    table = fase_table
    fase_filler = fase_table_filler

    @with_trailing_slash
    def get_one(self, proyecto_id):
        fases = DBSession.query(Fase).filter(Fase.id_proyecto == proyecto_id) \
        .all()
        return dict(fases=fases)
    
    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @paginate('value_list', items_per_page = 4)
    def get_all(self):
        if TienePermiso("importar tipo de item").is_met(request.environ) \
                    or TienePermiso("importar fase").is_met(request.environ):
            fase_table_filler.init("")
            tmpl_context.widget = self.table
            d = dict()
            d["value_list"] = self.fase_filler.get_value()
            d["model"] = "Fases"
            d["accion"] = "./buscar"
            d["direccion_anterior"] = "../.."
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')
 
    @with_trailing_slash
    @expose('saip.templates.get_all_comun')
    @expose('json')
    @paginate('value_list', items_per_page = 4)
    def buscar(self, **kw):
        buscar_table_filler = FaseTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Fases", accion = "./buscar", \
                direccion_anterior = "../..")
        return d       
    
    def obtener_orden(self, id_proyecto):
        cantidad_fases = DBSession.query(Proyecto.nro_fases) \
                    .filter(Proyecto.id == id_proyecto).scalar()
        ordenes = DBSession.query(Fase.orden).filter(Fase.id_proyecto == \
                id_proyecto).order_by(Fase.orden).all()
        vec = list()
        list_ordenes = list()
        for elem in ordenes:
            list_ordenes.append(elem.orden)
        for elem in xrange(cantidad_fases):
            if not (elem+1) in list_ordenes:
                vec.append(elem+1)        
        return vec[0]

    def importar_caracteristica(self, id_tipo_item_viejo, id_tipo_item_nuevo):
        caracteristicas = DBSession.query(Caracteristica) \
            .filter(Caracteristica.id_tipo_item == id_tipo_item_viejo).all()
        for caracteristica in caracteristicas:
            c = Caracteristica()
            c.nombre = caracteristica.nombre
            c.tipo = caracteristica.tipo
            c.descripcion = caracteristica.descripcion
            ids_caracteristicas = DBSession.query(Caracteristica.id) \
               .filter(Caracteristica.id_tipo_item == id_tipo_item_nuevo).all()
            if ids_caracteristicas:        
                proximo_id_caracteristica = proximo_id(ids_caracteristicas)
            else:
                proximo_id_caracteristica = "CA1-" + id_tipo_item_nuevo
            c.id = proximo_id_caracteristica

            c.tipo_item = DBSession.query(TipoItem).filter(TipoItem.id == \
                        id_tipo_item_nuevo).one()
            DBSession.add(c)

    def importar_tipo_item(self, id_fase_vieja, id_fase_nueva):
        tipos_item = DBSession.query(TipoItem).filter(TipoItem.id_fase == \
                    id_fase_vieja).all()
        for tipo_item in tipos_item:
            t = TipoItem()
            t.codigo = tipo_item.codigo
            t.nombre = tipo_item.nombre
            t.descripcion = tipo_item.descripcion
            ids_tipos_item = DBSession.query(TipoItem.id) \
                    .filter(TipoItem.id_fase == id_fase_nueva).all()
            if ids_tipos_item:        
                proximo_id_tipo_item = proximo_id(ids_tipos_item)
            else:
                proximo_id_tipo_item = "TI1-" + id_fase_nueva
            t.id = proximo_id_tipo_item
            t.fase = DBSession.query(Fase).filter(Fase.id == id_fase_nueva) \
                    .one()
            DBSession.add(t)
            cont = DBSession.query(Caracteristica) \
                    .filter(Caracteristica.id_tipo_item == t.id).count()
            self.importar_caracteristica(tipo_item.id, t.id)
    
    @with_trailing_slash
    @expose()
    def importar_fase(self, *args, **kw):
        id_proyecto = unicode(request.url.split("/")[-8])
        f = Fase()
        id_fase = unicode(request.url.split("/")[-2])
        fase_a_importar = DBSession.query(Fase).filter(Fase.id == id_fase) \
                .one()
        existe_nombre = DBSession.query(Fase).filter(Fase.id_proyecto == \
             id_proyecto).filter(Fase.nombre == fase_a_importar.nombre).count()    
        f.nombre = fase_a_importar.nombre
        if existe_nombre:  
            f.nombre = f.nombre + "'"   
        f.orden = self.obtener_orden(id_proyecto)
        fecha_inicio = datetime.datetime.now()
        f.fecha_inicio = datetime.date(int(fecha_inicio.year), \
                    int(fecha_inicio.month),int(fecha_inicio.day))
        
        f.descripcion = fase_a_importar.descripcion
        f.estado = u'Inicial'
        ids_fases = DBSession.query(Fase.id).filter(Fase.id_proyecto == \
                    id_proyecto).all()
        if ids_fases:        
            proximo_id_fase = proximo_id(ids_fases)
        else:
            proximo_id_fase = "FA1-" + id_proyecto
        f.id = proximo_id_fase
        f.proyecto = DBSession.query(Proyecto).filter(Proyecto.id == \
                id_proyecto).one()        
        DBSession.add(f)
        self.importar_tipo_item(id_fase, f.id)
        flash(u"Se importó de forma exitosa")
        raise redirect('./../../../../..')

