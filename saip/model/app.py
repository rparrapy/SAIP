# -*- coding: utf-8 -*-
"""Modulo de modelo: proyecto."""

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relation, backref

from saip.model import DeclarativeBase, metadata, DBSession

class Proyecto(DeclarativeBase):
    """ Clase correspondiente a un proyecto del sistema, 
    mapeada a la tabla proyectos de forma declarativa. """ 

    __tablename__ = 'proyectos'
    id = Column(String, primary_key = True)
    nombre = Column(String, nullable = False)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    descripcion = Column(String)
    estado = Column(String, nullable = False)

    
    def __init__(self, id, nombre, fecha_inicio, fecha_fin, estado, descripcion = ""):
        """ Constructor de la clase proyecto."""

        self.id = id
        self.nombre = nombre
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.descripcion = descripcion
        self.estado = estado

    def agregar_fase(self, fase):
        """ Permite agregar una fase al proyecto dado. """
        
        self.fases.append(fase)


class Fase(DeclarativeBase):
    """ Clase correspondiente a un fase del sistema, 
    mapeada a la tabla fases de forma declarativa. """ 

    __tablename__ = 'fases'
    id = Column(String, primary_key = True)
    nombre = Column(String, nullable = False)
    orden = Column(String, nullable = False)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    descripcion = Column(String)
    estado = Column(String, nullable = False)
    id_proyecto = Column(String, ForeignKey("proyectos.id"))
    
    proyecto = relation("Proyecto", backref = backref('fases', order_by=id))

    def __init__(self, id, nombre, orden, fecha_inicio, fecha_fin, estado, proyecto = "", descripcion = ""):
        """ Constructor de la clase fase."""

        self.id = id
        self.nombre = nombre
        self.orden = orden
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.descripcion = descripcion
        self.estado = estado
        self.proyecto = proyecto

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
    id = Column(String, primary_key = True)
    nombre = Column(String, nullable = False)
    descripcion = Column(String)
    id_fase = Column(String, ForeignKey("fases.id"))
    
    fase = relation("Fase", backref = backref('tipos_item', order_by=id))

    def __init__(self, id, nombre, fase = "", descripcion = ""):
        """ Constructor de la clase tipo de item."""

        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.fase = fase

    def agregar_caracteristica(self, caracteristica):
        """ Permite agregar una carateristica al tipo de item dado. """
        
        self.caracteristicas.append(caracteristica)


class Caracteristica(DeclarativeBase):
    """ Clase correspondiente a una caracteristica del sistema, 
    mapeada a la tabla caracteristicas de forma declarativa. """ 

    __tablename__ = 'caracteristicas'
    id = Column(String, primary_key = True)
    nombre = Column(String, nullable = False)
    tipo = Column(String)
    descripcion = Column(String)    
    id_tipo_item = Column(String, ForeignKey("tipos_item.id"))
    
    tipo_item = relation("TipoItem", backref = backref('caracteristicas', order_by=id))

    def __init__(self, id, nombre, tipo, tipo_item = "", descripcion = ""):
        """ Constructor de la clase caracteristica."""

        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.tipo_item = tipo_item
        self.descripcion = descripcion


class LineaBase(DeclarativeBase):
    """ Clase correspondiente a una linea base del sistema, 
    mapeada a la tabla lineas_base de forma declarativa. """ 

    __tablename__ = 'lineas_base'
    id = Column(String, primary_key = True)
    descripcion = Column(String)
    estado = Column(String, nullable = False)
    id_fase = Column(String, ForeignKey("fases.id"))
    
    fase = relation("Fase", backref = backref('lineas_base', order_by=id))

    def __init__(self, id, nombre, estado, fase = "", descripcion = ""):
        """ Constructor de la clase linea base."""

        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.estado = estado
        self.fase = fase


    def agregar_item(self, item):
        """ Permite agregar un item a la linea base dada. """
        
        self.items.append(item)


class Item(DeclarativeBase):
    """ Clase correspondiente a un item del sistema, 
    mapeada a la tabla items de forma declarativa. """ 

    __tablename__ = 'items'
    id = Column(String, primary_key = True)
    nombre = Column(String, nullable = False)
    descripcion = Column(String)
    estado = Column(String, nullable = False)
    anexo = Column(String)
    observaciones = Column(String)
    prioridad = Column(Integer, nullable = False)
    complejidad = Column(Integer, nullable = False)
    id_tipo_item = Column(String, ForeignKey("tipos_item.id"))
    id_linea_base = Column(String, ForeignKey("lineas_base.id"))    

    tipo_item = relation("TipoItem", backref = backref('items', order_by=id))
    linea_base = relation("LineaBase", backref = backref('items', order_by=id))    
   
    def __init__(self, id, nombre, estado, prioridad, complejidad, descripcion = "", anexo = "", observaciones = ""):
        """ Constructor de la clase item."""

        self.id = id
        self.nombre = nombre
        self.prioridad = prioridad
        self.complejidad = complejidad
        self.estado = estado
        self.descripcion = descripcion
        self.anexo = anexo
        self.observaciones = observaciones

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
    id = Column(String, primary_key = True)
    nombre = Column(String)
    contenido = Column(LargeBinary)    
    id_item = Column(String, ForeignKey("items.id"))
    
    item = relation("Item", backref = backref('archivos', order_by=id))

    def __init__(self, id, nombre, item = "", contenido = ""):
        """ Constructor de la clase archivo."""

        self.id = id
        self.nombre = nombre
        self.item = item
        self.contenido = contenido        


class Relacion(DeclarativeBase):
    """ Clase correspondiente a una relacion del sistema, 
    mapeada a la tabla relaciones de forma declarativa. """ 

    __tablename__ = 'relaciones'
    id = Column(String, primary_key = True)
    id_item_1 = Column(String, ForeignKey("items.id"))
    id_item_2 = Column(String, ForeignKey("items.id"))    
    
    item_1 = relation("Item", primaryjoin=(id_item_1==Item.id))
    item_2 = relation("Item", primaryjoin=(id_item_2==Item.id))

    def __init__(self, id, item_1, item_2):
        """ Constructor de la clase revision."""

        self.id = id
        self.item_1 = item_1
        self.item_2 = item_2        


class Revision(DeclarativeBase):
    """ Clase correspondiente a una revision del sistema, 
    mapeada a la tabla revisiones de forma declarativa. """ 

    __tablename__ = 'revisiones'
    id = Column(String, primary_key = True)
    descripcion = Column(String)    
    id_item = Column(String, ForeignKey("items.id"))
    
    item = relation("Item", backref = backref('revisiones', order_by=id))

    def __init__(self, id, item = "", descripcion = ""):
        """ Constructor de la clase revision."""

        self.id = id
        self.item = item
        self.descripcion = descripcion        
