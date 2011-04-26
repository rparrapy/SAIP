# -*- coding: utf-8 -*-
"""Modulo de modelo: caracteristica."""

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relation, backref

from saip.model import DeclarativeBase, metadata, DBSession


class Caracteristica(DeclarativeBase):
    """ Clase correspondiente a una caracteristica del sistema, 
    mapeada a la tabla caracteristicas de forma declarativa. """ 

    __tablename__ = 'caracteristicas'
    id = Column(String, primary_key = True)
    nombre = Column(String, nullable = False)
    tipo = Column(String)
    descripcion = Column(String)    
    id_tipo_item = Column(String, ForeignKey("tipos_item.id"))
    
    tipo_item = relation(TipoItem, backref = backref('caracteristicas', order_by=id))

    def __init__(self, id, nombre, tipo, tipo_item = "", descripcion = ""):
    """ Constructor de la clase caracteristica."""

        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.tipo_item = tipo_item
        self.descripcion = descripcion


