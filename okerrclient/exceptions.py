class OkerrExc(Exception):
    pass

class OkerrLockError(OkerrExc):
    pass

class OkerrClientServer(OkerrExc):
    pass
    
class OkerrAuth(OkerrExc):
    pass

class OkerrKeyAuth(OkerrExc):
    pass
        
class OkerrNoKey(OkerrExc):
    pass
        
class OkerrNoTextID(OkerrExc):
    pass
    
class OkerrBadData(OkerrExc):
    pass

class OkerrBadMethod(OkerrExc):
    pass

