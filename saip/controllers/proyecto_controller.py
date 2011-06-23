# -*- coding: utf-8 -*-
from tgext.crud import CrudRestController
from saip.model import DBSession, Proyecto, Fase, Usuario, Rol, Ficha
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect, flash
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash
from tgext.crud.decorators import registered_validate, catch_errors 
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso, TieneAlgunPermiso
from tg import request
from saip.controllers.fase_controller import FaseController
from saip.controllers.ficha_proyecto_controller import FichaProyectoController
from sqlalchemy import func
from saip.lib.func import proximo_id, estado_proyecto
from formencode import FancyValidator, Invalid, Schema
from formencode.validators import NotEmpty, Regex, DateConverter, DateValidator
from formencode.validators import Int
from formencode.compound import All
from sprox.formbase import Field
from tw.forms.fields import TextField
from sprox.widgets import PropertySingleSelectField
import transaction
from sqlalchemy.sql import exists
from sqlalchemy import or_

errors = ()
try:
    from sqlalchemy.exc import IntegrityError, DatabaseError, ProgrammingError
    errors =  (IntegrityError, DatabaseError, ProgrammingError)
except ImportError:
    pass

class Unico(FancyValidator):
    def _to_python(self, value, state):
        id_proyecto = self.id_proyecto = unicode(request.url.split("/")[-2])
        band = DBSession.query(Proyecto).filter(Proyecto.id != id_proyecto) \
                .filter(Proyecto.nombre == value).count()
        if band:
            raise Invalid(
                'El nombre de proyecto elegido ya está en uso',
                value, state)
        return value

class ValidarExpresion(Regex):
    messages = {
        'invalid': ("Introduzca un valor que empiece con una letra"),
        }

class ProyectoTable(TableBase):
	__model__ = Proyecto
	__omit_fields__ = ['id', 'fases', 'fichas', 'id_lider']
proyecto_table = ProyectoTable(DBSession)

class ProyectoTableFiller(TableFiller):
    __model__ = Proyecto
    buscado = ""

    def lider(self, obj):
        return obj.lider.nombre_usuario

    def __actions__(self, obj):
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        if TienePermiso("modificar proyecto").is_met(request.environ):
            value = value + '<div><a class="edit_link" href="'+pklist+ \
                '/edit" style="text-decoration:none" TITLE= "Modificar"></a>'\
                '</div>'
        pp = TieneAlgunPermiso(tipo = u"Proyecto", recurso = u"Fase", \
                id_proyecto = pklist).is_met(request.environ)
        pf = TieneAlgunPermiso(tipo = u"Fase", recurso = u"Tipo de Item", \
                id_proyecto = pklist).is_met(request.environ)
        pfp = TienePermiso(u"asignar rol cualquier fase", \
              id_proyecto = pklist).is_met(request.environ)
        pfi = TieneAlgunPermiso(tipo = "Fase", recurso = u"Ficha", \
              id_proyecto = pklist).is_met(request.environ)
        if pp or pf or pfp or pfi: 
            value = value + '<div><a class="fase_link" href="'+pklist+ \
                    '/fases" style="text-decoration:none" TITLE= "Fases"></a>'\
                    '</div>'
        if TienePermiso("asignar rol proyecto", id_proyecto = pklist).is_met( \
                        request.environ):
            value = value + '<div><a class="responsable_link" href="'+pklist+ \
                    '/responsables" style="text-decoration:none" '\
                    'TITLE= "Responsables"></a>'\
                    '</div>'
        if TienePermiso("eliminar proyecto").is_met(request.environ):
            value = value + '<div><form method="POST" action="'+pklist+ \
                    '" class="button-to" TITLE= "Eliminar">'\
                    '<input type="hidden" name="_method" value="DELETE" />'\
                    '<input class="delete-button" onclick="return confirm' \
                    '(\'¿Está seguro?\');" value="delete" type="submit" '\
                    'style="background-color: transparent; float:left; '\
                    'border:0; color: #286571; display: inline; margin: 0; '\
                    'padding: 0;"/>'\
                    '</form></div>'
        pr = DBSession.query(Proyecto).get(pklist)
        estado_proyecto(pr)
        cant_fases = DBSession.query(Fase).filter(Fase.id_proyecto == pklist) \
                    .count()
        if cant_fases == pr.nro_fases and pr.estado == u"Nuevo" and \
            TienePermiso("setear estado proyecto en desarrollo"). \
            is_met(request.environ):
            value = value + '<div><a class="inicio_link" href="iniciar/' \
                    +pklist+'" style="text-decoration:none">Inicia proyecto' \
                    '</a></div>'        

        value = value + '</div>'
        return value
    
    def init(self,buscado):
        self.buscado = buscado
    def _do_get_provider_count_and_objs(self, **kw):
        proyectos = DBSession.query(Proyecto).all()
        for proyecto in reversed(proyectos):
            buscado = self.buscado in str(proyecto.nro_fases) or \
                      self.buscado in str(proyecto.fecha_inicio) or \
                      self.buscado in str(proyecto.fecha_fin) or \
                      self.buscado in proyecto.lider.nombre_usuario or \
                      self.buscado in proyecto.nombre or \
                      self.buscado in proyecto.descripcion or \
                      self.buscado in proyecto.estado
    
            if not buscado: proyectos.remove(proyecto)
        ps = TieneAlgunPermiso(tipo = u"Sistema", recurso = u"Proyecto") \
            .is_met(request.environ)
        if not ps:
            for proyecto in reversed(proyectos):
                pfp = TienePermiso(u"asignar rol cualquier fase", \
                      id_proyecto = pklist).is_met(request.environ)
                pfi = TieneAlgunPermiso(tipo = "Fase", recurso = u"Ficha", \
                      id_proyecto = pklist).is_met(request.environ)
                pp = TieneAlgunPermiso(tipo = u"Proyecto", recurso = u"Fase", \
                     id_proyecto = proyecto.id).is_met(request.environ)
                pf = TieneAlgunPermiso(tipo = u"Fase", recurso =
                     u"Tipo de Item", id_proyecto = proyecto.id). \
                     is_met(request.environ)

                if not (pp or pf or pfp or pfi): proyectos.remove(proyecto)
                    
        return len(proyectos), proyectos 
proyecto_table_filler = ProyectoTableFiller(DBSession)

class NroValido(FancyValidator):
    def _to_python(self, value, state):
        id_proyecto = self.id_proyecto = unicode(request.url.split("/")[-2])
        cant_fases = DBSession.query(Fase).filter(Fase.id_proyecto == \
                    id_proyecto).count()
        if int(value) < cant_fases:
            raise Invalid(
                u'Existen más fases que el nro. ingresado',
                value, state)
        return value   

class AddProyecto(AddRecordForm):
    __model__ = Proyecto
    __omit_fields__ = ['id', 'fases', 'fichas', 'estado', 'fecha_inicio', 'fecha_fin']
    nombre = All(NotEmpty(), ValidarExpresion(r'^[A-Za-z][A-Za-z0-9 ]*$'), \
            Unico())
    nro_fases = All(NotEmpty() ,Int(min = 0))
    __dropdown_field_names__ = {'lider':'nombre_usuario'}
    #fecha_fin = DateValidator(DateConverter()after_now = True)
add_proyecto_form = AddProyecto(DBSession)

form_validator =  Schema(nro_fases = All(NroValido(), NotEmpty(), Int(min = \
                 0)))

class CantidadFasesField(TextField):
    def update_params(self, d):
        id_proy = unicode(request.url.split("/")[-2])
        pr = DBSession.query(Proyecto).get(id_proy)
        if pr.estado != u"Nuevo":
            d.disabled = True
        super(CantidadFasesField, self).update_params(d)

class EditProyecto(EditableForm):
    __model__ = Proyecto
    __base_validator__ = form_validator
    __hide_fields__ = ['id', 'fases', 'fichas', 'estado',  'fecha_inicio', 'fecha_fin']
    nro_fases = CantidadFasesField('nro_fases') 
    nombre = All(NotEmpty(), ValidarExpresion(r'^[A-Za-z][A-Za-z0-9 ]*$'), \
            Unico())
    __dropdown_field_names__ = {'lider':'nombre_usuario'}
edit_proyecto_form = EditProyecto(DBSession)

class ProyectoEditFiller(EditFormFiller):
    __model__ = Proyecto
proyecto_edit_filler = ProyectoEditFiller(DBSession)

class ProyectoController(CrudRestController):
    fases = FaseController(DBSession)
    model = Proyecto
    table = proyecto_table
    table_filler = proyecto_table_filler  
    edit_filler = proyecto_edit_filler
    edit_form = edit_proyecto_form
    new_form = add_proyecto_form
    responsables = FichaProyectoController(DBSession)

    @expose()
    def iniciar(self, id_proyecto):
        if TienePermiso("setear estado proyecto en desarrollo", id_proyecto = \
                        id_proyecto).is_met(request.environ):
            pr = DBSession.query(Proyecto).get(id_proyecto)
            fecha_inicio = datetime.datetime.now()
            pr.fecha_inicio = datetime.date(int(fecha_inicio.year), \
                            int(fecha_inicio.month),int(fecha_inicio.day))
            pr.estado = "En Desarrollo"
            flash("El proyecto " + id_proyecto + " se ha iniciado")
        else:
            flash(u" El usuario no cuenta con los permisos necesarios", \
                u"error" )
        raise redirect('../')
    
    def get_one(self, proyecto_id):
        tmpl_context.widget = proyecto_table
        proyecto = DBSession.query(Proyecto).get(proyecto_id)
        value = proyecto_table_filler.get_value(proyecto = proyecto)
        return dict(proyecto = proyecto, value = value, accion = \
                "/proyectos/buscar")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=4)
    def get_all(self, *args, **kw):   
        d = super(ProyectoController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("crear proyecto"). \
                            is_met(request.environ)
        d["model"] = "Proyectos"
        d["accion"] = "./buscar"
        d["direccion_anterior"] = "../"
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    def new(self, *args, **kw):
        if TienePermiso("crear proyecto").is_met(request.environ):
            d = super(ProyectoController, self).new(*args, **kw)
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')
        
                    
    @expose('tgext.crud.templates.edit')
    def edit(self, *args, **kw):
        if TienePermiso("modificar proyecto").is_met(request.environ):
            d = super(ProyectoController, self).edit(*args, **kw)
            d["direccion_anterior"] = "../"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')
                    

    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page = 4)
    def buscar(self, **kw):
        buscar_table_filler = ProyectoTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"])
        else:
            buscar_table_filler.init("")
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list = value, model = "Proyectos", accion = "./buscar")
        d["permiso_crear"] = TienePermiso("crear proyecto").\
                            is_met(request.environ)
        d["direccion_anterior"] = "../"
        return d

    @catch_errors(errors, error_handler=new)
    @expose()
    @registered_validate(error_handler=new)
    def post(self, **kw):
        p = Proyecto()
        p.descripcion = kw['descripcion']
        p.nombre = kw['nombre']
        p.estado = 'Nuevo'
        p.nro_fases = int(kw['nro_fases'])
        ids_proyectos = DBSession.query(Proyecto.id).all()
        if ids_proyectos:
            proximo_id_proyecto = proximo_id(ids_proyectos)
        else:
            proximo_id_proyecto = "PR1"
        p.id = proximo_id_proyecto
        if kw['lider']:
            objeto_usuario = DBSession.query(Usuario).filter(Usuario.id == \
                            kw['lider']).one()
            p.lider = objeto_usuario
            ids_fichas = DBSession.query(Ficha.id).filter(Ficha.id_usuario == \
                        kw['lider']).all()
            r = DBSession.query(Rol).filter(Rol.id == u'RL3').one()
            ficha = Ficha()
            ficha.usuario = objeto_usuario
            ficha.rol = r
            ficha.proyecto = p
            if ids_fichas:
                proximo_id_ficha = proximo_id(ids_fichas)
            else:
                proximo_id_ficha = "FI1-" + kw["lider"]
            ficha.id = proximo_id_ficha
            DBSession.add(p)
            DBSession.add(ficha)            
        else:
            DBSession.add(p)
        raise redirect('./')

    @expose()
    @registered_validate(error_handler=edit)
    @catch_errors(errors, error_handler=edit)
    def put(self, *args, **kw):
        """update"""
        
        id_proyecto = args[0]
        proyecto_modificado = DBSession.query(Proyecto).filter(Proyecto.id == \
                            id_proyecto).one()
        
        pks = self.provider.get_primary_fields(self.model)
        for i, pk in enumerate(pks):
            if pk not in kw and i < len(args):
                kw[pk] = args[i]
        usuario = None
        if kw['lider']:
            id_lider = kw['lider']
            viejo_lider_proyecto_tupla = DBSession.query(Proyecto.id_lider). \
                                       filter(Proyecto.id == id_proyecto).one()
            if viejo_lider_proyecto_tupla:
                viejo_lider_proyecto_id = viejo_lider_proyecto_tupla.id_lider
                ficha = DBSession.query(Ficha).filter(Ficha.id_proyecto == \
                      id_proyecto).filter(Ficha.id_usuario == \
                      viejo_lider_proyecto_id).filter(Ficha.id_rol == u'RL3') \
                      .scalar()
                if ficha:
                    usuario = DBSession.query(Usuario).filter(Usuario.id == \
                            id_lider).one()
                    ids_fichas = DBSession.query(Ficha.id).filter(Ficha. \
                                id_usuario == id_lider).all()
                    if ids_fichas:
                        proximo_id_ficha = proximo_id(ids_fichas)
                    else:
                        proximo_id_ficha = "FI1-" + id_lider
                    ficha.id = proximo_id_ficha
                    ficha.usuario = usuario
                    DBSession.add(ficha)
                else:
                    ids_fichas = DBSession.query(Ficha.id).filter(Ficha.\
                                id_usuario == id_lider).all()
                    rol = DBSession.query(Rol).filter(Rol.id == u'RL3').one()
                    proyecto = DBSession.query(Proyecto).filter(Proyecto.id \
                             == id_proyecto).one()
                    usuario = DBSession.query(Usuario).filter(Usuario.id == \
                             id_lider).one()
                    fi = Ficha()
                    fi.usuario = usuario
                    fi.rol = rol
                    fi.proyecto = proyecto
                    if ids_fichas:
                        proximo_id_ficha = proximo_id(ids_fichas)
                    else:
                        proximo_id_ficha = "FI1-" + id_lider
                    fi.id = proximo_id_ficha                      
                    DBSession.add(fi)

        else:
            viejo_lider_proyecto_tupla = DBSession.query(Proyecto.id_lider). \
                                       filter(Proyecto.id == id_proyecto).one()
            if viejo_lider_proyecto_tupla:
                viejo_lider_proyecto_id = viejo_lider_proyecto_tupla.id_lider
                ficha_lider_a_eliminar = DBSession.query(Ficha).filter \
                                        (Ficha.id_proyecto == id_proyecto). \
                                        filter(Ficha.id_usuario == \
                                        viejo_lider_proyecto_id).filter \
                                        (Ficha.id_rol == u'RL3').scalar()
                DBSession.delete(ficha_lider_a_eliminar)
        proyecto_modificado.lider = usuario
        proyecto_modificado.nombre = kw["nombre"]
        proyecto_modificado.descripcion = kw["descripcion"]
        proyecto_modificado.nro_fases = kw["nro_fases"]
        
        redirect('../')

