from repoze.what.predicates import Predicate
from saip.model import Proyecto, Fase, DBSession

class TienePermiso(Predicate):
    message = "El usuario no cuenta con los permisos necesarios para realizar esta operación"
    
    def __init__(self, permiso ,**kwargs):
        self.permiso = permiso
        self.id_proyecto = kwargs["id_proyecto"]
        self.id_fase = kwargs["id_fase"]   
    
    def evaluate(self, environ, credentials):
        fichas = DBSession.query(Ficha).filter_by(usuario = credentials.get('repoze.what.userid'))
        if self.id_proyecto:
            fichas = fichas.filter_by(proyecto = self.id_proyecto)
        if self.id_fase:
            fichas = fichas.filter_by(fase = self.id_fase)
        
        band = False
        for ficha in fichas:
            for perm in ficha.rol:
                if perm.nombre == permiso: 
                    band = True
                    break
        
        if !band: self.unmet() 
                
    



