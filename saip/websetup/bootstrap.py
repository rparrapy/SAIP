# -*- coding: utf-8 -*-
"""Setup the SAIP application"""

import logging
from tg import config
from saip import model

import transaction


def bootstrap(command, conf, vars):
    """Place any commands to setup saip here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:

        m = model.Usuario()
        m.id = u'US1'
        m.nombre_usuario = u'admin'
        m.nombre = u'Bruce'
        m.apellido = u'Almighty'        
        m.email = u'bruce@almighty.com'
        m.password = u'brucepass'
        m.direccion = u'frente a una vereda'
        m.telefono = u'0904 ALMIGHTY'        
    
        model.DBSession.add(m)
    
        r = model.Rol()
        r.id = u'RL1'
        r.nombre = u'administrador'
        r.tipo = u'Sistema'

        fic = model.Ficha()        
        fic.id = u'FI1-US1'
        fic.usuario = m
        fic.rol = r
    
        model.DBSession.add(r)
        model.DBSession.add(fic)

        lider = model.Rol()
        lider.id = u'RL2'
        lider.nombre = u'Lider de Proyecto'
        lider.tipo = u'Proyecto'

        model.DBSession.add(lider)
        
        encargado = model.Rol()
        encargado.id = u'RL3'
        encargado.nombre = u'Encargado de fase'
        encargado.tipo = u'Fase'

        model.DBSession.add(encargado)

        permisos = [{"nombre":"crear rol", "recurso":"Rol", "tipo": "Sistema"},\
         {"nombre":"eliminar rol", "recurso":"Rol", "tipo": "Sistema"},\
         {"nombre":"asignar permiso", "recurso":"Rol", "tipo": "Sistema"},\
         {"nombre":"listar roles", "recurso":"Rol", "tipo": "Sistema"},\
         {"nombre":"crear usuario", "recurso":"Usuario", "tipo": "Sistema"},\
         {"nombre":"modificar usuario", "recurso":"Usuario", "tipo": "Sistema"},\
         {"nombre":"eliminar usuario", "recurso":"Usuario", "tipo": "Sistema"},\
         {"nombre":"asignar rol sistema", "recurso":"Ficha", "tipo": "Sistema"},\
         {"nombre":"asignar rol proyecto", "recurso":"Ficha", "tipo": "Proyecto"},\
         {"nombre":"asignar rol cualquier fase", "recurso":"Ficha", "tipo": "Proyecto"},\
         {"nombre":"asignar rol fase", "recurso":"Ficha", "tipo": "Fase"},\
         {"nombre":"listar usuarios", "recurso":"Usuario", "tipo": "Sistema"},\
         {"nombre":"crear proyecto", "recurso":"Proyecto", "tipo": "Sistema"},\
         {"nombre":"modificar proyecto", "recurso":"Proyecto", "tipo": "Sistema"},\
         {"nombre":"eliminar proyecto", "recurso":"Proyecto", "tipo": "Sistema"},\
         {"nombre":"listar proyectos", "recurso":"Proyecto", "tipo": "Sistema"},\
         {"nombre":"setear estado proyecto en desarrollo", "recurso":"Proyecto", "tipo": "Proyecto"},\
         {"nombre":"crear fase", "recurso":"Fase", "tipo": "Proyecto"},\
         {"nombre":"modificar fase", "recurso":"Fase", "tipo": "Proyecto"},\
         {"nombre":"eliminar fase", "recurso":"Fase", "tipo": "Proyecto"},\
         {"nombre":"listar fases", "recurso":"Fase", "tipo": "Proyecto"},\
         {"nombre":"importar fase", "recurso":"Fase", "tipo": "Proyecto"},\
         {"nombre":"crear tipo de item", "recurso":"Tipo de Item", "tipo": "Fase"},\
         {"nombre":"modificar tipo de item", "recurso":"Tipo de Item", "tipo": "Fase"},\
         {"nombre":"eliminar tipo de item", "recurso":"Tipo de Item", "tipo": "Fase"},\
         {"nombre":"listar tipos de item", "recurso":"Tipo de Item", "tipo": "Fase"},\
         {"nombre":"importar tipo de item", "recurso":"Tipo de Item", "tipo": "Fase"},\
         {"nombre":"crear linea base", "recurso":"Linea Base", "tipo": "Fase"},\
         {"nombre":"separar linea base", "recurso":"Linea Base", "tipo": "Fase"},\
         {"nombre":"unir lineas base", "recurso":"Linea Base", "tipo": "Fase"},\
         {"nombre":"listar lineas base", "recurso":"Linea Base", "tipo": "Fase"},\
         {"nombre":"abrir linea base", "recurso":"Linea Base", "tipo": "Fase"},\
         {"nombre":"cerrar linea base", "recurso":"Linea Base", "tipo": "Fase"},\
         {"nombre":"crear item", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"modificar item", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"eliminar item", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"listar items", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"reversionar item", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"recuperar item", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"setear estado item en desarrollo", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"setear estado item aprobado", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"setear estado item listo", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"eliminar revisiones", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"descargar archivo", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"calcular costo de impacto", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"crear relaciones", "recurso":"Item", "tipo": "Fase"},\
         {"nombre":"eliminar relaciones", "recurso":"Item", "tipo": "Fase"}]
        
        c = 1

        
        def agregar_permisos(permisos,c):
            for permiso in permisos:
                p = model.Permiso()
                p.id = unicode("PE"+str(c),"utf-8")
                p.nombre = unicode(permiso["nombre"],"utf-8")
                p.tipo = unicode(permiso["tipo"],"utf-8")
                p.recurso = unicode(permiso["recurso"],"utf-8")
                model.DBSession.add(p)
                if p.tipo == u"Sistema": p.roles.append(r)
                if p.tipo == u"Proyecto": p.roles.append(lider)
                if p.tipo == u"Fase": p.roles.append(encargado)
                c = c + 1
            return c

        c = agregar_permisos(permisos,c)      
        

        model.DBSession.flush()
        transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'
        

    # <websetup.bootstrap.after.auth>
