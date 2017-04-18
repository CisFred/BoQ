import sqlite3
import traceback

class BaseDb():
    _db = sqlite3.connect('boq_data.db')
    _db.row_factory = sqlite3.Row
    def __new__(cls, **kwargs):
        _pkey = cls._fields[0][0]

        if _pkey in kwargs and kwargs[_pkey] in cls._store:
            return cls._store[kwargs[_pkey]]

        # print(cls.__name__, kwargs)
        o = super().__new__(cls)
        if _pkey in kwargs:
            cls._store[kwargs[_pkey]] = o
        o._table = cls._table
        o._fields = cls._fields
        o._store = cls._store
        o._fnames = cls._fnames
        o._pkey = _pkey
        [setattr(o, x, 0) for x in o._fnames if not hasattr(o,x)]
        pls = cls.get(**kwargs)
        if pls:                   #  and len(p) == 1:
            return pls[0]
        return o

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def update(self, **kwargs):
        for k,v in kwargs.items():
            if k in self._fnames and v != getattr(self,k):
                self.saveme = True
        self.__dict__.update(kwargs)


    @classmethod
    def get(cls, **kwargs):
        w_cl = []
        values = []
        _pkey = cls._fields[0][0]
        if _pkey in kwargs:
            w_cl.append(_pkey + ' = ?')
            values.append(kwargs[_pkey])
        else:
            for k,v in kwargs.items():
                if k in cls._fnames:
                    w_cl.append(k + ' = ?')
                    values.append(v)
                else:
                    print('skip {} not in {}'.format(k,cls._fnames))
        where = 'where ' + ' and '.join(w_cl) if w_cl else ''
        r = cls._db.execute('select * from {} {}'.format(cls._table, where),
                             values)
        return [cls(**dict(x)) for x in r.fetchall()]
    def save(self):
        if self.saveme:
            self.upsert()
            self.saveme = False
            
    def upsert(self, **kwargs):
        """ Generic upsert. If t"""
        v = list()
        vv = list()
        pkey = self._fnames[0]
        self.__dict__.update(kwargs)
        pval = getattr(self,pkey)
        for f in self._fnames:
            if getattr(self,f,None):
                v.append('?')
                vv.append(getattr(self,f))
            else:
                t = "(select {} from {} where {} = ?)".format(f,
                                                              self._table,
                                                              pkey)
                vv.append(pval)
                print('Add', t)
                v.append(t)
        q = 'insert or replace into {} ({}) values({})'
        q = q.format(self._table, ','.join(self._fnames), ','.join(v))
        # print(q, vv)
        self._db.execute(q, vv)
        self._db.commit()
        return self

class Player(BaseDb):
    _table = 'player'
    _fields = (('name', 'text primary key'),
               ('player_id', 'int'), ('level', 'int'))
    _fnames = [x[0] for x in _fields]
    _store = dict()
    def __init__(self, **kwargs):
        if 'level' in kwargs and hasattr(self,'level'):
            if self.level > kwargs['level']:
                kwargs.pop('level')
        super().__init__(**kwargs)


class Stuff(BaseDb):
    _table = 'stuff'
    _fields = (('name', 'text primary key'), ('id', 'int'),
               ('id_short_1', 'int'), ('id_short_2', 'int'),
               ('price', 'int'))
    _fnames = [x[0] for x in _fields]
    _store = dict()

class Recipe(BaseDb):
    _table = 'recipe'
    _fields = (('recipe', 'text primary key'),
               ('i1', 'int'), ('q1', 'int'), ('i2', 'int'), ('q2', 'int'),
               ('i3', 'int'), ('q3', 'int'), ('i4', 'int'), ('q4', 'int'),
               ('i5', 'int'), ('q5', 'int'), ('i6', 'int'), ('q6', 'int'),
               ('i7', 'int'), ('q7', 'int'))
    _fnames = [x[0] for x in _fields]
    _store = dict()

class Backpack(BaseDb):
    _table = 'backpack'
    _fields = (('player_id', 'int primary key',) +
               tuple(( ('slt%d'%x, 'int') for x in range(36))) +
               tuple(( ('qty%d'%x, 'int') for x in range(36))))
    _fnames = [x[0] for x in _fields]
    _store = dict()

class Warehouse(BaseDb):
    _table = 'warehouse'
    _fields = (('player_id', 'int primary key',) +
               tuple(( ('slt%d'%x, 'int') for x in range(54))) +
               tuple(( ('qty%d'%x, 'int') for x in range(54))))
    _fnames = [x[0] for x in _fields]
    _store = dict()
