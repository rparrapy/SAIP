# -*- coding: utf-8 -*-
from saip.tests.models import ModelTest
from saip.model import Usuario

class TestUsuario(ModelTest):
    """Unidad de testing del modelo ``Usuario``"""
    klass = Usuario
    attrs = dict(
        id = u"US1",
        nombre = u"usuario",
        nombre_usuario = u"nombre_usuario",
        apellido = u"apellido",
        email = u"mail@mail.com",
        telefono = u"234877",
        direccion = u"frente a una vereda"
    )

    def test_obj_creacion(self):
        """Los datos de usuario se almacenan correctamente"""
        assert self.obj.nombre == u"usuario" and \
            self.obj.nombre_usuario == u"nombre_usuario" and \
            self.obj.apellido == u"apellido" and \
            self.obj.email == u"mail@mail.com" and \
            self.obj.telefono == u"234877" and \
            self.obj.direccion == u"frente a una vereda" and \
            self.obj.id == u"US1"
