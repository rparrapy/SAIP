# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Relacion, Item, Fase, TipoItem
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from saip.lib.auth import TienePermiso
from tg import request, flash
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func, desc, or_, and_
from sqlalchemy.orm import aliased
from saip.lib.func import *
import pydot
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class RelacionTable(TableBase):
    __model__ = Relacion
    __omit_fields__ = ['id_item_1', 'id_item_2']
    __xml_fields__ = ['fase']
    #__dropdown_field_names__ = {'tipo_item':'nombre'}    
relacion_table = RelacionTable(DBSession)

class RelacionTableFiller(TableFiller):
    __model__ = Relacion
    buscado = ""
    id_item = ""
    version_item = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        item = DBSession.query(Item).filter(Item.id == self.id_item).filter( \
                Item.version == self.version_item).one()
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True
        if TienePermiso("eliminar relaciones", id_fase = item.tipo_item.fase \
                        .id).is_met(request.environ) and not bloqueado:
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm' \
            '(\'¿Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0;' \
            ' color: #286571; display: inline; margin: 0; padding: 0;"/>'\
            '</form>'\
            '</div>'
        value = value + '</div>'
        return value
    
    def init(self,buscado, id_item, version_item):
        self.buscado = buscado
        self.id_item = id_item
        self.version_item = version_item

    def _do_get_provider_count_and_objs(self, buscado="", **kw): #PROBAR BUSCAR
        item_1 = aliased(Item)
        item_2 = aliased(Item)                
        raux = DBSession.query(Relacion).join((item_1, Relacion.id_item_1 == \
            item_1.id)).join((item_2, Relacion.id_item_2 == item_2.id)) \
            .filter(or_(and_(Relacion.id_item_1 == self.id_item, Relacion \
            .version_item_1 == self.version_item), and_(Relacion.id_item_2 == \
            self.id_item, Relacion.version_item_2 == self.version_item)))\
            .filter(or_(Relacion.id.contains(self.buscado), \
            item_1.nombre.contains(self.buscado), item_2.nombre.contains( \
            self.buscado))).all()
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version_item).one()
        lista = [x for x in relaciones_a_actualizadas(item.relaciones_a) + \
                relaciones_b_actualizadas(item.relaciones_b)]
        relaciones = [r for r in raux if r in lista]
        return len(relaciones), relaciones 
    

relacion_table_filler = RelacionTableFiller(DBSession)

class AddRelacion(AddRecordForm):
    __model__ = Relacion
    __omit_fields__ = ['id', 'id_item_1', 'id_item_2', 'item_1']
add_relacion_form = AddRelacion(DBSession)


class RelacionController(CrudRestController):
    fases = FaseController(DBSession)
    model = Relacion
    table = relacion_table
    table_filler = relacion_table_filler  
    new_form = add_relacion_form

    def _before(self, *args, **kw):
        self.id_item = unicode("-".join(request.url.split("/")[-3] \
                .split("-")[0:-1]))
        self.version_item = unicode(request.url.split("/")[-3].split("-")[-1])
        super(RelacionController, self)._before(*args, **kw)
    
    def get_one(self, relacion_id):
        tmpl_context.widget = relacion_table
        relacion = DBSession.query(Relacion).get(relacion_id)
        value = relacion_table_filler.get_value(relacion = relacion)
        return dict(relacion = relacion, value = value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all_relacion")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):   
        relacion_table_filler.init("", self.id_item, self.version_item)   
        d = super(RelacionController, self).get_all(*args, **kw)
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version_item).one()
        d["accion"] = "./buscar"
        d["fases"] = list()
        d["model"] = "Relaciones"
        lista = [x.id_item_2 for x in item.relaciones_a] + \
                [x.id_item_1 for x in item.relaciones_b]
        fase_actual = DBSession.query(Fase).filter(Fase.id == \
                item.tipo_item.id_fase).one()
        band = False
        ts_item = [t for t in fase_actual.tipos_item]
        items = list()
        for t_item in ts_item:
            items = items + t_item.items
        for it in items:
            if it.id not in lista and it.id != self.id_item:
                band = True
                break
        if band: d["fases"].append(fase_actual)
        fase_ant = DBSession.query(Fase).filter(Fase.id_proyecto == \
                item.tipo_item.fase.id_proyecto).filter(Fase.orden == \
                item.tipo_item.fase.orden - 1).first()
        if fase_ant:
            band = False
            ts_item = [t for t in fase_ant.tipos_item]
            items = list()
            for t_item in ts_item:
                items = items + t_item.items
            for it in items:
                if it.id not in lista and it.linea_base:
                    if it.linea_base.cerrado and it.linea_base.consistente:
                        band = True
                        break
            if band: d["fases"].append(fase_ant)
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True
        if d["fases"]:
            d["permiso_crear"] = TienePermiso("crear relaciones", id_fase = \
                    fase_actual.id).is_met(request.environ) and not bloqueado
        else: d["permiso_crear"] = False
        d["direccion_anterior"] = "../.."
        return d

    @without_trailing_slash
    @expose('saip.templates.new_relacion')
    def new(self, *args, **kw):
        it = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version_item).one()
        if TienePermiso("crear relaciones", id_fase = it.tipo_item.fase.id):
            tmpl_context.widget = self.new_form
            d = dict(value=kw, model=self.model.__name__)
            d["items"] = DBSession.query(Item).join(Item.tipo_item) \
                .filter(TipoItem.id_fase == kw["fase"]).filter(Item.id != \
                self.id_item).filter(Item.borrado == False).all()
            lista = [x.id_item_2 for x in it.relaciones_a] + \
                    [y.id_item_1 for y in it.relaciones_b]
            for item in reversed(d["items"]):
                if item.id in lista: 
                    d["items"].remove(item)
                else:
                    if item.tipo_item.fase < it.tipo_item.fase:
                        if item.linea_base:
                            if not item.linea_base.consistente and \
                               item.linea_base.cerrado: d["items"].remove(item)
                        else: d["items"].remove(item)
            aux = []
            for item in d["items"]:
                for item_2 in d["items"]:
                    if item.id == item_2.id : 
                        if item.version > item_2.version: 
                            aux.append(item_2)
                        elif item.version < item_2.version: 
                            aux.append(item)
            d["items"] = [i for i in d["items"] if i not in aux]
            d["direccion_anterior"] = "../"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')            


    @with_trailing_slash
    @expose('saip.templates.get_all_relacion')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        buscar_table_filler = RelacionTableFiller(DBSession)
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version_item).one()
        buscar_table_filler = RelacionTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_item, \
                    self.version_item)
        else:
            buscar_table_filler.init("", self.id_item, self.version_item)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Relaciones", accion = "./buscar")
        d["fases"] = list()
        lista = [x.id_item_2 for x in item.relaciones_a] + \
                [x.id_item_1 for x in item.relaciones_b]
        fase_actual = DBSession.query(Fase).filter(Fase.id == \
                item.tipo_item.id_fase).one()
        band = False
        ts_item = [t for t in fase_actual.tipos_item]
        items = list()
        for t_item in ts_item:
            items = items + t_item.items
        for it in items:
            if it.id not in lista and it.id != self.id_item:
                band = True
                break
        if band: d["fases"].append(fase_actual)
        fase_ant = DBSession.query(Fase).filter(Fase.id_proyecto == \
                item.tipo_item.fase.id_proyecto).filter(Fase.orden == \
                item.tipo_item.fase.orden - 1).first()
        if fase_ant:
            band = False
            ts_item = [t for t in fase_ant.tipos_item]
            items = list()
            for t_item in ts_item:
                items = items + t_item.items
            for it in items:
                if it.id not in lista and it.linea_base:
                    if it.linea_base.cerrado and it.linea_base.consistente:
                        band = True
                        break
            if band: d["fases"].append(fase_ant)        
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True
        if d["fases"]:
            d["permiso_crear"] = TienePermiso("crear relaciones", id_fase = \
                    fase_actual.id).is_met(request.environ) and not bloqueado
        else: d["permiso_crear"] = False
        d["direccion_anterior"] = "../.."        
        return d

    def crear_version(self, it, borrado = None):
        nueva_version = Item()
        nueva_version.id = it.id
        nueva_version.version = it.version + 1
        nueva_version.nombre = it.nombre
        nueva_version.descripcion = it.descripcion
        nueva_version.estado = it.estado
        nueva_version.observaciones = it.observaciones
        nueva_version.prioridad = it.prioridad
        nueva_version.complejidad = it.complejidad
        nueva_version.borrado = it.borrado
        nueva_version.anexo = it.anexo
        nueva_version.tipo_item = it.tipo_item
        nueva_version.linea_base = it.linea_base
        nueva_version.archivos = it.archivos
        for relacion in it.relaciones_a:
            if not relacion == borrado:
                aux = relacion.id.split("+")
                r = Relacion()
                r.id = "-".join(aux[0].split("-")[0:-1]) + "-" + \
                    unicode(nueva_version.version) + "+" +aux[1] 
                r.item_1 = nueva_version
                r.item_2 = relacion.item_2
        for relacion in it.relaciones_b:
            if not relacion == borrado:
                r = Relacion()
                aux = relacion.id.split("+")
                r.id = aux[0] + "+" + "-".join(aux[1].split("-")[0:-1]) + \
                    "-" + unicode(nueva_version.version)
                r.item_1 = relacion.item_1
                r.item_2 = nueva_version
        return nueva_version

    @expose('json')
    def post(self, **kw):
        r = Relacion()

        item_2 = DBSession.query(Item).filter(Item.id == self.id_item) \
                .filter(Item.version == self.version_item).one()
        item_1 = DBSession.query(Item).filter(Item.id == kw["item_2"]) \
                .order_by(desc(Item.version)).first()
        r.id = "RE-" + item_1.id + "-" + unicode(item_1.version) + "+" + \
                item_2.id + "-" + unicode(item_2.version)
        r.item_1 = item_1
        r.item_2 = self.crear_version(item_2)

        if forma_ciclo(r.item_1):
            DBSession.delete(r)
            raise redirect('./')
        else:
            DBSession.add(r)
            flash("Creacion realizada de forma exitosa")
            raise redirect('./../../' + r.item_2.id + '-' + \
                unicode(r.item_2.version) + '/' + 'relaciones/')

    @expose()
    def post_delete(self, *args, **kw):
        #it = DBSession.query(Item).filter(Item.id == self.id_item).filter(Item.version == self.version_item).one()
        relacion = DBSession.query(Relacion).filter(Relacion.id == args[0]).one()
        nueva_version_1 = self.crear_version(relacion.item_2, relacion)
        raise redirect('./../../' + nueva_version_1.id + '-' + unicode(nueva_version_1.version) + '/' + 'relaciones/')

