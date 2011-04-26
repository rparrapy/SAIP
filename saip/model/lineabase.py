# -*- coding: utf-8 -*-
"""Modulo de modelo: linea base."""

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relation, backref

from saip.model import DeclarativeBase, metadata, DBSession


class LineaBase(DeclarativeBase):
    """ Clase correspondiente a una linea base del sistema, 
    mapeada a la tabla lineas_base de forma declarativa. """ 

    __tablename__ = 'lineas_base'
    id = Column(String, primary_key = True)
    descripcion = Column(String)
    estado = Column(String, nullable = False)
    id_fase = Column(String, ForeignKey("fases.id"))
    
    fase = relation(Fase, backref = backref('lineas_base', order_by=id))
    items = relation(Item, order_by = Item.id, backref = "linea_base")

    def __init__(self, id, nombre, estado, fase = "", descripcion = ""):
    """ Constructor de la clase linea base."""

        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.estado = estado
        self.fase = fase


