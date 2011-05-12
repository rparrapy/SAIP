from tgext.crud import CrudRestController
from saip.model import DBSession, TipoItem
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm #para creacion
from tg import tmpl_context #templates
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate 
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso
from tg import request
from sqlalchemy import func
from saip.model.app import Fase

class TipoItemTable(TableBase):
	__model__ = TipoItem
	__omit_fields__ = ['id', 'fase', 'id_fase', 'items', 'caracteristicas']
tipo_item_table = TipoItemTable(DBSession)


class TipoItemTableFiller(TableFiller):
    __model__ = TipoItem
    buscado = ""
    id_fase = ""
    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div><a class="edit_link" href="'+pklist+'/edit" style="text-decoration:none">edit</a>'\
              '</div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm(\'Are you sure?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        '</form>'\
        '</div>'
        value = value + '</div>'
        return value
    
    def init(self,buscado,id_fase):
        self.buscado = buscado
        self.id_fase = id_fase
    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        print "id_fase" + self.id_fase
        if self.id_fase == "":
            tiposItem = DBSession.query(TipoItem).filter(TipoItem.nombre.contains(self.buscado)).all()    
        else:
            tiposItem = DBSession.query(TipoItem).filter(TipoItem.nombre.contains(self.buscado)).filter(TipoItem.id_fase == self.id_fase).all()  
        return len(tiposItem), tiposItem 
tipo_item_table_filler = TipoItemTableFiller(DBSession)

class AddTipoItem(AddRecordForm):
    __model__ = TipoItem
    __omit_fields__ = ['id', 'fase', 'id_fase', 'items', 'caracteristicas']
add_tipo_item_form = AddTipoItem(DBSession)

class EditTipoItem(EditableForm):
    __model__ = TipoItem
    __omit_fields__ = ['id', 'fase', 'id_fase', 'items', 'caracteristicas']
edit_tipo_item_form = EditTipoItem(DBSession)

class TipoItemEditFiller(EditFormFiller):
    __model__ = TipoItem
tipo_item_edit_filler = TipoItemEditFiller(DBSession)

class TipoItemController(CrudRestController):
    model = TipoItem
    table = tipo_item_table
    table_filler = tipo_item_table_filler  
    edit_filler = tipo_item_edit_filler
    edit_form = edit_tipo_item_form
    new_form = add_tipo_item_form
    id_fase = None

    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        super(TipoItemController, self)._before(*args, **kw)
    
    def get_one(self, tipo_item_id): #verificar nombre tipo_item_id
        tmpl_context.widget = tipo_item_table
        tipo_item = DBSession.query(TipoItem).get(tipo_item_id)
        value = tipo_item_table_filler.get_value(tipo_item = tipo_item)
        return dict(tipo_item = tipo_item, value = value, model = "Tipos de Item", accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def get_all(self, *args, **kw):
        #falta TienePermiso
        d = super(TipoItemController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        d["model"] = "Tipos de Item"
        a_eliminar = list()
        for tipo_item in d["value_list"]:
            if not (tipo_item["fase"] == self.id_fase):
                a_eliminar.append(tipo_item)
        for tipo_item in a_eliminar:
            d["value_list"].remove(tipo_item)
        return d
    
    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 7)
    def buscar(self, **kw):
        buscar_table_filler = TipoItemTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"],self.id_fase)
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Tipos de Item", accion = "./buscar")#verificar valor de model
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d
    
    @expose()
    @require(TienePermiso("manage"))
    def post(self, **kw):
        t = TipoItem()
        t.descripcion = kw['descripcion']
        t.nombre = kw['nombre']

        maximo_id_tipo_item = DBSession.query(func.max(TipoItem.id)).filter(TipoItem.id_fase == self.id_fase).scalar()        
        if not maximo_id_tipo_item:
            maximo_id_tipo_item = "TI0-" + self.id_fase    
        tipo_item_maximo = maximo_id_tipo_item.split("-")[0]
        nro_maximo = int(tipo_item_maximo[2:])
        t.id = "TI" + str(nro_maximo + 1) + "-" + self.id_fase
        t.fase = DBSession.query(Fase).filter(Fase.id == self.id_fase).one()        
        DBSession.add(t)
        raise redirect('./')        
