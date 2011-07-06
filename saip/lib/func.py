# -*- coding: utf-8 -*-

"""

Módulo que provee funciones varias para la utilización en los controladores.

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""


from saip.model import DBSession, Item, Fase, Proyecto, LineaBase
from sqlalchemy import func, desc
import pydot
import datetime



def opuesto(arista, nodo):
    """
    Devuelve el otro item correspondiente a una relación

    @param arista: Relación que se analizará
    @type arista: L{Relacion}
    @param nodo: Item conocido de la relación
    @type nodo: L{Item}
    @return: El otro item correspondiente a la relación, es decir, el que no
             se recibió como parámetro
    @rtype: L{Item}
    """
    if nodo == arista.item_1:
        return arista.item_2
    if nodo == arista.item_2:
        return arista.item_1

def relaciones_a_actualizadas(aristas):
    """
    Provee la lista de relaciones actualizadas 
    (con el hijo/sucesor en su versión actual)
    a partir de una lista de relaciones .

    @param aristas: lista de relaciones
    @type aristas: list(L{Relacion})
    @return: lista filtrada de relaciones con el item hijo/sucesor en su
             en su versión actual
    @rtype: list(L{Relacion})  
    """
    lista = list()
    for arista in reversed(aristas):
        aux = DBSession.query(Item).filter(Item.id == arista.item_2.id)\
              .order_by(desc(Item.version)).first()
        if aux.version == arista.item_2.version:
            lista.append(arista)
    return lista

def relaciones_b_actualizadas(aristas):
    """
    Provee la lista de relaciones actualizadas 
    (con el padre/antecesor en su versión actual)
    a partir de una lista de relaciones .

    @param aristas: lista de relaciones
    @type aristas: list(L{Relacion})
    @return: lista filtrada de relaciones con el item hijo/sucesor en su
             en su versión actual
    @rtype: list(L{Relacion})  
    """
    lista = list()
    for arista in reversed(aristas):
        aux = DBSession.query(Item).filter(Item.id == arista.item_1.id) \
              .order_by(desc(Item.version)).first()
        if aux.version == arista.item_1.version:
            lista.append(arista)
    return lista

def es_huerfano(item):
    """
    Determina si un item es considerado huérfano o no.
    
    @param item: Item que se analizará
    @type item: L{Item}
    @return: True si el item es huérfano, False en caso contrario.
    @rtype: Bool
    """
    band = True
    if item.tipo_item.fase.orden == 1: return False
    for relacion in relaciones_b_actualizadas(item.relaciones_b):
        if relacion.item_1.tipo_item.fase != item.tipo_item.fase:
            band = False
            break            
    return band

def relaciones_a_recuperar(aristas):
    """
    Provee la lista de relaciones sin duplicados 
    (con el hijo/sucesor en la mayor versión presente en la lista recibida,
    por cada id_item) a partir de una lista de relaciones .

    @param aristas: lista de relaciones
    @type aristas: list(L{Relacion})
    @return: lista filtrada de relaciones con el item hijo/sucesor en la mayor
             versión presente en aristas
    @rtype: list(L{Relacion})  
    """
    aux = []
    for arista in aristas:
        for arista_2 in aristas:
            if arista.item_2.id == arista_2.item_2.id: 
                if arista.item_2.version > arista_2.item_2.version: 
                    aux.append(arista_2)
                elif arista.item_2.version < arista_2.item_2.version :
                    aux.append(arista)
    lista = [a for a in aristas if a not in aux]
    return lista

def relaciones_b_recuperar(aristas):
    """
    Provee la lista de relaciones sin duplicados 
    (con el padre/antecesor en la mayor versión presente en la lista recibida,
    por cada id_item) a partir de una lista de relaciones .

    @param aristas: lista de relaciones
    @type aristas: list(L{Relacion})
    @return: lista filtrada de relaciones con el item padre/antecesor en la
             mayor versión presente en aristas
    @rtype: list(L{Relacion})  
    """
    aux = []
    for arista in aristas:
        for arista_2 in aristas:
            if arista.item_1.id == arista_2.item_1.id: 
                if arista.item_1.version > arista_2.item_1.version: 
                    aux.append(arista_2)
                elif arista.item_1.version < arista_2.item_1.version :
                    aux.append(arista)
    lista = [a for a in aristas if a not in aux]
    return lista


def forma_ciclo(nodo, nodos_explorados = [], aristas_exploradas = [] , 
                band = False, nivel = 1):
    """
    Determina recursivamente si existe un ciclo en la componente conexa del grafo
    de items a la que pertenece un item dado.
    
    @param nodo: Item dado.(Normalmente acaba de añadírsele un relación)
    @type nodo: {Item}
    @param nodos_explorados: Lista de items que ya han sido visitados.
    @type nodos_explorados: list({Item})
    @param aristas_exploradas: Lista de relaciones visitadas.
    @type aristas_exploradas: list({Relacion})
    @param band: Bandera que indica si ya se ha encontrado un bucle.
    @type band: Bool
    @param nivel: Indica la cantidad de llamadas recursivas anidadas 
                  realizadas.
    @type nivel: Integer
    @return: True si existe un bucle, False en caso contrario.
    @rtype: Bool
    """
    if nivel == 1:
        aristas_exploradas = list()
    aristas = relaciones_a_actualizadas(nodo.relaciones_a)
    nodos_explorados.append(nodo)
    if aristas:
        for arista in aristas:
            if arista not in aristas_exploradas:
                aristas_exploradas.append(arista)
                nodo_b = opuesto(arista, nodo)
                nivel = nivel + 1
                band = forma_ciclo(nodo_b, nodos_explorados, aristas_exploradas, 
                                   band, nivel)

            else:    
                return True
            if band: return band
        return False
    else:
        return False

def color(nodo):
    """
    Determina el color que debe tener un item para la representación gráfica
    del costo de impacto basado en el orden de la fase a la que pertenece.
    
    @param nodo: Item a colorear.
    @type nodo: {Item}
    @return: El color que debe usarse para colorear el item.
    @rtype: String 
    """
    colores = ["white", "blue", "green", "yellow", "orange", "purple", \
               "pink", "gray", "brown"]
    if nodo.tipo_item.fase.proyecto.nro_fases > len(colores):
        return colores[0]
    else:
        return colores[nodo.tipo_item.fase.orden-1]        

def costo_impacto(nodo, grafo, nodos_explorados = [], aristas_exploradas = [], 
                  costo = 0, nivel = 1, camino = (), inicial = None):
    """
    Calcula recursivamente el costo de impacto de un item determinado y genera
    el grafo para la representación gráfica del resultado.

    @param nodo: Item dado
    @type nodo: {Item}
    @param grafo: Grafo que se utilizará para la representación gráfica de
                  resultados.
    @type grafo: grafo Pydot 
    @param nodos_explorados: Lista de items que ya han sido visitados.
    @type nodos_explorados: list({Item})
    @param aristas_exploradas: Lista de relaciones visitadas.
    @type aristas_exploradas: list({Relacion})
    @param costo: Suma de las complejidades de los items visitados.
    @type costo: Integer
    @param nivel: Indica la cantidad de llamadas recursivas anidadas 
                  realizadas.
    @type nivel: Integer
    @param camino: Guarda la secuencia exacta de fases que ya se ha recorrido.
    @type camino: tuple(Fase.orden)
    @param inicial: Indica el item sobre el cual se está calculando el costo de
                    impacto.
    @type inicial: {Item}
    @return: El costo de impacto y el grafo para representar el resultado.
    """
    if nodo.tipo_item.fase.orden not in camino:
        camino = camino + (nodo.tipo_item.fase.orden, )
    elif nodo.tipo_item.fase.orden != camino[-1]:
        return 0, grafo, False
        
    aristas = relaciones_a_actualizadas(nodo.relaciones_a) + \
              relaciones_b_actualizadas(nodo.relaciones_b)
    nodos_explorados.append(nodo)
    nombre_nodo = nodo.codigo + "/F = " + str(nodo.tipo_item.fase.orden) +  \
                  "/C = " + str(nodo.complejidad)
    if nivel == 1:
        col = "red"
        inicial = nodo
    else:
        col = color(nodo)
    n = pydot.Node(nombre_nodo, style="filled", fillcolor = col)    
    grafo.add_node(n)
    for arista in aristas:
        if arista not in aristas_exploradas:
            aristas_exploradas.append(arista)
            nombre_a = arista.item_1.codigo + "/F = " + \
                        str(arista.item_1.tipo_item.fase.orden) + "/C = " + \
                        str(arista.item_1.complejidad)
            if inicial == arista.item_1:
                col = "red"
            else:
                col = color(arista.item_1)
            n_a = pydot.Node(nombre_a, style="filled", fillcolor = col)
            nombre_b = arista.item_2.codigo + "/F = " + \
                       str(arista.item_2.tipo_item.fase.orden) + "/C = " + \
                       str(arista.item_2.complejidad)
            if  inicial == arista.item_2:
                col = "red"
            else:
                col = color(arista.item_2)
            n_b = pydot.Node(nombre_b, style="filled", fillcolor = col)
            nodo_b = opuesto(arista, nodo)
            if nodo_b not in nodos_explorados:
                nivel = nivel + 1                                  
                costo, grafo, band = costo_impacto(nodo_b, grafo, nodos_explorados, \
                                             aristas_exploradas, costo, \
                                             nivel, camino, inicial)
                if band:
                   grafo.add_node(n_a)
                   grafo.add_node(n_b)
                   grafo.add_edge(pydot.Edge(n_a, n_b))
    return costo + nodo.complejidad, grafo, True

def estado_proyecto(proyecto):
    """
    Asigna el estado al correspondiente a un proyecto dado.
    
    @param proyecto: Proyecto cuyo estado desea actualizarse. 
    @type proyecto: {Proyecto}
    """
    finalizado = True
    for fase in proyecto.fases:
        if not fase.estado == u"Finalizada":
            finalizado = False
            break
    if not proyecto.fases:
        finalizado = False
    if finalizado: 
        proyecto.estado = u"Finalizado"
        if not proyecto.fecha_fin:
            fecha_fin = datetime.datetime.now()
            proyecto.fecha_fin = datetime.date(int(fecha_fin.year), \
                                 int(fecha_fin.month),int(fecha_fin.day))
    else: 
        proyecto.fecha_fin = None
        if proyecto.estado == u"Finalizado": proyecto.estado = "En Desarrollo"

def estado_fase(fase):
    """
    Asigna el estado correspondiente a una fase dada.
    
    @param fase: Fase cuyo estado desea actualizarse. 
    @type fase: {Fase}
    """
    finalizada = True
    items = list()
    lista_items = list()
    aux = list()
    proyecto = DBSession.query(Proyecto).get(fase.id_proyecto)
    for tipo in fase.tipos_item:
        lista_items.append(tipo.items)
    for it in lista_items:
        for i in it:
            items.append(i)

    for item in items:
        for item_2 in items:
            if item is not item_2  and item.id == item_2.id : 
                if item.version > item_2.version: 
                    aux.append(item_2)
                else:
                    aux.append(item)
    items_aux = [i for i in items if i not in aux and not i.borrado]
    items = items_aux
    finalizada = True
    lb_total = True
    lb_parcial = False
    for item in items:
        if lb_total or not lb_parcial: #si todavía no se encontró al menos un
                                       #item fuera y un item dentro de una LB
            if item.linea_base:
                if item.linea_base.cerrado:
                    lb_parcial = True
                    if lb_total and not sucesor(item):
                        finalizada = False
                else:
                    lb_total = False
                    finalizada = False
            else: 
                  lb_total =  False
                  finalizada = False
    if not items:
        fase.estado = u"Inicial" 
    elif finalizada: 
        fase.estado = u"Finalizada"
        if not fase.fecha_fin:
            fecha_fin = datetime.datetime.now()
            fase.fecha_fin = datetime.date(int(fecha_fin.year), \
                                 int(fecha_fin.month),int(fecha_fin.day))
    elif lb_total and fase.orden == proyecto.nro_fases:
        fase.estado = u"Finalizada"
    elif lb_total:
        fase.estado = u"Linea Base Total"
    elif lb_parcial:
        fase.estado = u"Linea Base Parcial"
    else:
        fase.estado = u"En Desarrollo"
        if not fase.fecha_inicio:
            fecha_inicio = datetime.datetime.now()
            fase.fecha_inicio = datetime.date(int(fecha_inicio.year), \
                                 int(fecha_inicio.month),int(fecha_inicio.day))
    pro = DBSession.query(Proyecto).filter(Proyecto.id == fase.id_proyecto) \
          .one()    
    estado_proyecto(pro)
    if not finalizada: fase.fecha_fin = None 

def sucesor(item):
    """
    Evalúa si un item tiene o no un sucesor en la fase siguiente.
    
    @param item: Item dado
    @type item: {Item}
    @return: True si cuenta con un sucesor, False en caso contrario.
    """
    band = False
    for relacion in item.relaciones_a:
        if not relacion.item_2.tipo_item.fase == item.tipo_item.fase: 
            band = True
            break
    return band 

def consistencia_lb(lb):
    """
    Evalúa la consistencia de una línea base y asigna el valor correspondiente. 
    
    @param lb: Linea base a evaluar.
    @type lb: L{LineaBase}
    """
    consistente = True
    items = [x for x in lb.items if x.borrado is not True]
    aux = list()  
    for item in items:
            for item_2 in items:
                if item is not item_2  and item.id == item_2.id : 
                    if item.version > item_2.version and item_2 not in aux: 
                        aux.append(item_2) 
    for item in aux:
        items.remove(item) 
    for item in items:
        if not item.estado == u"Aprobado" or item.revisiones or \
           es_huerfano(item):
            consistente = False
            break
    if consistente: 
        lb.consistente = True
    else:
        lb.consistente = False

def proximo_id(lista_ids):
    """
    Determina el siguiente id a ser utilizado para un objeto del sistema 
    (proyecto, fase, item, etc.).

    @param lista_ids: lista de ids existentes del elemento del modelo dado.
    @type lista_ids: list()
    @return: proximo id a ser utilizado.
    """
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



