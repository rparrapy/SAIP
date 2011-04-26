# -*- coding: utf-8 -*-
"""Modulo de modelo: relacion. """

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relation, backref

from saip.model import DeclarativeBase, metadata, DBSession


class Relacion(DeclarativeBase):
    """ Clase correspondiente a una relacion del sistema, 
    mapeada a la tabla relaciones de forma declarativa. """ 

    __tablename__ = 'relaciones'
    id = Column(String, primary_key = True
    id_item__1 = Column(String, ForeignKey("items.id"))
    id_item__2 = Column(String, ForeignKey("items.id"))    
    
    item_1 = relation(Item)
    item_2 = relation(Item)

    def __init__(self, id, item_1, item_2):
    """ Constructor de la clase revision."""

        self.id = id
        self.item_1 = item_1
        self.item_2 = item_2        


