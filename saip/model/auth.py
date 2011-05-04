# -*- coding: utf-8 -*-
"""
Auth* related model.

This is where the models used by :mod:`repoze.who` and :mod:`repoze.what` are
defined.

It's perfectly fine to re-use this definition in the SAIP application,
though.

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

    __tablename__ = 'fichas'
    id = Column(Unicode, primary_key = True)
    id_Usuario = Column(Unicode, ForeignKey('usuarios.id',
        onupdate="CASCADE", ondelete="CASCADE"))
    id_Rol = Column(Unicode, ForeignKey('roles.id',
        onupdate="CASCADE", ondelete="CASCADE"))
    id_Proyecto = Column(Unicode, ForeignKey('proyectos.id',
        onupdate="CASCADE", ondelete="CASCADE"))
    id_Fase = Column(Unicode, ForeignKey('fases.id',
        onupdate="CASCADE", ondelete="CASCADE"))

    proyecto = relation("Proyecto", backref = backref('fichas', order_by=id))
    fase = relation("Fase", backref = backref('fichas', order_by=id))    
    usuario = relation("Usuario", backref = backref('roles', order_by=id))
    rol = relation("Rol", backref = backref('fichas', order_by=id))
    
    def get_nombre(self):
        n = str(self.rol.nombre) + "/" + str(self.usuario.nombre_usuario)
        if self.proyecto: 
            n = n + "/" + str(self.proyecto.nombre) 
        if self.fase:        
            n = n + "/" + str(self.fase.nombre)
        return n        

    nombre = property(get_nombre)

    """def __init__(self, id, proyecto, usuario, rol):


        self.id = id
        self.proyecto = proyecto
        self.usuario = usuario
        self.fase = fase
        self.rol = rol """




#{ The auth* model itself


class Rol(DeclarativeBase):
    """
    Group definition for :mod:`repoze.what`.

    Only the ``group_name`` column is required by :mod:`repoze.what`.

    """

    __tablename__ = 'roles'

    #{ Columns

    id = Column(Unicode, primary_key=True)
    nombre = Column(Unicode, unique=True, nullable=False)
    descripcion = Column(Unicode)
    tipo =  Column(Unicode, nullable=False)
        

    #{ Relations
    
    usuarios = []
    #usuarios = relation('Usuario', secondary=user_group_table, backref='roles')

    #}

class Usuario(DeclarativeBase):
    """
    User definition.

    This is the user definition used by :mod:`repoze.who`, which requires at
    least the ``user_name`` column.

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
        """Return a set with all permissions granted to the user."""
        perms = set()
        for g in self.grupos:
            perms = perms | set(g.permissions)
        return perms

    @classmethod
    def by_email_address(cls, emaila):
        """Return the user object whose email address is ``email``."""
        return DBSession.query(cls).filter_by(email=emaila).first()

    @classmethod
    def by_user_name(cls, username):
        """Return the user object whose user name is ``username``."""
        return DBSession.query(cls).filter_by(nombre=username).first()

    def _set_password(self, password):
        """Hash ``password`` on the fly and store its hashed version."""
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
        """Return the hashed version of the password."""
        return self._password

    password = synonym('_password', descriptor=property(_get_password,
                                                        _set_password))

    #}

    def validate_password(self, password):
        """
        Check the password against existing credentials.

        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool

        """
        hash = sha1()
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        hash.update(password + str(self.password[:40]))
        return self.password[40:] == hash.hexdigest()


class Permiso(DeclarativeBase):
    """
    Permission definition for :mod:`repoze.what`.

    Only the ``permission_name`` column is required by :mod:`repoze.what`.

    """

    __tablename__ = 'permisos'

    #{ Columns

    id = Column(Unicode, primary_key = True)
    nombre = Column(Unicode, nullable = False)
    descripcion = Column(Unicode)

    #{ Relations

    roles = relation('Rol', secondary=rol_permiso,
                      backref='permisos')

    #}

#}
