# -*- coding: utf-8 -*-
from saip.model import DBSession, Item
from sqlalchemy import func
import pydot

def opuesto(arista, nodo):
    if nodo == arista.item_1:
        return arista.item_2
    if nodo == arista.item_2:
        return arista.item_1
    
def forma_ciclo(nodo, nodos_explorados = [], aristas_exploradas = [] , band = False, nivel = 1):
    #aux = list()
    #aux.append(relacion)
    #if nodo == relacion.item_1:
    #    aristas = nodo.relaciones_a + aux
    #else:
    aristas = nodo.relaciones_a
    nodos_explorados.append(nodo)
    for arista in aristas:
        if arista not in aristas_exploradas:
            aristas_exploradas.append(arista)
            nodo_b = opuesto(arista, nodo)
            nivel = nivel + 1
            band = forma_ciclo(nodo_b, nodos_explorados, aristas_exploradas, band, nivel)
        else:
                return True
        if band: return band
    return False


def costo_impacto(nodo, grafo, nodos_explorados = [], aristas_exploradas = [], costo = 0): 
    aristas = nodo.relaciones_a + nodo.relaciones_b   
    nodos_explorados.append(nodo)
    for arista in aristas:
        if arista not in aristas_exploradas:
            aristas_exploradas.append(arista)                
            grafo.add_edge(pydot.Edge(arista.item_1.id, arista.item_2.id))
            nodo_b = opuesto(arista, nodo)
            if nodo_b not in nodos_explorados:                                     
                costo, grafo = costo_impacto(nodo_b, grafo, nodos_explorados, aristas_exploradas, costo)
    return costo + nodo.complejidad, grafo


