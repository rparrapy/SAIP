# -*- coding: utf-8 -*-
"""Modulo de modelo: tipo de item."""

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relation, backref

from saip.model import DeclarativeBase, metadata, DBSession


class TipoItem(DeclarativeBase):
    """ Clase correspondiente a un tipo de item del sistema, 
    mapeada a la tabla tipos_item de forma declarativa. """ 

    __tablename__ = 'tipos_item'
    id = Column(String, primary_key = True)
    nombre = Column(String, nullable = False)
    descripcion = Column(String)
    id_fase = Column(String, ForeignKey("fases.id"))
    
    fase = relation(Fase, backref = backref('tipos_item', order_by=id))
    items = relation(Item, order_by = Item.id, backref("tipo_item")
    caracteristicas = relation(Item, order_by = Item.id, backref("tipo_item")

    def __init__(self, id, nombre, descripcion = "", fase = "", descripcion = ""):
    """ Constructor de la clase tipo de item."""

        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.fase = fase

    def agregar_caracteristica(self, caracteristica):
    """ Permite agregar una carateristica al tipo de item dado. """
        
        self.caracteristicas.append(caracteristica)



