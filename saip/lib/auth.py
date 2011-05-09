# -*- coding: utf-8 -*-
from repoze.what.predicates import Predicate, is_anonymous
from saip.model import Ficha, Proyecto, Fase, DBSession, Usuario
from tg import request

class TienePermiso(Predicate):
    message = "El usuario no cuenta con los permisos necesarios para realizar esta operacion"
    
    def __init__(self, permiso ,**kwargs):
        self.permiso = permiso
        if "id_proyecto" in kwargs: 
            self.id_proyecto = kwargs["id_proyecto"]
        else: self.id_proyecto = None
        if "id_fase" in kwargs: 
            self.id_fase = kwargs["id_fase"]
        else: self.id_fase = None   
    
    def evaluate(self, environ, credentials):
        if is_anonymous().is_met(request.environ): self.unmet()
        usuario = DBSession.query(Usuario).filter_by(nombre = credentials.get('repoze.what.userid')).first()
        #fichas = DBSession.query(Ficha).filter_by(usuario = credentials.get('repoze.what.userid'))
        fichas = usuario.roles
        if self.id_proyecto:
            fichas = fichas.filter_by(proyecto = self.id_proyecto)
        if self.id_fase:
            fichas = fichas.filter_by(fase = self.id_fase)
        
        band = False
        for ficha in fichas:
            for perm in ficha.rol.permisos:
                if perm.nombre == self.permiso: 
                    band = True
                    break
        
        if not band: self.unmet() 
                
    



