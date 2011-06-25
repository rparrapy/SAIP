# -*- coding: utf-8 -*-
"""

Módulo que define las clases del modelo del sistema relacionadas a
la autentificación y a la autorización. Este módulo es utilizado por
repoze.what y repoze.who

@authors:
    - U{Alejandro Arce<mailto:alearce07@gmail.com>}
    - U{Gabriel Caroni<mailto:gabrielcaroni@gmail.com>}
    - U{Rodrigo Parra<mailto:rodpar07@gmail.com>}
"""


import os
from datetime import datetime
import sys
try:
    from hashlib import sha1
except ImportError:
    sys.exit('ImportError: No module named hashlib\n'
             'If you are on python2.4 this library is not part of python. '
             'Please install it. Example: easy_install hashlib')

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, synonym, backref

from saip.model import DeclarativeBase, metadata, DBSession

__all__ = ['Usuario', 'Rol', 'Permiso', 'Ficha']


#{ Association tables


# This is the association table for the many-to-many relationship between
# groups and permissions. This is required by repoze.what.
rol_permiso = Table('rol_permiso', metadata,
    Column('id_Rol', Unicode, ForeignKey('roles.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('id_Permiso', Unicode, ForeignKey('permisos.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships. It's required by repoze.what.
class Ficha(DeclarativeBase):
    """Clase correspondiente a una ficha del sistema mapeada a la tabla
       fichas de forma declarativa. Relaciona un L{Rol} con un {Usuario} y,
       si corresponde, con un {Proyecto} y/o una {Fase}"""

    __tablename__ = 'fichas'
    id = Column(Unicode, primary_key = True)
    id_usuario = Column(Unicode, ForeignKey('usuarios.id',
        onupdate="CASCADE", ondelete="CASCADE"), nullable = False)
    id_rol = Column(Unicode, ForeignKey('roles.id',
        onupdate="CASCADE", ondelete="CASCADE"), nullable = False)
    id_proyecto = Column(Unicode, ForeignKey('proyectos.id',
        onupdate="CASCADE", ondelete="CASCADE"))
    id_fase = Column(Unicode, ForeignKey('fases.id',
        onupdate="CASCADE", ondelete="CASCADE"))

    proyecto = relation("Proyecto", backref = backref('fichas', order_by=id, \
                        cascade="all,delete,delete-orphan"))
    fase = relation("Fase", backref = backref('fichas', order_by=id, \
                    cascade="all,delete,delete-orphan"))    
    usuario = relation("Usuario", backref = backref('roles', order_by=id, \
              cascade="all,delete,delete-orphan"))
    rol = relation("Rol", backref = backref('fichas', order_by=id, \
                   cascade="all,delete,delete-orphan"))

    
    def get_nombre(self):
        n = str(self.rol.nombre) + "/" + str(self.usuario.nombre_usuario)
        if self.proyecto: 
            n = n + "/" + str(self.proyecto.nombre) 
        if self.fase:        
            n = n + "/" + str(self.fase.nombre)
        return n        

    nombre = property(get_nombre)



#{ The auth* model itself


class Rol(DeclarativeBase):
    """
    Clase correspondiente a un Rol del sistema mapeada a la tabla roles de
    forma declarativa. 
    """

    __tablename__ = 'roles'

    #{ Columns

    id = Column(Unicode, primary_key=True)
    nombre = Column(Unicode, unique=True, nullable=False)
    descripcion = Column(Unicode)
    tipo =  Column(Unicode, nullable=False)
        

    #{ Relations
    
    usuarios = []


    #}

class Usuario(DeclarativeBase):
    """
    Clase correspondiente a un Usuario del sistema mapeada a la tabla usuarios 
    de forma declarativa. 
    """
    __tablename__ = 'usuarios'

    #{ Columns

    id = Column(Unicode, primary_key = True)
    nombre_usuario = Column(Unicode, nullable = False, unique = True)
    nombre = Column(Unicode, nullable = False)
    apellido = Column(Unicode, nullable = False)
    email = Column(Unicode, nullable = False)
    telefono = Column(Unicode, nullable = False)
    direccion = Column(Unicode, nullable = False)
    _password = Column('password', Unicode,
                       info={'rum': {'field':'Password'}})


    #{ Getters and setters

    @property
    def permissions(self):
        perms = set()
        for g in self.grupos:
            perms = perms | set(g.permissions)
        return perms

    @classmethod
    def by_email_address(cls, emaila):
        return DBSession.query(cls).filter_by(email=emaila).first()

    @classmethod
    def by_user_name(cls, username):
        return DBSession.query(cls).filter_by(nombre=username).first()

    def _set_password(self, password):
        """Hashea el password y almacena la versión hasheada."""
        # Make sure password is a str because we cannot hash unicode objects
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        salt = sha1()
        salt.update(os.urandom(60))
        hash = sha1()
        hash.update(password + salt.hexdigest())
        password = salt.hexdigest() + hash.hexdigest()
        # Make sure the hashed password is a unicode object at the end of the
        # process because SQLAlchemy _wants_ unicode objects for Unicode cols
        if not isinstance(password, unicode):
            password = password.decode('utf-8')
        self._password = password

    def _get_password(self):
        """Retorna la versión hasheada de un password."""
        return self._password

    password = synonym('_password', descriptor=property(_get_password,
                                                        _set_password))

    #}

    def validate_password(self, password):
        """
        Valida el password ingresado por el usuario.

        @param password: el password (texto claro) proveído por el usuario 
                         y que será hasheado con la versión almacenada en la
                         base de datos.  
        @type password: Unicode.
        @return: Si el password ingresado es válido o no
        @rtype: Bool

        """
        hash = sha1()
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        hash.update(password + str(self.password[:40]))
        return self.password[40:] == hash.hexdigest()


class Permiso(DeclarativeBase):
    """
    
    Clase correspondiente a un Permiso del sistema mapeada a la tabla permisos 
    de forma declarativa. 
    
    """

    __tablename__ = 'permisos'

    #{ Columns

    id = Column(Unicode, primary_key = True)
    nombre = Column(Unicode, nullable = False)
    tipo = Column(Unicode, nullable = False)
    recurso = Column(Unicode, nullable = False)
    descripcion = Column(Unicode)

    #{ Relations

    roles = relation('Rol', secondary=rol_permiso,
                      backref='permisos')

    #}

#}
