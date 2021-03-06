# -*- coding: utf-8 -*-
"""
Controlador de Fichas de fase en el módulo de administración.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""
from tgext.crud import CrudRestController
from saip.model import DBSession, Ficha, Usuario, Rol, Proyecto, Fase
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import AddRecordForm
from tg import tmpl_context
from tg import expose, require, request, redirect, flash
from tg.decorators import with_trailing_slash, paginate, without_trailing_slash  
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso
from tg import request
from sqlalchemy import func
from sprox.widgets import PropertySingleSelectField
from saip.lib.func import proximo_id


class FichaTable(TableBase):
    """ Define el formato de la tabla"""
    __model__ = Ficha
    __field_order__ = ['id','usuario', 'rol', 'proyecto', 'fase']
    __omit_fields__ = ['id_fase','id_fase','id_usuario','id_rol']
ficha_table = FichaTable(DBSession)

class FichaTableFiller(TableFiller):
    """
    Clase que se utiliza para llenar las tablas.
    """
    __model__ = Ficha
    buscado=""
    id_fase = ""    
    def init(self,buscado, id_fase):
        self.buscado=buscado
        self.id_fase = id_fase

    def __actions__(self, obj):
        """
        Define las acciones posibles para cada ficha.
        """
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'
        fase = DBSession.query(Fase).get(self.id_fase)
        permiso_asignar_rol_cualquier_fase = TienePermiso \
                            ("asignar rol cualquier fase", id_proyecto = \
                            fase.id_proyecto).is_met(request.environ)
        permiso_asignar_rol_fase = TienePermiso("asignar rol fase", id_fase = \
                                    self.id_fase).is_met(request.environ)
        if permiso_asignar_rol_fase or permiso_asignar_rol_cualquier_fase:
            value = value + '<div>'\
              '<form method="POST" action="'+pklist+'" class="button-to">'\
              '<input type="hidden" name="_method" value="DELETE" />'\
              '<input class="delete-button" onclick="return confirm' \
              '(\'Está seguro?\');" value="delete" type="submit" '\
              'style="background-color: transparent; float:left; border:0;' \
              ' color: #286571; display: inline; margin: 0; padding: 0;"/>'\
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
        """
        Se utiliza para listar solo las fichas que cumplan ciertas
        condiciones y de acuerdo a ciertos permisos.
        """
        if self.id_fase == "":
            fichas = DBSession.query(Ficha) \
                    .filter(Ficha.id.contains(self.buscado)).all()    
        else:
            id_proyecto = self.id_fase.split("-")[1]
            permiso_asignar_rol_fase = TienePermiso("asignar rol fase", \
                        id_fase = self.id_fase).is_met(request.environ)
            permiso_asignar_rol_cualquier_fase = TienePermiso( \
                    "asignar rol cualquier fase", id_proyecto = \
                    id_proyecto).is_met(request.environ)
            if permiso_asignar_rol_fase or permiso_asignar_rol_cualquier_fase:
                fichas = DBSession.query(Ficha).filter(Ficha.id_fase == \
                self.id_fase).all()
                for ficha in reversed(fichas):
                    if ficha.rol.tipo != u"Fase": 
                        fichas.remove(ficha)
                    elif not (self.buscado in ficha.usuario.nombre_usuario or \
                        self.buscado in ficha.rol.nombre or self.buscado in \
                        ficha.id or self.buscado in ficha.proyecto.nombre or \
                        self.buscado in ficha.fase.nombre): fichas.remove(ficha)
                    
            else: fichas = list()
        return len(fichas), fichas 
ficha_table_filler = FichaTableFiller(DBSession)

class RolesField(PropertySingleSelectField):
    """Clase para obtener los roles de fase existentes."""
    def _my_update_params(self, d, nullable=False):
         roles = DBSession.query(Rol).filter(Rol.tipo == "Fase")
         d['options'] = [(rol.id, '%s'%(rol.nombre)) for rol in roles]
         return d
            

class AddFicha(AddRecordForm):
    """ Define el formato del formulario para crear una nueva ficha"""
    __model__ = Ficha
    __omit_fields__ = ['proyecto','fase','id']
    rol = RolesField
    __dropdown_field_names__ = {'rol':'nombre', 'usuario':'nombre_usuario'}
add_ficha_form = AddFicha(DBSession)


class FichaFaseController(CrudRestController):
    """Controlador de fichas de fases"""
    model = Ficha
    table = ficha_table
    table_filler = ficha_table_filler  
    new_form = add_ficha_form


    def _before(self, *args, **kw):
        self.id_fase = unicode(request.url.split("/")[-3])
        super(FichaFaseController, self)._before(*args, **kw)
    
    def get_one(self, Ficha_id):
        tmpl_context.widget = Ficha_table
        ficha = DBSession.query(Ficha).get(Ficha_id)
        value = fase_table_filler.get_value(Ficha=ficha)
        return dict(Ficha=ficha, value=value, accion = "./")

    @with_trailing_slash
    @expose("saip.templates.get_all")
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def get_all(self, *args, **kw):
        """
        Lista las fichas existentes de acuerdo a condiciones establecidas 
        en L{ficha_fase_controller.FichaTableFiller
        ._do_get_provider_count_and_objs}.
        """  
        ficha_table_filler.init("", self.id_fase)
        d = super(FichaFaseController, self).get_all(*args, **kw)
        id_proyecto = self.id_fase.split("-")[1]
        existe_rol = DBSession.query(Rol).filter(Rol.tipo == u'Fase').count()
        d["permiso_crear"] = (TienePermiso("asignar rol fase", id_fase = \
                self.id_fase).is_met(request.environ) or TienePermiso( \
                "asignar rol cualquier fase", id_proyecto = id_proyecto) \
                .is_met(request.environ)) and existe_rol
        d["model"] = "Responsables"
        d["accion"] = "./buscar"
        d["direccion_anterior"] = "../.."
        return d

    @without_trailing_slash
    @expose('tgext.crud.templates.new')
    def new(self, *args, **kw):
        """
        Despliega una página para la creación de una nueva ficha de fase.
        """
        id_proyecto = self.id_fase.split("-")[1]
        permiso_asignar_rol_fase = TienePermiso("asignar rol fase", \
                id_fase = self.id_fase).is_met(request.environ)
        permiso_asignar_rol_cualquier_fase = TienePermiso( \
                "asignar rol cualquier fase", id_proyecto = id_proyecto) \
                .is_met(request.environ)
        if permiso_asignar_rol_fase or permiso_asignar_rol_cualquier_fase:
            d = super(FichaFaseController, self).new(*args, **kw)
            d["direccion_anterior"] = "./"
            return d
        else:
            flash(u"El usuario no cuenta con los permisos necesarios", \
                u"error")
            raise redirect('./')

    def edit(self, *args, **kw):
        pass         
    
    @with_trailing_slash
    @expose('saip.templates.get_all')
    @expose('json')
    @paginate('value_list', items_per_page=7)
    def buscar(self, **kw):
        """
        Lista las fichas de fase de acuerdo a un criterio de búsqueda 
        introducido por el usuario.
        """
        id_proyecto = self.id_fase.split("-")[1]
        existe_rol = DBSession.query(Rol).filter(Rol.tipo == u'Fase').count()
        buscar_table_filler = FichaTableFiller(DBSession)
        if "parametro" in kw:
            buscar_table_filler.init(kw["parametro"], self.id_fase)
        else:
           buscar_table_filler.init("",self.id_fase)
        tmpl_context.widget = self.table
        value = buscar_table_filler.get_value()
        d = dict(value_list=value, model="Responsables", accion = "./buscar")
        d["permiso_crear"] = (TienePermiso("asignar rol fase", id_fase = \
                self.id_fase).is_met(request.environ) or TienePermiso( \
                "asignar rol cualquier fase", id_proyecto = id_proyecto) \
                .is_met(request.environ)) and existe_rol
        d["direccion_anterior"] = "../.."
        return d
    
    @expose()
    def post(self, **kw):
        """Registra la nueva ficha creada"""
        if not DBSession.query(Ficha).filter(Ficha.id_usuario == \
                kw['usuario']).filter(Ficha.id_rol == kw['rol']) \
                .filter(Ficha.id_fase == self.id_fase).count():
            f = Ficha()
            ids_fichas = DBSession.query(Ficha.id).filter(Ficha.id_usuario == \
                    kw['usuario']).all()
            if ids_fichas:        
                proximo_id_ficha = proximo_id(ids_fichas)
            else:
                proximo_id_ficha = "FI1-" + kw['usuario']
            f.id = proximo_id_ficha
            usuario = DBSession.query(Usuario).filter(Usuario.id == \
                kw['usuario']).one()
            rol = DBSession.query(Rol).filter(Rol.id ==  kw['rol']).one()
            fase = DBSession.query(Fase).filter(Fase.id == self.id_fase).one()
            proyecto = fase.proyecto
            f.usuario = usuario
            f.rol = rol
            f.proyecto = proyecto   
            f.fase = fase        
            DBSession.add(f)
        else:
            flash(u"La ficha ya existe", u"error")
        raise redirect('./')
