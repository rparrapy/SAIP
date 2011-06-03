# -*- coding: utf-8 -*-
"""Modulo de modelo: proyecto."""

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.orm import relation, backref

from saip.model import DeclarativeBase, metadata, DBSession

class Proyecto(DeclarativeBase):
    """ Clase correspondiente a un proyecto del sistema, 
    mapeada a la tabla proyectos de forma declarativa. """ 

    __tablename__ = 'proyectos'
    id = Column(Unicode, primary_key = True)
    nombre = Column(Unicode, nullable = False)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    descripcion = Column(Unicode)
    estado = Column(Unicode, nullable = False)
    nro_fases = Column(Integer, nullable = False)

    def agregar_fase(self, fase):
        """ Permite agregar una fase al proyecto dado. """
        
        self.fases.append(fase)


class Fase(DeclarativeBase):
    """ Clase correspondiente a un fase del sistema, 
    mapeada a la tabla fases de forma declarativa. """ 

    __tablename__ = 'fases'
    id = Column(Unicode, primary_key = True)
    nombre = Column(Unicode, nullable = False)
    orden = Column(Integer, nullable = False)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    descripcion = Column(Unicode)
    estado = Column(Unicode, nullable = False)
    id_proyecto = Column(Unicode, ForeignKey("proyectos.id"))
    
    proyecto = relation("Proyecto", backref = backref('fases',cascade="all,delete,delete-orphan", order_by=id))

    
    def agregar_tipo_item(self, tipo_item):
        """ Permite agregar un tipo de item a la fase dada. """
        
        self.tipos_item.append(tipo_item)

    def agregar_item(self, item):
        """ Permite agregar un item a la fase dada. """
        
        self.items.append(item)

    def agregar_linea_base(self, lb):
        """ Permite agregar un item a la fase dada. """
        
        self.lineas_base.append(lb)


class TipoItem(DeclarativeBase):
    """ Clase correspondiente a un tipo de item del sistema, 
    mapeada a la tabla tipos_item de forma declarativa. """ 

    __tablename__ = 'tipos_item'
    id = Column(Unicode, primary_key = True)
    nombre = Column(Unicode, nullable = False)
    descripcion = Column(Unicode)
    id_fase = Column(Unicode, ForeignKey("fases.id"))
    
    fase = relation("Fase", backref = backref('tipos_item', cascade="all,delete,delete-orphan", order_by=id))

    def agregar_caracteristica(self, caracteristica):
        """ Permite agregar una carateristica al tipo de item dado. """
        
        self.caracteristicas.append(caracteristica)


class Caracteristica(DeclarativeBase):
    """ Clase correspondiente a una caracteristica del sistema, 
    mapeada a la tabla caracteristicas de forma declarativa. """ 

    __tablename__ = 'caracteristicas'
    id = Column(Unicode, primary_key = True)
    nombre = Column(Unicode, nullable = False)
    tipo = Column(Unicode)
    descripcion = Column(Unicode)    
    id_tipo_item = Column(Unicode, ForeignKey("tipos_item.id"))
    
    tipo_item = relation("TipoItem", backref = backref('caracteristicas', cascade="all,delete,delete-orphan", order_by=id))

    


class LineaBase(DeclarativeBase):
    """ Clase correspondiente a una linea base del sistema, 
    mapeada a la tabla lineas_base de forma declarativa. """ 

    __tablename__ = 'lineas_base'
    id = Column(Unicode, primary_key = True)
    descripcion = Column(Unicode)
    estado = Column(Unicode, nullable = False)
    id_fase = Column(Unicode, ForeignKey("fases.id"))
    
    fase = relation("Fase", backref = backref('lineas_base', cascade="all,delete,delete-orphan", order_by=id))


    def agregar_item(self, item):
        """ Permite agregar un item a la linea base dada. """
        
        self.items.append(item)


class Item(DeclarativeBase):
    """ Clase correspondiente a un item del sistema, 
    mapeada a la tabla items de forma declarativa. """ 

    __tablename__ = 'items'
    id = Column(Unicode, primary_key = True)
    version = Column(Integer, primary_key = True)
    nombre = Column(Unicode, nullable = False)
    descripcion = Column(Unicode)
    estado = Column(Unicode, nullable = False)
    anexo = Column(Unicode)
    observaciones = Column(Unicode)
    prioridad = Column(Integer, nullable = False)
    complejidad = Column(Integer, nullable = False)
    borrado = Column(Boolean)
    id_tipo_item = Column(Unicode, ForeignKey("tipos_item.id"))
    id_linea_base = Column(Unicode, ForeignKey("lineas_base.id"))    

    tipo_item = relation("TipoItem", backref = backref('items', cascade="all,delete,delete-orphan", order_by=id))
    linea_base = relation("LineaBase",backref = backref('items', order_by=id))    
   
    
    def agregar_archivo(self, archivo):
        """ Permite agregar un archivo al item dado. """
        
        self.archivos.append(archivo)

    def agregar_revision(self, revision):
        """ Permite agregar un archivo al item dado. """
        
        self.revisiones.append(revision)



class Archivo(DeclarativeBase):
    """ Clase correspondiente a una archivo del sistema, 
    mapeada a la tabla archivos de forma declarativa. """ 

    __tablename__ = 'archivos'
    id = Column(Unicode, primary_key = True)
    nombre = Column(Unicode)
    contenido = Column(LargeBinary)    
    
    items = relation("Item", secondary = "item_archivo", backref = backref('archivos', cascade="all,delete", order_by=id))


class Item_Archivo(DeclarativeBase):
    
    __tablename__ = 'item_archivo'
    __table_args__ = (ForeignKeyConstraint(['id_item', 'version_item'], ['items.id', 'items.version']), {})
    
    id_item = Column(Unicode, primary_key=True)
    version_item = Column(Integer, primary_key=True)
    id_archivo = Column(Unicode, ForeignKey('archivos.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)  
    
        


class Relacion(DeclarativeBase):
    """ Clase correspondiente a una relacion del sistema, 
    mapeada a la tabla relaciones de forma declarativa. """ 

    __tablename__ = 'relaciones'
    __table_args__ = (ForeignKeyConstraint(['id_item_1', 'version_item_1'], ['items.id', 'items.version']), \
                      ForeignKeyConstraint(['id_item_2', 'version_item_2'], ['items.id', 'items.version']),{}) 

    id = Column(Unicode, primary_key = True)
    id_item_1 = Column(Unicode)
    version_item_1 = Column(Integer)
    id_item_2 = Column(Unicode)
    version_item_2 = Column(Integer)    
    
    item_1 = relation("Item", primaryjoin = and_(id_item_1 == Item.id, version_item_1 == Item.version), backref = backref('relaciones_a', cascade="all,delete,delete-orphan"))
    
    item_2 = relation("Item", primaryjoin = and_(id_item_2 == Item.id, version_item_2 == Item.version), backref = backref('relaciones_b', cascade="all,delete,delete-orphan")


class Revision(DeclarativeBase):
    """ Clase correspondiente a una revision del sistema, 
    mapeada a la tabla revisiones de forma declarativa. """ 

    __tablename__ = 'revisiones'
    id = Column(Unicode, primary_key = True)
    descripcion = Column(Unicode)    
    id_item = Column(Unicode, ForeignKey("items.id"))
    
    item = relation("Item", backref = backref('revisiones', cascade="all,delete,delete-orphan", order_by=id))
