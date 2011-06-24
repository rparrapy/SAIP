# -*- coding: utf-8 -*-
from saip.tests.models import ModelTest
from saip.model import Proyecto

class TestProyecto(ModelTest):
    """Unidad de testing del modelo ``Proyecto``"""
    klass = Proyecto
    attrs = dict(
        id = u"PR1",
        nombre = u"proyecto",
        descripcion = u"proyecto de prueba",
        estado = u"Nuevo",
        nro_fases = 3
    )

    def test_obj_creacion(self):
        """Los datos de proyecto se almacenan correctamente"""
        assert self.obj.nombre == u"proyecto" and \
            self.obj.descripcion == u"proyecto de prueba" and \
            self.obj.id == u"PR1" and self.obj.estado == u"Nuevo" and \
            self.obj.nro_fases == 3
