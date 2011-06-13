# -*- coding: utf-8 -*-
from repoze.what.predicates import Predicate, is_anonymous
from saip.model import Ficha, Proyecto, Fase, DBSession, Usuario
from tg import request

    
    
class TieneAlgunPermiso(Predicate):

    message = "El usuario no cuenta con ningun permiso de las caracteristicas especificadas"
    
    def __init__(self,**kwargs): 
        if "tipo" in kwargs: 
            self.tipo = kwargs["tipo"]
        else: self.tipo = None
        if "recurso" in kwargs: 
            self.recurso = kwargs["recurso"]
        else: self.recurso = None
        if "id_proyecto" in kwargs: 
            self.id_proyecto = kwargs["id_proyecto"]
        else: self.id_proyecto = None
        if "id_fase" in kwargs: 
            self.id_fase = kwargs["id_fase"]
        else: self.id_fase = None   

    def evaluate(self, environ, credentials):
        if is_anonymous().is_met(request.environ): self.unmet()
        usuario = DBSession.query(Usuario).filter(Usuario.nombre_usuario == credentials.get('repoze.what.userid')).first()
        fichas = DBSession.query(Ficha).filter(Ficha.usuario == usuario)
        if self.id_proyecto:
            fichas = fichas.filter(Ficha.id_proyecto == self.id_proyecto)
        if self.id_fase:
            fichas = fichas.filter(Ficha.id_fase == self.id_fase)
        fichas = fichas.all()
        if self.tipo:
            for ficha in reversed(fichas):
                if ficha.rol.tipo != self.tipo: fichas.remove(ficha)
        if self.recurso:
            band = False
            for ficha in reversed(fichas):
                for perm in ficha.rol.permisos:
                    if perm.recurso == self.recurso: 
                        band = True
                        break
                if not band: fichas.remove(ficha)
        if not fichas: self.unmet()        
                     

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
        #if self.id_proyecto: self.id_proyecto = unicode(request.url.split("/")[-3])
        #if self.id_fase: self.id_fase = unicode(request.url.split("/")[-3])    
        if is_anonymous().is_met(request.environ): self.unmet()
        usuario = DBSession.query(Usuario).filter(Usuario.nombre_usuario == credentials.get('repoze.what.userid')).first()
        fichas = DBSession.query(Ficha).filter(Ficha.usuario == usuario)
        if self.id_proyecto:
            fichas = fichas.filter(Ficha.id_proyecto == self.id_proyecto)
        if self.id_fase:
            fichas = fichas.filter(Ficha.id_fase == self.id_fase)
        
        band = False
        for ficha in fichas:
            for perm in ficha.rol.permisos:
                if perm.nombre == self.permiso: 
                    band = True
                    break
        
        if not band: self.unmet() 
                
    



