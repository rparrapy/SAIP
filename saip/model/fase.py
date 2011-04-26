# -*- coding: utf-8 -*-
"""Modulo de modelo: fase."""

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relation, backref

from saip.model import DeclarativeBase, metadata, DBSession


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
    
    proyecto = relation(Proyecto, backref = backref('fases', order_by=id))
    tipos_item = relation(TipoItem, order_by = TipoItem.id, backref = "fase")    
    items = relation(Item, order_by = Item.id, backref = "fase")
    lineas_base = relation(LineaBase, order_by = LineaBase.id, backref = "fase")

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


