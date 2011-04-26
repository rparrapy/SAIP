# -*- coding: utf-8 -*-
"""Modulo de modelo: item."""

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relation, backref

from saip.model import DeclarativeBase, metadata, DBSession


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

    tipo_item = relation(TipoItem, backref = backref('caracteristicas', order_by=id))
    linea_base = relation(LineaBase, backref = backref('items', order_by=id))    
    archivos = relation(Archivo, order_by = Archivo.id, backref = "item")
    revisiones = relation(Revision, order_by = Revision.id, backref = "item")
    
        
    

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


