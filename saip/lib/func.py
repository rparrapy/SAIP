# -*- coding: utf-8 -*-
from saip.model import DBSession, Item, Fase, Proyecto, LineaBase
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


def estado_fase(fase):
    finalizada = True
    items = list()
    for tipo in fase.tipos_item:
        items.append(tipo.items)
    for item in reversed(items):
            for item_2 in reversed(items):
                if item is not item_2  and item.id == item_2.id : 
                    if item.version > item_2.version: 
                        items.remove(item_2)
                    else:
                        items.remove(item) 
    finalizada = True
    lb_total = True
    lb_parcial = False
    for item in items:
        if lb_total or not lb_parcial: #si todavía no se encontró al menos un item fuera y un item dentro de una LB
            if item.linea_base:
                if item.linea_base.cerrada:
                    lb_parcial = True
                    if lb_total and not sucesor(item):
                        finalizada = False
                else:
                    lb_total = False
                    finalizada = False
            else: lb_total =  False
                  finalizada = False
    
    if finalizada: 
        fase.estado = u"Finalizada"
    elif lb_total:
        fase.estado = u"Linea Base Total"
    elif lb_parcial:
        fase.estado = u"Linea Base Parcial"
    elif items:
        fase.estado = u"En Desarrollo"
    else:
        fase.estado = u"Inicial"

    

def sucesor(item):
    band = False
    for relacion in item.relaciones_a:
        if not relacion.item_2.fase == item.fase: band = True
    return band 


def estado_proyecto(proyecto):
    finalizado = True
    for fase in proyecto.fases:
        if not fase.estado == u"Finalizada":
            finalizado = False
            break
    if finalizado: proyecto.estado = u"Finalizado"

def consistencia_lb(lb):
    consistente = True
    items = [x for x in lb.items if x.borrado is not True]    
    for item in reversed(items):
            for item_2 in reversed(items):
                if item is not item_2  and item.id == item_2.id : 
                    if item.version > item_2.version: 
                        items.remove(item_2)
                    else:
                        items.remove(item) 
    for item in items:
        if not item.estado == u"Aprobado":
            consistente = False
            break
    if consistente: 
        lb.consistente = True
    else:
        lb.consistente = False

     
