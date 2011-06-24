# -*- coding: utf-8 -*-
from saip.tests.models import ModelTest
from saip.model import Rol

class TestRol(ModelTest):
    """Unidad de testing del modelo ``Rol``"""
    klass = Rol
    attrs = dict(
        id = u"RL1",
        nombre = u"rol",
        descripcion = u"rol de prueba",
        tipo = u"Sistema"
    )

    def test_obj_creacion(self):
        """Los datos de rol se almacenan correctamente"""
        assert self.obj.nombre == u"rol" and \
            self.obj.descripcion == u"rol de prueba" and \
            self.obj.tipo == u"Sistema" and self.obj.id == u"RL1"
