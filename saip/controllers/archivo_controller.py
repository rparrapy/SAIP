# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Archivo, Item, Fase, TipoItem, Relacion
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context #templates
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from saip.lib.auth import TienePermiso
from tg import request, flash, response
from tg.controllers import CUSTOM_CONTENT_TYPE 
from saip.controllers.fase_controller import FaseController
from sqlalchemy import func, desc, or_
from tw.forms.fields import FileField
from saip.lib.func import *
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class ArchivoTable(TableBase):
    __model__ = Archivo
    __omit_fields__ = ['contenido', 'items']
archivo_table = ArchivoTable(DBSession)

class ArchivoTableFiller(TableFiller):
    __model__ = Archivo
    __omit_fields__ = ['contenido']
    buscado = ""
    id_item = ""
    version = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version).one()
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True
        value = '<div>'
        if TienePermiso("descargar archivo", id_fase = item.tipo_item.fase \
                        .id).is_met(request.environ):
            value = value + '<div><a class="descarga_link"' \
                    ' href="descargar?id_archivo='+ pklist + \
                    '" style="text-decoration:none" TITLE= "Descargar"></a>'\
                    '</div>'
        if TienePermiso("modificar item", id_fase = item.tipo_item.fase.id) \
                        .is_met(request.environ) and not bloqueado:
            value = value + '<div>'\
                '<form method="POST" action="'+ pklist + \
                '" class="button-to" TITLE= "Eliminar">'\
                '<input type="hidden" name="_method" value="DELETE" />'\
                '<input class="delete-button" onclick="return confirm' \
                '(\'¿Está seguro?\');" value="delete" type="submit" '\
                'style="background-color: transparent; float:left; border:0;' \
                ' color: #286571; display: inline; margin: 0; padding: 0;"/>'\
                '</form>'\
                '</div>'
        value = value + '</div>'
        return value
    
    def init(self,buscado, id_item, version):
        self.buscado = buscado
        self.id_item = id_item
        self.version = version

    def _do_get_provider_count_and_objs(self, buscado="", id_item = "", \
                                        version = "", **kw):
        archivos = DBSession.query(Archivo).filter(or_(Archivo.id.contains( \
                   self.buscado), Archivo.nombre.contains(self.buscado))).all()
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
                .filter(Item.version == self.version).one()
        for archivo in reversed(archivos):
            if item not in archivo.items: archivos.remove(archivo)
        return len(archivos), archivos 

archivo_table_filler = ArchivoTableFiller(DBSession)

class AddArchivo(AddRecordForm):
    __model__ = Archivo
    __omit_fields__ = ['id', 'items', 'nombre']
    contenido = FileField('archivo')
add_archivo_form = AddArchivo(DBSession)


class ArchivoController(CrudRestController):
    model = Archivo
    table = archivo_table
    table_filler = archivo_table_filler  
    new_form = add_archivo_form

    def _before(self, *args, **kw):
        self.id_item = unicode("-".join(request.url.split("/")[-3] \
                            .split("-")[0:-1]))
        self.version_item = unicode(request.url.split("/")[-3].split("-")[-1])
        super(ArchivoController, self)._before(*args, **kw)
    
    def get_one(self, archivo_id):
        tmpl_context.widget = archivo_table
        archivo = DBSession.query(Archivo).get(archivo_id)
        value = archivo_table_filler.get_value(archivo = archivo)
        return dict(archivo = archivo, value = value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):
        archivo_table_filler.init("", self.id_item, self.version_item)
        d = super(ArchivoController, self).get_all(*args, **kw)
        d["accion"] = "./buscar"
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
                .filter(Item.version == self.version_item).one()       
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True
        d["permiso_crear"] = TienePermiso("descargar archivo", id_fase = \
                            item.tipo_item.fase.id) and not bloqueado
        d["direccion_anterior"] = "../.."                  
        return d

    @without_trailing_slash
    @expose(content_type=CUSTOM_CONTENT_TYPE)
    def descargar(self, *args, **kw):
        item = DBSession.query(Item).filter(Item.id == self.id_item).filter( \
                Item.version == self.version_item).one()
        if TienePermiso("descargar archivo", id_fase = item.tipo_item.fase \
                        .id).is_met(request.environ):
            id_archivo = kw["id_archivo"]
            archivo = DBSession.query(Archivo).filter(Archivo.id == \
                    id_archivo).one()
            rh = response.headers
            rh['Content-Type'] = 'application/octet-stream'
            disposition = 'attachment; filename="'+ archivo.nombre +'"'
            rh['Content-disposition'] = disposition 
            rh['Pragma'] = 'public' # for IE 
            rh['Cache-control'] = 'max-age=0' #for IE 
            return archivo.contenido
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            redirect('./')

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    def new(self, *args, **kw):
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
                .filter(Item.version == self.version_item).one()
        if TienePermiso("modificar item", id_fase = item.tipo_item.fase.id ) \
                        .is_met(request.environ):
            tmpl_context.widget = self.new_form
            d = dict(value=kw, model=self.model.__name__)
            d["direccion_anterior"] = "../.."
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            redirect('./')


    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        buscar_table_filler = ArchivoTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_item, \
                                self.version_item)
        else:
            buscar_table_filler.init("", self.id_item, self.version_item)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "archivo", accion = "./buscar")
        item = DBSession.query(Item).filter(Item.id == self.id_item) \
                .filter(Item.version == self.version_item).one()      
        bloqueado = False
        if item.linea_base:
            if item.linea_base.cerrado: bloqueado = True 
        d["permiso_crear"] = TienePermiso("modificar item", item.tipo_item \
                            .fase.id) and not bloqueado
        d["direccion_anterior"] = "../.."
        return d

    def crear_version(self, it):
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
        for relacion in relaciones_a_actualizadas(it.relaciones_a):
            aux = relacion.id.split("+")
            r = Relacion()
            r.id = "-".join(aux[0].split("-")[0:-1]) + "-" + \
                    unicode(nueva_version.version) + "+" +aux[1] 
            r.item_1 = nueva_version
            r.item_2 = relacion.item_2
        for relacion in relaciones_b_actualizadas(it.relaciones_b):
            r = Relacion()
            aux = relacion.id.split("+")
            r.id = aux[0] + "+" + "-".join(aux[1].split("-")[0:-1]) + "-" + \
                    unicode(nueva_version.version)
            r.item_1 = relacion.item_1
            r.item_2 = nueva_version
        return nueva_version

    @expose('json')
    def post(self, **kw):
        id_item_version = unicode(request.url.split("/")[-3])
        self.id_item = id_item_version.split("-")[0] + "-" + id_item_version \
                    .split("-")[1] + "-" + id_item_version.split("-")[2] + \
                    "-" + id_item_version.split("-")[3]
        self.version_item = id_item_version.split("-")[4]
        it = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version_item).one()
        nueva_version = self.crear_version(it)
        a = Archivo()

        ids_archivos = DBSession.query(Archivo.id).all()
        if ids_archivos:        
            proximo_id_archivo = proximo_id(ids_archivos)
        else:
            proximo_id_archivo = "AR1"
        a.id = proximo_id_archivo 
        a.nombre = kw['archivo'].filename
        a.contenido = kw['archivo'].value
        a.items.append(nueva_version)
        DBSession.add(a)
        flash(u"Creación realizada de forma exitosa")
        raise redirect('./../../' + nueva_version.id + '-' + unicode( \
                        nueva_version.version) + '/' + 'archivos/')

    @expose()
    def post_delete(self, *args, **kw):
        id_item_version = unicode(request.url.split("/")[-3])
        self.id_item = id_item_version.split("-")[0] + "-" + \
                    id_item_version.split("-")[1] + "-" + \
                    id_item_version.split("-")[2] + "-" + \
                    id_item_version.split("-")[3]
        self.version_item = id_item_version.split("-")[4]

        it = DBSession.query(Item).filter(Item.id == self.id_item) \
            .filter(Item.version == self.version_item).one()
        nueva_version = self.crear_version(it)
        archivo = DBSession.query(Archivo).filter(Archivo.id == args[0]).one()        
        nueva_version.archivos.remove(archivo)
        raise redirect('./../../' + nueva_version.id + '-' + \
                unicode(nueva_version.version) + '/' + 'archivos/')

