from tgext.crud import CrudRestController
from saip.model import DBSession, Proyecto
from sprox.tablebase import TableBase #para manejar datos de prueba
from sprox.fillerbase import TableFiller #""
from sprox.formbase import AddRecordForm #para creacion
from tg import tmpl_context #templates
from tg import expose, require, request
import datetime
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller
from saip.lib.auth import TienePermiso

class ProyectoTable(TableBase): #para manejar datos de prueba
	__model__ = Proyecto
	__omit_fields__ = ['id', 'fases', 'fichas']
proyecto_table = ProyectoTable(DBSession)

class ProyectoTableFiller(TableFiller):#para manejar datos de prueba
	__model__ = Proyecto
proyecto_table_filler = ProyectoTableFiller(DBSession)

class AddProyecto(AddRecordForm):
    __model__ = Proyecto
    __omit_fields__ = ['id', 'fases', 'fichas']
add_proyecto_form = AddProyecto(DBSession)

class EditProyecto(EditableForm):
    __model__ = Proyecto
    __omit_fields__ = ['id', 'fases', 'fichas']
edit_proyecto_form = EditProyecto(DBSession)

class ProyectoEditFiller(EditFormFiller):
    __model__ = Proyecto
proyecto_edit_filler = ProyectoEditFiller(DBSession)

class ProyectoController(CrudRestController):

    model = Proyecto
    table = proyecto_table
    table_filler = proyecto_table_filler
    new_form = add_proyecto_form
    edit_filler = proyecto_edit_filler
    edit_form = edit_proyecto_form
    @expose("saip.templates.get_all")
    def get_all(self, *args, **kw):       
        d = super(ProyectoController, self).get_all(*args, **kw)
        d["permiso_crear"] = TienePermiso("manage").is_met(request.environ)
        return d

    @expose()
    @require(TienePermiso("manage"))
    def post(self, **kw):
        p = Proyecto()
        p.descripcion = kw['descripcion']
        p.nombre = kw['nombre']
        p.fecha_inicio = datetime.date(int(kw['fecha_inicio'][0:4]),int(kw['fecha_inicio'][5:7]),int(kw['fecha_inicio'][8:10]))
        p.fecha_fin = datetime.date(int(kw['fecha_fin'][0:4]),int(kw['fecha_fin'][5:7]),int(kw['fecha_fin'][8:10]))
        p.estado = kw['estado']
        p.nro_fases = int(kw['nro_fases'])
        contid = DBSession.query(Proyecto).count()
        p.id = "PR" + str(contid + 1)
        DBSession.add(p)

