# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Archivo, Item, Fase, TipoItem
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
from sqlalchemy import func
from tw.forms.fields import FileField
errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class ArchivoTable(TableBase):
    __model__ = Archivo
    __omit_fields__ = ['contenido', 'id_item', 'item']
archivo_table = ArchivoTable(DBSession)

class ArchivoTableFiller(TableFiller):
    __model__ = Archivo
    __omit_fields__ = ['contenido']
    buscado = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="descarga_link" href="descargar?id_archivo='+ pklist +'" style="text-decoration:none">descargar</a>'\
              '</div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+ pklist +'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm(\'¿Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        '</form>'\
        '</div>'
        value = value + '</div>'
        return value
    
    def init(self,buscado):
        self.buscado = buscado

    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        archivos = DBSession.query(Archivo).filter(Archivo.id.contains(self.buscado)).all()
        return len(archivos), archivos 
    
    def fase(self, obj):
        fase = unicode(obj.item_2.tipo_item.id_fase)
        return fase

archivo_table_filler = ArchivoTableFiller(DBSession)

class AddArchivo(AddRecordForm):
    __model__ = Archivo
    __omit_fields__ = ['id', 'id_item', 'item', 'nombre']
    contenido = FileField('archivo')
add_archivo_form = AddArchivo(DBSession)


class ArchivoController(CrudRestController):
    model = Archivo
    table = archivo_table
    table_filler = archivo_table_filler  
    new_form = add_archivo_form

    def _before(self, *args, **kw):
        self.id_item = unicode(request.url.split("/")[-3][0:-2])
        self.version_item = unicode(request.url.split("/")[-3][-1])
        #self.id_fase = unicode(request.url.split("/")[-5])
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
    @require(TienePermiso("manage"))
    def get_all(self, *args, **kw):      
        d = super(ArchivoController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        item = DBSession.query(Item).filter(Item.id == self.id_item).filter(Item.version == self.version_item).one()
        lista = [archivo.id for archivo in item.archivos]
        for archivo in reversed(d["value_list"]):
            if archivo["id"] not in lista:
                d["value_list"].remove(archivo)
        return d

    @without_trailing_slash
    @expose(content_type=CUSTOM_CONTENT_TYPE) 
    @require(TienePermiso("manage"))
    def descargar(self, *args, **kw):
        id_archivo = kw["id_archivo"]
        archivo = DBSession.query(Archivo).filter(Archivo.id == id_archivo).one()
        rh = response.headers
        rh['Content-Type'] = 'application/octet-stream'
        disposition = 'attachment; filename="'+ archivo.nombre +'"'
        rh['Content-disposition'] = disposition 
        rh['Pragma'] = 'public' # for IE 
        rh['Cache-control'] = 'max-age=0' #for IE 
        return archivo.contenido

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    @require(TienePermiso("manage"))
    def new(self, *args, **kw):
        tmpl_context.widget = self.new_form
        d = dict(value=kw, model=self.model.__name__)
        return d


    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    @require(TienePermiso("manage"))
    def buscar(self, **kw):
        buscar_table_filler = ArchivoTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "archivo", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

    #@catch_errors(errors, error_handler=new)
    @expose('json')
    #@registered_validate(error_handler=new)
    def post(self, **kw):
        a = Archivo()
        maximo_id_archivo = DBSession.query(func.max(Archivo.id)).scalar()
        if not maximo_id_archivo:
            maximo_id_archivo = "AR0-" + self.id_item
        archivo_maximo = maximo_id_archivo.split("-")[0]
        nro_maximo = int(archivo_maximo[2:])
        a.id = "AR" + str(nro_maximo + 1) + "-" + self.id_item     
        a.nombre = kw['archivo'].filename
        a.contenido = kw['archivo'].value
        a.items.append(DBSession.query(Item).filter(Item.id == self.id_item).filter(Item.version == self.version_item).one())
        DBSession.add(a)
        #flash("Creación realizada de forma exitosa")
        raise redirect('./')