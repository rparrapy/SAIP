# -*- coding: utf-8 -*-
from saip.model import DBSession, Item
from sqlalchemy import func

def opuesto(arista, nodo):
    if nodo == arista.item_1:
        return arista.item_2
    if nodo == arista.item_2:
        return arista.item_1
    
def forma_ciclo(nodo, relacion, nodos_explorados, aristas_exploradas, band):
    #nodo = DBSession.query(Item).filter(Item.id == id_item).order_by(fun.max(Item.version)).first()
    if nodo == relacion.item1:
        aristas = nodo.relaciones_a + relacion
    else:
        aristas = nodo.relaciones_a
    nodos_explorados.append(nodo)
    for arista in aristas:
        if band: return band
        if arista not in aristas_exploradas:
            nodo_b = opuesto(arista, nodo)
            band = forma_ciclo(nodo_b, nodos_explorados, aristas_exploradas, band)
        else:
                return True
    return False

def costo_impacto(nodo, nodos_explorados, aristas_exploradas, costo):
    aristas = nodo.relaciones_a    
    nodos_explorados.append(nodo)
    for arista in aristas:
        if arista not in aristas_exploradas:
            nodo_b = opuesto(arista, nodo)
            if nodo_b not in nodos_explorados:                                     
                costo = costo_impacto(nodo_b, nodos_explorados, aristas_exploradas, costo)
    return costo + nodo.complejidad


