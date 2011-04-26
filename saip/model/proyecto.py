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

    fases = relation(Fase, order_by = Fase.id, backref = "proyecto")    
    

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

