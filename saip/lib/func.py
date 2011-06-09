# -*- coding: utf-8 -*-
from saip.model import DBSession, Item, Fase, Proyecto, LineaBase
from sqlalchemy import func
import pydot

def opuesto(arista, nodo):
    if nodo == arista.item_1:
        return arista.item_2
    if nodo == arista.item_2:
        return arista.item_1

def relaciones_a_actualizadas(aristas):
    aux = []
    for arista in aristas:
        for arista_2 in aristas:
            if arista.item_2.id == arista_2.item_2.id: 
                if arista.item_2.version > arista_2.item_2.version: 
                    aux.append(arista_2)
                elif arista.item_2.version < arista_2.item_2.version :
                    aux.append(arista)
    aristas = [a for a in aristas if a not in aux]
    return aristas

def relaciones_b_actualizadas(aristas):
    aux = []
    for arista in aristas:
        for arista_2 in aristas:
            if arista.item_1.id == arista_2.item_1.id: 
                if arista.item_1.version > arista_2.item_1.version: 
                    aux.append(arista_2)
                elif arista.item_1.version < arista_2.item_1.version :
                    aux.append(arista)
    aristas = [a for a in aristas if a not in aux]
    return aristas


def forma_ciclo(nodo, nodos_explorados = [], aristas_exploradas = [] , band = False, nivel = 1):
    #aux = list()
    #aux.append(relacion)
    #if nodo == relacion.item_1:
    #    aristas = nodo.relaciones_a + aux
    #else:
    aristas = relaciones_a_actualizadas(nodo.relaciones_a)
    #for arista in aristas:
    #    print arista.item_2.id + unicode(arista.item_2.version) + unicode(nivel)
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
    aristas = relaciones_a_actualizadas(nodo.relaciones_a) + relaciones_b_actualizadas(nodo.relaciones_b)
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
            else: 
                  lb_total =  False
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
    if not proyecto.fases:
        finalizado = False
    if finalizado: proyecto.estado = u"Finalizado"

def consistencia_lb(lb):
    consistente = True
    items = [x for x in lb.items if x.borrado is not True]
    aux = list()  
    for item in items:
            for item_2 in items:
                if item is not item_2  and item.id == item_2.id : 
                    if item.version > item_2.version: 
                        aux.append(item_2)
                    else:
                        aux.append(item)
    for item in aux:
        items.remove(item) 
    for item in items:
        if not item.estado == u"Aprobado":
            consistente = False
            break
    if consistente: 
        lb.consistente = True
    else:
        lb.consistente = False

def proximo_id(lista_ids):
    num_max = 0
    for un_id in lista_ids:
        primera_parte = un_id.id.split("-")[0]
        el_resto = un_id.id.split("-")[1:]
        el_resto_unido = "-".join(el_resto)
        num_id = int(primera_parte[2:])
        if num_id > num_max:
            num_max = num_id
    id_final = primera_parte[0:2] + unicode(num_max + 1)
    if el_resto_unido:
        id_final = id_final + "-" + el_resto_unido
    return id_final



