# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Fase
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context #templates
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso
from tg import request
from sqlalchemy import func
from saip.model.app import Proyecto
from saip.controllers.tipo_item_controller import TipoItemController
from formencode.validators import Regex
from tw.forms import SingleSelectField
from sprox.widgets import PropertySingleSelectField
from saip.controllers.proyecto_controller_2 import ProyectoControllerNuevo

errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass


class HijoDeRegex(Regex):
    messages = {
        'invalid': ("Introduzca un valor que empiece con una letra"),
        }


class FaseTable(TableBase):
	__model__ = Fase
	__omit_fields__ = ['id', 'proyecto', 'lineas_base', 'fichas', 'tipos_item', 'id_proyecto']
fase_table = FaseTable(DBSession)

class FaseTableFiller(TableFiller):
    __model__ = Fase
    buscado = ""
    id_proyecto = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="edit_link" href="'+pklist+'/edit" style="text-decoration:none">edit</a>'\
              '</div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="tipo_item_link" href="'+pklist+'/tipo_item" style="text-decoration:none">tipo_item</a></div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm(\'¿Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        '</form>'\
        '</div>'
        value = value + '</div>'
        return value
    
    def init(self, buscado, id_proyecto):
        self.buscado = buscado
        self.id_proyecto = id_proyecto
    def _do_get_provider_count_and_objs(self, buscado = "", **kw):
        if self.id_proyecto == "":
            fases = DBSession.query(Fase).filter(Fase.nombre.contains(self.buscado)).order_by(Fase.orden).all()    
        else:
            fases = DBSession.query(Fase).filter(Fase.nombre.contains(self.buscado)).filter(Fase.id_proyecto == self.id_proyecto).order_by(Fase.orden).all()  
        return len(fases), fases 
fase_table_filler = FaseTableFiller(DBSession)


class OrdenFieldNew(PropertySingleSelectField):
    def obtener_fases_posibles(self):
        id_proyecto = unicode(request.url.split("/")[-3])
        cantidad_fases = DBSession.query(Proyecto.nro_fases).filter(Proyecto.id == id_proyecto).scalar()
        ordenes = DBSession.query(Fase.orden).filter(Fase.id_proyecto == id_proyecto).order_by(Fase.orden).all()
        vec = list()
        list_ordenes = list()
        for elem in ordenes:
            list_ordenes.append(elem.orden)
        for elem in xrange(cantidad_fases):
            if not (elem+1) in list_ordenes:
                vec.append(elem+1)        
        return vec
    
    def _my_update_params(self, d, nullable=False):
        opciones = self.obtener_fases_posibles()
        d['options'] = opciones
        return d

class OrdenFieldEdit(PropertySingleSelectField):
    def obtener_fases_posibles(self):
        id_proyecto = unicode(request.url.split("/")[-4])
        id_fase = unicode(request.url.split("/")[-2])
        cantidad_fases = DBSession.query(Proyecto.nro_fases).filter(Proyecto.id == id_proyecto).scalar()
        ordenes = DBSession.query(Fase.orden).filter(Fase.id_proyecto == id_proyecto).order_by(Fase.orden).all()
        orden_actual = DBSession.query(Fase.orden).filter(Fase.id == id_fase).scalar()
        vec = list()
        list_ordenes = list()
        vec.append(orden_actual)
        for elem in ordenes:
            list_ordenes.append(elem.orden)
        for elem in xrange(cantidad_fases):
            if not (elem+1) in list_ordenes:
                vec.append(elem+1)     
        return vec
    
    def _my_update_params(self, d, nullable=False):
        opciones = self.obtener_fases_posibles()
        d['options'] = opciones
        return d


class AddFase(AddRecordForm):
    __model__ = Fase
    __omit_fields__ = ['id', 'proyecto', 'lineas_base', 'fichas', 'tipos_item', 'id_proyecto', 'estado', 'fecha_inicio']
    orden = OrdenFieldNew
add_fase_form = AddFase(DBSession)

class EditFase(EditableForm):
    __model__ = Fase
    __omit_fields__ = ['id', 'lineas_base', 'fichas', 'estado', 'fecha_inicio']
    __hide_fields__ = ['id_proyecto', 'tipos_item', 'proyecto']
    orden = OrdenFieldEdit
edit_fase_form = EditFase(DBSession)

class FaseEditFiller(EditFormFiller):
    __model__ = Fase
fase_edit_filler = FaseEditFiller(DBSession)


class FaseController(CrudRestController):
    proyectos = ProyectoControllerNuevo()    
    tipo_item = TipoItemController(DBSession)
    model = Fase
    table = fase_table
    table_filler = fase_table_filler  
    edit_filler = fase_edit_filler
    edit_form = edit_fase_form
    new_form = add_fase_form
    id_proyecto = None

    def _before(self, *args, **kw):
        self.id_proyecto = unicode(request.url.split("/")[-3])
        super(FaseController, self)._before(*args, **kw)
    
    
    def get_one(self, fase_id):
        tmpl_context.widget = fase_table
        fase = DBSession.query(Fase).get(fase_id)
        value = fase_table_filler.get_value(fase = fase)
        return dict(fase = fase, value = value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all_fase")
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    #@require(TienePermiso("listar fases",id_proyecto = id_proyecto))
    def get_all(self, *args, **kw):  
        #TienePermiso("listar fases",id_proyecto = self.id_proyecto).check_authorization(request.environ)
        d = super(FaseController, self).get_all(*args, **kw)
        cant_fases = DBSession.query(Fase).filter(Fase.id_proyecto == self.id_proyecto).count()
        if cant_fases < DBSession.query(Proyecto.nro_fases).filter(Proyecto.id == self.id_proyecto).scalar():
            d["orden_suficiente"] = True
        else:
            d["orden_suficiente"] = False 
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        
        
        a_eliminar = list()
        for fase in d["value_list"]:
            if not (fase["proyecto"] == self.id_proyecto):
                a_eliminar.append(fase)
        for fase in a_eliminar:
            d["value_list"].remove(fase)
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    @require(TienePermiso("manage"))
    def new(self, *args, **kw):
        return super(FaseController, self).new(*args, **kw)
    
    @with_trailing_slash
    @expose('saip.templates.get_all_fase')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        buscar_table_filler = FaseTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_proyecto)
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "fase", accion = "./buscar")

        cant_fases = DBSession.query(Fase).filter(Fase.id_proyecto == self.id_proyecto).count()
        if cant_fases < DBSession.query(Proyecto.nro_fases).filter(Proyecto.id == self.id_proyecto).scalar():
            d["orden_suficiente"] = True
        else:
            d["orden_suficiente"] = False

        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d
    
    @catch_errors(errors, error_handler=new)
    @expose()
    @registered_validate(error_handler=new)
    @require(TienePermiso("manage"))
    def post(self, **kw):
        f = Fase()
        f.nombre = kw['nombre']   
        f.orden = kw['orden']
        fecha_inicio = datetime.datetime.now()
        f.fecha_inicio = datetime.date(int(fecha_inicio.year),int(fecha_inicio.month),int(fecha_inicio.day))
        f.fecha_fin = datetime.date(int(kw['fecha_fin'][0:4]),int(kw['fecha_fin'][5:7]),int(kw['fecha_fin'][8:10]))
        f.descripcion = kw['descripcion']
        f.estado = 'Inicial'
        maximo_id_fase = DBSession.query(func.max(Fase.id)).filter(Fase.id_proyecto == self.id_proyecto).scalar()        
        if not maximo_id_fase:
            maximo_id_fase = "FA0-" + self.id_proyecto    
        fase_maxima = maximo_id_fase.split("-")[0]
        nro_maximo = int(fase_maxima[2:])
        f.id = "FA" + str(nro_maximo + 1) + "-" + self.id_proyecto
        f.proyecto = DBSession.query(Proyecto).filter(Proyecto.id == self.id_proyecto).one()        
        DBSession.add(f)
        raise redirect('./')
