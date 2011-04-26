# -*- coding: utf-8 -*-
"""Modulo de modelo: revision. """

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relation, backref

from saip.model import DeclarativeBase, metadata, DBSession


class Revision(DeclarativeBase):
    """ Clase correspondiente a una revision del sistema, 
    mapeada a la tabla revisiones de forma declarativa. """ 

    __tablename__ = 'revisiones'
    id = Column(String, primary_key = True
    descripcion = Column(String)    
    id_item = Column(String, ForeignKey("items.id"))
    
    item = relation(Item, backref = backref('revisiones', order_by=id))

    def __init__(self, id, item = "", descripcion = ""):
    """ Constructor de la clase revision."""

        self.id = id
        self.item = item
        self.descripcion = descripcion        


