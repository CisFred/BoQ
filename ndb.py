import sqlite3
import traceback

class BaseDb():
    _db = sqlite3.connect('boq_data.db')
    _db.row_factory = sqlite3.Row
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self._table = self.__class__._table
        self._fields = self.__class__._fields
        self._store = self.__class__._store
        self._fnames = [x[0] for x in self._fields]
        self._pkey = self._fnames[0]
        print('Init', self, dir(self))

    def get(self, **kwargs):
        w_cl = []
        values = []
        for k,v in kwargs.items():
            w_cl.append(k + ' = ?')
            values.append(v)
        where = 'where ' + ' and '.join(w_cl) if w_cl else ''
        r = self._db.execute('select * from {} {}'.format(self._table, where),
                             values)
        return r.fetchall()
    def save(self):
        print('save', self)
        traceback.print_stack()

class Player(BaseDb):
    _table = 'player'
    _fields = (('name', 'text primary key'),
               ('player_id', 'int'), ('level', 'int'))
    _store = dict()
    def __new__(cls, **kwargs):
        print('new player', super(BaseDb,cls))
        o = super(BaseDb,cls).__new__(cls)
        # print('new Player', dir(o))
        BaseDb.__init__(o)
        print('new Player', dir(o))
        if o._pkey in kwargs:
            if kwargs[o._pkey] in cls._store:
                return cls._store[kwargs[o._pkey]]
        p = cls.get(o, **kwargs)
        if p:                   #  and len(p) == 1:
            o.__dict__.update(dict(p[0]))
            o.update = True
            return o
        return super().__new__(cls)
    def __init__(self, **kwargs):
        BaseDb.__init__(self, **kwargs)
        self.__dict__.update(kwargs)
        self.save()
        try:
            self._store[kwargs[self._pkey]] = self
        except:
            pass
