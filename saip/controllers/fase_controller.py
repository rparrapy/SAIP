# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Fase
from sprox.tablebase import TableBase #para manejar datos de prueba
from sprox.fillerbase import TableFiller #""
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
from saip.model.app import Proyecto



class FaseTable(TableBase): #para manejar datos de prueba
	__model__ = Fase
	__omit_fields__ = ['id','proyecto']
fase_table = FaseTable(DBSession)

class FaseTableFiller(TableFiller):#para manejar datos de prueba
    __model__ = Fase
    buscado=""
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
    
    def init(self,buscado):
        self.buscado=buscado
    def _do_get_provider_count_and_objs(self, buscado="", **kw):
        fases = DBSession.query(Fase).filter(Fase.nombre.contains(self.buscado)).all()
        return len(fases), fases 
fase_table_filler = FaseTableFiller(DBSession)

class AddFase(AddRecordForm):
    __model__ = Fase
    __omit_fields__ = ['id', 'proyecto']
add_fase_form = AddFase(DBSession)

class EditFase(EditableForm):
    __model__ = Fase
    __omit_fields__ = ['id', 'proyecto']
edit_fase_form = EditFase(DBSession)

class FaseEditFiller(EditFormFiller):
    __model__ = Fase
fase_edit_filler = FaseEditFiller(DBSession)


class FaseController(CrudRestController):    

    #def __init__(self, sesion, id_proy):
    #    super(FaseController, self).__init__(sesion)
    #    proyecto_id = id_proy

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
        value = fase_table_filler.get_value(fase=fase)
        return dict(fase=fase, value=value, accion = "./buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    #@require(TienePermiso("listar fases",id_proyecto = id_proyecto))
    def get_all(self, *args, **kw):  
        TienePermiso("listar fases",id_proyecto = self.id_proyecto).check_authorization(request.environ)
        d = super(FaseController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "./buscar"
        #print d["value_list"]
        a_eliminar = list()
        for fase in d["value_list"]:
            if not (fase["proyecto"] == self.id_proyecto):
                a_eliminar.append(fase)
        for fase in a_eliminar:
            d["value_list"].remove(fase)
        return d
    
    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def buscar(self, **kw):
        buscar_table_filler = FaseTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list=value, model="fase", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d
    
    @expose()
    @require(TienePermiso("manage")) #para prueba
    def post(self, **kw):
        f = Fase()
        f.nombre = kw['nombre']   
        f.orden = kw['orden']
        f.fecha_inicio = datetime.date(int(kw['fecha_inicio'][0:4]),int(kw['fecha_inicio'][5:7]),int(kw['fecha_inicio'][8:10]))
        f.fecha_fin = datetime.date(int(kw['fecha_fin'][0:4]),int(kw['fecha_fin'][5:7]),int(kw['fecha_fin'][8:10]))
        f.descripcion = kw['descripcion']
        f.estado = kw['estado']
        #f.id = "F1"
        #prueba = DBSession.query(Fase).all()
        #print "prueba" + str(prueba)
        #if prueba == "":
        maximo_id_fase = DBSession.query(func.max(Fase.id)).filter(Fase.id_proyecto==self.id_proyecto).scalar()        
        #maximo_id_fase = fases_por_proyecto.query.(func.max(Fase.id)).scalar()
        #print fases_por_proyecto
        if not maximo_id_fase:
            maximo_id_fase = "FA0-" + self.id_proyecto    
        #maximo_id_fase = DBSession.query.(func.max(Fase.id)).scalar()
        #num_maximo = maximo_id_fase[2:]
        fase_maxima = maximo_id_fase.split("-")[0]
        nro_maximo = int(fase_maxima[2:])
        print nro_maximo
        #print maximo_id_fase[2:3]
        f.id = "FA" + str(nro_maximo + 1) + "-" + self.id_proyecto
        print f.id
        f.proyecto = DBSession.query(Proyecto).filter(Proyecto.id == self.id_proyecto).one()        
        DBSession.add(f)
        raise redirect('./')
