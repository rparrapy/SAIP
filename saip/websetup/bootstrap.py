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
        u = model.Usuario()
        u.id = u'US1'
        u.nombre_usuario = u'manager'
        u.nombre = u'manager'
        u.apellido = u'manager'        
        u.email = u'manager@somedomain.com'
        u.password = u'managepass'
        u.direccion = u'frente a una vereda'
        u.telefono = u'0904 manager'        
    
        model.DBSession.add(u)
    
        g = model.Rol()
        g.id = u'1'
        g.nombre = u'manager'
        g.tipo = u'1'

        f = model.Ficha()        
        f.id = u'1'
        f.usuario = u
        f.rol = g
    
        model.DBSession.add(g)
        model.DBSession.add(f)
        
        p = model.Permiso()
        p.id = u'PE1'
        p.tipo = u'Sistema'
        p.nombre = u'manage'
        p.descripcion = u'This permission give an administrative right to the bearer'
        p.roles.append(g)
    
        model.DBSession.add(p)
    
        u1 = model.Usuario()
        u1.id = u'US2'
        u1.nombre_usuario = u'editor'        
        u1.nombre = u'editor'
        u1.apellido = u'editor'    
        u1.email = u'editor@somedomain.com'
        u1.password = u'editpass'
        u1.direccion = u'frente a una vereda'
        u1.telefono = u'0904 editor'  
    
        model.DBSession.add(u1)
        
        permisos_sistema = ["crear rol", "modificar rol", "eliminar rol",\
                    "asignar permiso", "desasignar permiso", "listar roles",\
                    "crear usuario", "modificar usuario", "eliminar usuario",\
                    "asignar rol", "desasignar rol", "listar usuarios",\
                    "crear proyecto", "modificar proyecto", "eliminar proyecto", "listar proyectos"]

                    
        permisos_proyecto = ["crear fase", "modificar fase", "eliminar fase", "listar fases",\
                            "crear tipo de item", "modificar tipo de item", "eliminar tipo de item",\
                             "listar tipos de items"]
        
        permisos_fase = ["crear linea base", "separar linea base", "unir lineas base",\
                    "abrir linea base", "cerrar linea base", "listar lineas bases",\
                    "crear item", "modificar item", "eliminar item", "listar items",\
                    "reversionar item", "recuperar item", "setear estado item en desarrollo",\
                    "setear estado item aprobado", "setear estado item listo"]
        
        c = 2 
        
        def agregar_permisos(permisos,tipo,c):
            for permiso in permisos:
                p = model.Permiso()
                p.id = unicode("PE"+str(c),"utf-8")
                p.nombre = unicode(permiso,"utf-8")
                p.tipo = tipo
                model.DBSession.add(p)
                c = c + 1
            return c

        c = agregar_permisos(permisos_sistema, u"Sistema",c)
        c = agregar_permisos(permisos_proyecto, u"Proyecto",c)
        c = agregar_permisos(permisos_fase, u"Fase",c)        
        

        model.DBSession.flush()
        transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'
        

    # <websetup.bootstrap.after.auth>
