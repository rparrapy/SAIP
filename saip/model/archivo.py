# -*- coding: utf-8 -*-
"""Modulo de modelo: archivo. """

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relation, backref

from saip.model import DeclarativeBase, metadata, DBSession


class Archivo(DeclarativeBase):
    """ Clase correspondiente a una archivo del sistema, 
    mapeada a la tabla archivos de forma declarativa. """ 

    __tablename__ = 'archivos'
    id = Column(String, primary_key = True
    nombre = Column(String)
    contenido = Column(LargeBinary)    
    id_item = Column(String, ForeignKey("items.id"))
    
    item = relation(Item, backref = backref('archivos', order_by=id))

    def __init__(self, id, nombre, item = "", contenido = ""):
    """ Constructor de la clase archivo."""

        self.id = id
        self.nombre = nombre
        self.item = item
        self.contenido = contenido        


