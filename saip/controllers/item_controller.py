# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Item, TipoItem, Caracteristica, Relacion, Revision
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context #templates
from tg import expose, require, request, redirect, validate
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from tg import request, flash
from saip.controllers.fase_controller import FaseController
from saip.controllers.relacion_controller import RelacionController
from saip.controllers.archivo_controller import ArchivoController
from saip.controllers.borrado_controller import BorradoController
from saip.controllers.version_controller import VersionController
from saip.controllers.revision_controller import RevisionController
from sqlalchemy import func, desc, or_
from copy import *
import json
import os
import pydot
from saip.lib.func import *
from formencode.validators import NotEmpty

errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class ItemTable(TableBase):
    __model__ = Item
    __omit_fields__ = ['id_tipo_item', 'id_fase', 'id_linea_base', 'archivos','borrado', 'relaciones_a', 'relaciones_b', 'anexo']
    #__dropdown_field_names__ = {'tipo_item':'nombre'} 
item_table = ItemTable(DBSession)

class ItemTableFiller(TableFiller):
    __model__ = Item
    buscado = ""
    id_fase = ""

    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        pklist = pklist.split('/')
        id_item = pklist[0]
        id_tipo_item = unicode(id_item.split("-")[1] + "-" + id_item.split("-")[2] + "-" + id_item.split("-")[3])
        id_fase = unicode(id_tipo_item.split("-")[1] + "-" + id_tipo_item.split("-")[2])
        version_item = pklist[1]
        pklist = '-'.join(pklist)
        item = DBSession.query(Item).filter(Item.id == id_item).filter(Item.version == version_item).one()
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True
        value = '<div>'
        if TienePermiso("modificar item", id_fase = id_fase).is_met(request.environ) and not bloqueado:
            value = value + '<div><a class="edit_link" href="'+pklist+'/edit" style="text-decoration:none" TITLE = "Modificar"></a>'\
                    '</div>'       
        if TienePermiso("eliminar item", id_fase = id_fase).is_met(request.environ) and not bloqueado:
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to" TITLE = "Eliminar">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm(\'¿Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        '</form>'\
        '</div>'
        if TienePermiso("calcular costo de impacto", id_fase = id_fase).is_met(request.environ):
            value = value + '<div><a class="costo_link" href="costo?id_item='+id_item+'" style="text-decoration:none" TITLE = "Costo de impacto"></a>'\
                '</div>'
        if TienePermiso("reversionar item", id_fase = id_fase).is_met(request.environ) and item.version != 1:
            value = value + '<div><a class="reversion_link" href="'+pklist+'/versiones" style="text-decoration:none" TITLE = "Reversionar item"></a>'\
                    '</div>' 
        value = value + '<div><a class="archivo_link" href="'+pklist+'/archivos" style="text-decoration:none" TITLE = "Archivos"></a>'\
                '</div>'
        value = value + '<div><a class="relacion_link" href="'+pklist+'/relaciones" style="text-decoration:none" TITLE = "Relaciones"></a>'\
                '</div>'     

        revisiones = DBSession.query(Revision).filter(Revision.id_item == item.id).all()
        value = value + '<div><a class="revision_link" href="'+pklist+'/revisiones" style="text-decoration:none" TITLE = "Revisiones"></a>'\
              '</div>'     
        if item.estado == u"En desarrollo" and not bloqueado:
            if TienePermiso("setear estado item listo", id_fase = id_fase).is_met(request.environ):
                value = value + '<div><a class="listo_link" href="listo?pk_item='+pklist+'" style="text-decoration:none" TITLE = "Listo"></a>'\
              '</div>'
        if item.estado == u"Listo" and not bloqueado:
            if TienePermiso("setear estado item aprobado", id_fase = id_fase).is_met(request.environ) and not es_huerfano(item):
                value = value + '<div><a class="aprobado_link" href="aprobar?pk_item='+pklist+'" style="text-decoration:none" TITLE = "Aprobar"></a></div>'
                #si el orden de la fase es 1 no se controla antecesor
                #id_fase = item.id.split("-")[2] + "-" + item.id.split("-")[3]
                #print "ID FASE"
                #print id_fase
                #orden_fase_tupla = DBSession.query(Fase.orden).filter(Fase.id == id_fase).one()
                #orden_fase = orden_fase_tupla.orden
                #print "ORDEN FASE"
                #print orden_fase
                #if orden_fase == 1:
                #    mostrar = True
                #else:
                #    ids_relacionados_1 = DBSession.query(Relacion.id_item_2).filter(Relacion.id_item_1 == item.id).filter(Relacion.version_item_1 == item.version).all()
                #    ids_relacionados_2 = DBSession.query(Relacion.id_item_1).filter(Relacion.id_item_2 == item.id).filter(Relacion.version_item_2 == item.version).all()
                #    for id_item in ids_relacionados_1:
         #       print "ENTRO"

           # 
        if item.anexo != "{}":
            value = value + '<div><a class="caracteristica_link" href="listar_caracteristicas?pk_item='+pklist+'" style="text-decoration:none" TITLE = "Ver caracteristicas"></a></div>'

        value = value + '</div>'
        return value
    
    def init(self, buscado, id_fase):
        self.buscado = buscado
        self.id_fase = id_fase
    def _do_get_provider_count_and_objs(self, buscado = "", id_fase = "", **kw):
        if TieneAlgunPermiso(tipo = u"Fase", recurso = u"Item", id_fase = self.id_fase).is_met(request.environ):         
            items = DBSession.query(Item).join(Item.tipo_item).filter(or_(Item.id.contains(self.buscado),Item.nombre.contains(self.buscado), Item.version.contains(self.buscado), Item.descripcion.contains(self.buscado), Item.estado.contains(self.buscado), Item.observaciones.contains(self.buscado), Item.complejidad.contains(self.buscado), Item.prioridad.contains(self.buscado), TipoItem.nombre.contains(self.buscado), Item.id_linea_base.contains(self.buscado))).filter(Item.id_tipo_item.contains(self.id_fase)).filter(Item.borrado == False).order_by(Item.id).all()
            aux = []
            for item in items:
                for item_2 in items:
                    if item.id == item_2.id : 
                        if item.version > item_2.version: 
                            aux.append(item_2)
                        elif item.version < item_2.version :
                            aux.append(item)
            items = [i for i in items if i not in aux]
        else:
            items = list() 
        return len(items), items 
item_table_filler = ItemTableFiller(DBSession)

class AddItem(AddRecordForm):
    __model__ = Item
    __omit_fields__ = ['id', 'codigo',  'archivos', 'fichas', 'revisiones', 'id_tipo_item, id_linea_base', 'tipo_item', 'linea_base','relaciones_a', 'relaciones_b']
    nombre = NotEmpty()
add_item_form = AddItem(DBSession)

class EditItem(EditableForm):
    __model__ = Item
    __omit_fields__ = ['id', 'codigo', 'archivos', 'fichas', 'revisiones', 'id_tipo_item, id_linea_base', 'tipo_item', 'linea_base', 'relaciones_a', 'relaciones_b']
edit_item_form = EditItem(DBSession)

class ItemEditFiller(EditFormFiller):
    __model__ = Item
item_edit_filler = ItemEditFiller(DBSession)

class ItemController(CrudRestController):
    relaciones = RelacionController(DBSession)
    archivos = ArchivoController(DBSession)
    borrados = BorradoController(DBSession)
    versiones = VersionController(DBSession)
    revisiones = RevisionController(DBSession)
    model = Item
    table = item_table
    table_filler = item_table_filler  
    edit_filler = item_edit_filler
    edit_form = edit_item_form
    new_form = add_item_form

    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        super(ItemController, self)._before(*args, **kw)
    
    def get_one(self, item_id):
        tmpl_context.widget = item_table
        item = DBSession.query(Item).get(item_id)
        value = item_table_filler.get_value(item = item)
        return dict(item = item, value = value, accion = "./buscar")

    @without_trailing_slash
    @expose()
    def costo(self, *args, **kw):
        if TienePermiso("calcular costo de impacto", id_fase = self.id_fase).is_met(request.environ):
            id_item = kw["id_item"]
            if os.path.isfile('saip/public/images/grafo.png'): os.remove('saip/public/images/grafo.png')            
            item = DBSession.query(Item).filter(Item.id == id_item).order_by(desc(Item.version)).first()
            grafo = pydot.Dot(graph_type='digraph')
            valor, grafo = costo_impacto(item, grafo)
            grafo.write_png('saip/public/images/grafo.png')
            print valor
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')

    @with_trailing_slash
    @expose("saip.templates.get_all_item")
    @expose('json')
    @paginate('value_list', items_per_page=3)
    def get_all(self, *args, **kw):   
        item_table_filler.init("", self.id_fase)
        d = super(ItemController, self).get_all(*args, **kw)
        items_borrados = DBSession.query(Item).filter(Item.id.contains(self.id_fase)).filter(Item.borrado == True).count()
        d["permiso_recuperar"] = TienePermiso("recuperar item", id_fase = self.id_fase).is_met(request.environ) and items_borrados
        d["permiso_crear"] = TienePermiso("crear item", id_fase = self.id_fase).is_met(request.environ) #VERIFICAR el self.id_fase
        d["accion"] = "./buscar"   
        d["tipos_item"] = DBSession.query(TipoItem).filter(TipoItem.id_fase == self.id_fase)
        d["direccion_anterior"] = "../.."
        return d

    @without_trailing_slash
    @expose('saip.templates.new_item')
    def new(self, *args, **kw):
        if TienePermiso("crear item", id_fase = self.id_fase).is_met(request.environ):
            tmpl_context.widget = self.new_form
            d = dict(value=kw, model=self.model.__name__)
            d["caracteristicas"] = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_item == kw['tipo_item'])
            d["tipo_item"] = kw['tipo_item']
            d["direccion_anterior"] = "./"

            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')
        
    @without_trailing_slash
    @expose('saip.templates.edit_item')
    def edit(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-4])
        if TienePermiso("modificar item", id_fase = self.id_fase).is_met(request.environ): #VERIFICAR el self.id_fase
            """Display a page to edit the record."""
            tmpl_context.widget = self.edit_form
            pks = self.provider.get_primary_fields(self.model)
            clave_primaria = args[0]
            pk_version = unicode(clave_primaria.split("-")[4])
            pk_id = unicode(clave_primaria.split("-")[0] + "-" + clave_primaria.split("-")[1] + "-" + clave_primaria.split("-")[2] + "-" + clave_primaria.split("-")[3])
            clave = {}
            clave[0] = pk_id
            clave[1] = pk_version        
            kw = {}        
            for i, pk in  enumerate(pks):
                kw[pk] = clave[i]     
            value = self.edit_filler.get_value(kw)
            value['anexo'] = json.loads(value['anexo'])
            d = dict()
            d['value'] = value
            d['model'] = self.model.__name__
            d['pk_count'] = len(pks)

            id_item = unicode(request.url.split("/")[-2])
            id_item = id_item.split("-")
            id_tipo_item = id_item[1] + "-" + id_item[2] + "-" + id_item[3]
            caracteristicas = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_item == id_tipo_item).all()
            d['caracteristicas'] = caracteristicas
            d['tipo_item'] = id_tipo_item
            d["direccion_anterior"] = "../"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')

    @with_trailing_slash
    @expose('saip.templates.get_all_item')
    @expose('json')
    @paginate('value_list', items_per_page = 3)
    def buscar(self, **kw):
        #self.id_fase = unicode(request.url.split("/")[-4])
        buscar_table_filler = ItemTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_fase)
        else:
            buscar_table_filler.init("", self.id_fase)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "item", accion = "./buscar")
        items_borrados = DBSession.query(Item).filter(Item.id.contains(self.id_fase)).filter(Item.borrado == True).count()
        d["permiso_crear"] = TienePermiso("crear item", id_fase = self.id_fase).is_met(request.environ)
        d["permiso_recuperar"] = TienePermiso("recuperar item", id_fase = self.id_fase).is_met(request.environ) and items_borrados
        d["tipos_item"] = DBSession.query(TipoItem).filter(TipoItem.id_fase == self.id_fase)
        d["direccion_anterior"] = "../.."
        return d

    #@catch_errors(errors, error_handler=new)
    #@expose()
    #@registered_validate(error_handler=new)
    @expose()
    def post(self, **kw):
        print "post"
        #id_fase = unicode(request.url.split("/")[-3])
        #print id_fase
        i = Item()
        i.descripcion = kw['descripcion']
        i.nombre = kw['nombre']
        i.estado = 'En desarrollo'
        i.observaciones = kw['observaciones']
        i.prioridad = kw['prioridad']
        i.complejidad = kw['complejidad']
        i.version = 1
        i.borrado = False
        caract = DBSession.query(Caracteristica).filter(Caracteristica.id_tipo_item == kw['tipo_item']).all()
        anexo = dict()
        for nom_car in caract: 
            anexo[nom_car.nombre] = kw[nom_car.nombre]
        i.anexo = json.dumps(anexo)
        ids_items = DBSession.query(Item.id).filter(Item.id_tipo_item == kw["tipo_item"]).all()
        if ids_items:        
            proximo_id_item = proximo_id(ids_items)
        else:
            proximo_id_item = "IT1-" + kw["tipo_item"]
        i.id = proximo_id_item
        i.tipo_item = DBSession.query(TipoItem).filter(TipoItem.id == kw["tipo_item"]).one()
        DBSession.add(i)
        i.codigo = i.tipo_item.codigo + "-" + i.id.split("-")[0][2:]
        raise redirect('./')
    
    @expose()
    #@registered_validate(error_handler=edit)
    #@catch_errors(errors, error_handler=edit)
    def put(self, *args, **kw):
        """update"""
        nombre_caract = DBSession.query(Caracteristica.nombre).filter(Caracteristica.id_tipo_item == kw['tipo_item']).all()      
        anexo = dict()
        for nom_car in nombre_caract:
            anexo[nom_car.nombre] = kw[nom_car.nombre]
        anexo = json.dumps(anexo)

        clave_primaria = args[0]
        pk_version = unicode(clave_primaria.split("-")[4])
        pk_id = unicode(clave_primaria.split("-")[0] + "-" + clave_primaria.split("-")[1] + "-" + clave_primaria.split("-")[2] + "-" + clave_primaria.split("-")[3])
        clave = {}
        clave[0] = pk_id
        clave[1] = pk_version        
        it = DBSession.query(Item).filter(Item.id == pk_id).filter(Item.version == pk_version).scalar()
        pks = self.provider.get_primary_fields(self.model)
        for i, pk in enumerate(pks):
            if pk not in kw and i < len(clave):
                kw[pk] = clave[i]
        band = 0
        nueva_version = Item()
        nueva_version.id = it.id
        nueva_version.codigo = it.codigo
        nueva_version.version = int(pk_version) + 1
        nueva_version.nombre = it.nombre
        nueva_version.descripcion = it.descripcion
        nueva_version.estado = u"En desarrollo"
        nueva_version.observaciones = it.observaciones
        nueva_version.prioridad = it.prioridad
        nueva_version.complejidad = it.complejidad
        nueva_version.borrado = it.borrado
        nueva_version.anexo = it.anexo
        if not it.descripcion == kw['descripcion']:
            band = 1
            nueva_version.descripcion = kw['descripcion']
        if not it.nombre == kw['nombre']:
            band = 1
            nueva_version.nombre = kw['nombre']
        if not it.observaciones == kw['observaciones']:
            band = 1
            nueva_version.observaciones = kw['observaciones']
        if not it.prioridad == int(kw['prioridad']):
            band = 1
            nueva_version.prioridad = kw['prioridad']
        if not it.complejidad == int(kw['complejidad']):
            band = 1
            nueva_version.complejidad = kw['complejidad']
        if not it.anexo == anexo:
            band = 1
            nueva_version.anexo = anexo
        
        if band:
            nueva_version.tipo_item = it.tipo_item
            nueva_version.linea_base = it.linea_base
            nueva_version.archivos = it.archivos
            for relacion in relaciones_a_actualizadas(it.relaciones_a):
                aux = relacion.id.split("+")
                r = Relacion()
                r.id = "-".join(aux[0].split("-")[0:-1]) + "-" + unicode(nueva_version.version) + "+" +aux[1] 
                r.item_1 = nueva_version
                r.item_2 = relacion.item_2
                #print relacion.id
                #print r.id
            for relacion in relaciones_b_actualizadas(it.relaciones_b):
                r = Relacion()
                aux = relacion.id.split("+")
                r.id = aux[0] + "+" + "-".join(aux[1].split("-")[0:-1]) + "-" + unicode(nueva_version.version)
                r.item_1 = relacion.item_1
                r.item_2 = nueva_version
                #print relacion.id
                #print r.id
            DBSession.add(nueva_version)
            #PARTE NUEVA, CREAR REVISION PARA ITEMS DIRECTAMENTE RELACIONADOS. VERIFICAR SI SE LLAMA EN EL LUGAR CORRECTO.
            ids_items_direc_relacionados_1 = DBSession.query(Relacion.id_item_2, Relacion.version_item_2).filter(Relacion.id_item_1 == pk_id).filter(Relacion.version_item_1 == pk_version).all()
            ids_items_direc_relacionados_2 = DBSession.query(Relacion.id_item_1, Relacion.version_item_1).filter(Relacion.id_item_2 == pk_id).filter(Relacion.version_item_2 == pk_version).all()
            for tupla_id_item_version in (ids_items_direc_relacionados_1 + ids_items_direc_relacionados_2):
                r = Revision()
                id_item = tupla_id_item_version[0]
                version_item = tupla_id_item_version[1]
                ids_revisiones = DBSession.query(Revision.id).filter(Revision.id_item == id_item).all()
                if ids_revisiones:
                    proximo_id_revision = proximo_id(ids_revisiones)
                else:
                    proximo_id_revision = "RV1-" + id_item
                r.id = proximo_id_revision
                r.item = DBSession.query(Item).filter(Item.id == id_item).filter(Item.version == version_item).one()
                
                r.descripcion = "Modificacion del item relacionado directamente: " + pk_id
                DBSession.add(r)
            #FIN PARTE NUEVA
        else:       
            self.provider.update(self.model, params=kw)        
        redirect('../')

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
        nueva_version.tipo_item = it.tipo_item
        nueva_version.linea_base = it.linea_base
        nueva_version.archivos = it.archivos
        for relacion in it.relaciones_a:
            if not relacion == borrado:
                aux = relacion.id.split("+")
                r = Relacion()
                r.id = "-".join(aux[0].split("-")[0:-1]) + "-" + unicode(nueva_version.version) + "+" +aux[1] 
                r.item_1 = nueva_version
                r.item_2 = relacion.item_2
        for relacion in it.relaciones_b:
            if not relacion == borrado:
                r = Relacion()
                aux = relacion.id.split("+")
                r.id = aux[0] + "+" + "-".join(aux[1].split("-")[0:-1]) + "-" + unicode(nueva_version.version)
                r.item_1 = relacion.item_1
                r.item_2 = nueva_version
        return nueva_version

    def crear_revision(self, item, msg):
        rv = Revision()
        ids_revisiones = DBSession.query(Revision.id).filter(Revision.id_item == item.id).all()
        if ids_revisiones:
            proximo_id_revision = proximo_id(ids_revisiones)
        else:
            proximo_id_revision = "RV1-" + item.id
        rv.id = proximo_id_revision
        rv.item = item
        rv.descripcion = msg
        DBSession.add(rv)       

    @expose()
    def post_delete(self, *args, **kw):
        """This is the code that actually deletes the record"""
        pks = self.provider.get_primary_fields(self.model)
        clave_primaria = args[0]
        pk_version = unicode(clave_primaria.split("-")[4])
        pk_id = unicode(clave_primaria.split("-")[0] + "-" + clave_primaria.split("-")[1] + "-" + clave_primaria.split("-")[2] + "-" + clave_primaria.split("-")[3])
        it = DBSession.query(Item).filter(Item.id == pk_id).filter(Item.version == pk_version).scalar()
        it.borrado = True
        re = it.relaciones_a
        re_act = relaciones_a_actualizadas(re)
        if re:
            for relacion in re:
                if relacion in re_act:
                    nueva_version = self.crear_version(relacion.item_2, relacion)            
                    if es_huerfano(nueva_version) and (nueva_version.estado == u"Aprobado" or nueva_version.linea_base):
                            msg = u"Item huerfano"
                            self.crear_revision(nueva_version, msg)                
                DBSession.delete(relacion)
        re = it.relaciones_b
        if re:
            for relacion in re:         
                DBSession.delete(relacion)
        items_anteriores = DBSession.query(Item).filter(Item.id == pk_id).filter(Item.version != pk_version).all()
        if items_anteriores:
            for item in items_anteriores:
                DBSession.delete(item)
        redirect('./')


    @expose()
    def listo(self, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        if TienePermiso("setear estado item listo", id_fase = self.id_fase).is_met(request.environ): #VERIFICAR el self.id_fase
            pk = kw["pk_item"]
            pk_version = unicode(pk.split("-")[4])
            pk_id = unicode(pk.split("-")[0] + "-" + pk.split("-")[1] + "-" + pk.split("-")[2] + "-" + pk.split("-")[3])
            item = DBSession.query(Item).filter(Item.id == pk_id).filter(Item.version == pk_version).one()
            item.estado = "Listo"
            if item.linea_base:
                consistencia_lb(item.linea_base)
            flash("El item seleccionado se encuentra listo para ser aprobado")
            redirect('./')
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')

    @expose()
    def aprobar(self, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        if TienePermiso("setear estado item aprobado", id_fase = self.id_fase).is_met(request.environ): #VERIFICAR el self.id_fase
            pk = kw["pk_item"]
            pk_version = unicode(pk.split("-")[4])
            pk_id = unicode(pk.split("-")[0] + "-" + pk.split("-")[1] + "-" + pk.split("-")[2] + "-" + pk.split("-")[3])
            item = DBSession.query(Item).filter(Item.id == pk_id).filter(Item.version == pk_version).one()
            item.estado = "Aprobado"
            if item.linea_base:
                consistencia_lb(item.linea_base)
            flash("El item seleccionado fue aprobado")
            redirect('./')
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')


    @expose('saip.templates.get_all_caracteristicas_item')
    @paginate('value_list', items_per_page=7)
    def listar_caracteristicas(self, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        if TieneAlgunPermiso(tipo = u"Fase", recurso = u"Item", id_fase = self.id_fase).is_met(request.environ): #VERIFICAR el self.id_fase
            pk = kw["pk_item"]
            pk_id = unicode(pk.split("-")[0] + "-" + pk.split("-")[1] + "-" + pk.split("-")[2] + "-" + pk.split("-")[3])
            anexo = DBSession.query(Item.anexo).filter(Item.id == pk_id).one()
            anexo = json.loads(anexo.anexo)
            d = dict()
            d['anexo'] = anexo
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", u"error")
            redirect('./')
