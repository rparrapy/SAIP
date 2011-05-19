# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Ficha, Usuario, Rol, Proyecto, Fase
from sprox.tablebase import TableBase #para manejar datos de prueba
from sprox.fillerbase import TableFiller #""
from sprox.formbase import AddRecordForm #para creacion
from tg import tmpl_context #templates
from tg import expose, require, request, redirect
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash  
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso
from tg import request
from sqlalchemy import func
from sprox.widgets import PropertySingleSelectField

class FichaTable(TableBase): #para manejar datos de prueba
    __model__ = Ficha
    __field_order__ = ['id','usuario', 'rol', 'proyecto', 'fase']
    __omit_fields__ = ['id_proyecto','id_fase','id_usuario','id_rol']
ficha_table = FichaTable(DBSession)

class FichaTableFiller(TableFiller):#para manejar datos de prueba
    __model__ = Ficha
    buscado=""
    id_usuario = ""    
    def init(self,buscado, id_usuario):
        self.buscado=buscado
        self.id_usuario = id_usuario

    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        ficha = DBSession.query(Ficha).filter(Ficha.id == unicode(pklist)).one()
        if ficha.rol.tipo == u'Proyecto' and not ficha.proyecto or ficha.rol.tipo == u'Fase' and (not ficha.proyecto or not ficha.fase)  : 
            value = value + '<div><a class="edit_link" href="'+pklist+'/edit" style="text-decoration:none">edit</a>'\
              '</div>'
        if TienePermiso("manage").is_met(request.environ):
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm(\'Está seguro?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        '</form>'\
        '</div>'
        value = value + '</div>'
        return value
    
    def rol(self, obj):
        return obj.rol.nombre

    def usuario(self, obj):
        return obj.usuario.nombre_usuario

    def proyecto(self, obj):
        if obj.proyecto: return obj.proyecto.nombre

    def fase(self, obj):
        if obj.fase: return obj.fase.nombre

    def _do_get_provider_count_and_objs(self, buscado = "", **kw):
        if self.id_usuario == "":
            fichas = DBSession.query(Ficha).all()    
        else:
            fichas = DBSession.query(Ficha).filter(Ficha.id_usuario == self.id_usuario).all()
            for ficha in reversed(fichas):
                if not (ficha.nombre.contains(self.buscado)):
                    fichas.remove(ficha)
        return len(fichas), fichas 
ficha_table_filler = FichaTableFiller(DBSession)

class AddFicha(AddRecordForm):
    __model__ = Ficha
    __omit_fields__ = ['proyecto','fase','id','usuario']
    __dropdown_field_names__ = {'rol':'nombre'}
add_ficha_form = AddFicha(DBSession)

class ProyectoField(PropertySingleSelectField):
        
        def _my_update_params(self, d, nullable=False): 
            id_ficha = unicode(request.url.split("/")[-2])
            ficha = DBSession.query(Ficha).filter(Ficha.id == id_ficha).one()
            if ficha.rol.tipo == u"Proyecto" or ficha.rol.tipo == u"Fase":
                if not ficha.proyecto:
                    proyectos = DBSession.query(Proyecto).all()
                    d['options'] = [(proyecto.id, proyecto.nombre) for proyecto in proyectos]
                else:
                    d['options'] = [[ficha.id_proyecto, ficha.proyecto.nombre]]
            else: d['options'] = [[None,"-----------"]]
            return d

class FaseField(PropertySingleSelectField):
        
        def _my_update_params(self, d, nullable=False): 
            id_ficha = unicode(request.url.split("/")[-2])
            ficha = DBSession.query(Ficha).filter(Ficha.id == id_ficha).one()
            if ficha.rol.tipo == u"Fase": 
                if not ficha.proyecto:
                    d['options'] = [[None,"-----------"]]    
                else:
                    if not ficha.fase:
                        fases = DBSession.query(Fase).filter(Fase.id_proyecto == ficha.id_proyecto).all()
                        d['options'] = [(fase.id, fase.nombre) for fase in fases]
                    else:
                        d['options'] = [[ficha.id_fase, ficha.fase.nombre]]
            else: d['options'] = [[None,"-----------"]]
            return d

class EditFicha(EditableForm):
    __model__ = Ficha
    id_usuario = unicode(request.url.split("/")[-2])
    __hide_fields__ = ['id','usuario', 'rol']
    proyecto = ProyectoField
    fase = FaseField
edit_ficha_form = EditFicha(DBSession)

class FichaEditFiller(EditFormFiller):
    __model__ = Ficha
ficha_edit_filler = FichaEditFiller(DBSession)

class FichaController(CrudRestController):
    model = Ficha
    table = ficha_table
    table_filler = ficha_table_filler  
    edit_filler = ficha_edit_filler
    edit_form = edit_ficha_form
    new_form = add_ficha_form


    def _before(self, *args, **kw):
        self.id_usuario = unicode(request.url.split("/")[-3])
        super(FichaController, self)._before(*args, **kw)
    
    def get_one(self, Ficha_id):
        tmpl_context.widget = Ficha_table
        ficha = DBSession.query(Ficha).get(Ficha_id)
        value = proyecto_table_filler.get_value(Ficha=ficha)
        return dict(Ficha=ficha, value=value, accion = "/fichas/buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    #@require(TienePermiso("listar Fichas"))
    def get_all(self, *args, **kw):       
        d = super(FichaController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        d["accion"] = "/fichas/buscar"
        #print d["value_list"] 
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    #@require(TienePermiso("crear Ficha"))
    def new(self, *args, **kw):
        return super(FichaController, self).new(*args, **kw)        
    
    #@require(TienePermiso("modificar Ficha"))
    @expose('tgext.crud.templates.edit')
    def edit(self, *args, **kw):
        return super(FichaController, self).edit(*args, **kw)        

    
    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page=7)
    #@require(TienePermiso("listar Fichas"))
    def buscar(self, **kw):
        buscar_table_filler = FichaTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list=value, model="Ficha", accion = "/fichas/buscar")
        d["permiso_crear"] = TienePermiso("crear ficha").is_met(request.environ)
        return d
    
    @expose()
    def post(self, **kw):
        f = Ficha()
        max_id_ficha = DBSession.query(func.max(Ficha.id)).filter(Ficha.id_usuario == self.id_usuario).scalar()        
        if not max_id_ficha:
            max_id_ficha = "FI0-" + self.id_usuario    
        ficha_maxima = max_id_ficha.split("-")[0]
        nro_maximo = int(ficha_maxima[2:])
        f.id = "FI" + str(nro_maximo + 1) + "-" + self.id_usuario
        f.usuario = DBSession.query(Usuario).filter(Usuario.id == self.id_usuario).one()
        f.rol = DBSession.query(Rol).filter(Rol.id ==  kw['rol']).one()          
        DBSession.add(f)
        raise redirect('./')
