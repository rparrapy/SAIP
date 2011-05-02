from tgext.crud import CrudRestController
from saip.model import DBSession, Proyecto
from sprox.tablebase import TableBase #para manejar datos de prueba
from sprox.fillerbase import TableFiller #""

class ProyectoTable(TableBase): #para manejar datos de prueba
	__model__ = Proyecto
	__omit_fields__ = ['id','fases']
proyecto_table = ProyectoTable(DBSession)

class ProyectoTableFiller(TableFiller):#para manejar datos de prueba
	__model__ = Proyecto
proyecto_table_filler = ProyectoTableFiller(DBSession)

class ProyectoController(CrudRestController):
	model = Proyecto
	table = proyecto_table
	table_filler = proyecto_table_filler
