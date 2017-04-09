import sqlite3
import traceback

class BaseDb():
    _db = sqlite3.connect('boq_data.db')
    _db.row_factory = sqlite3.Row
    def __new__(cls, **kwargs):
        # print('new Player', dir(o))
        _pkey = cls._fields[0][0]
        o = False
        if _pkey in kwargs:
            if kwargs[_pkey] in cls._store:
                o = cls._store[kwargs[_pkey]]
        if not o:
            o = super().__new__(cls)
            o._table = cls._table
            o._fields = cls._fields
            o._store = cls._store
            o._fnames = [x[0] for x in o._fields]
            o._pkey = _pkey
            p = cls.get(**kwargs)
            if p:                   #  and len(p) == 1:
                o.__dict__.update(dict(p[0]))
        return o

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.update = True

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
                w_cl.append(k + ' = ?')
                values.append(v)
        where = 'where ' + ' and '.join(w_cl) if w_cl else ''
        print('select * from {} {}'.format(cls._table, where),
              values)
        r = cls._db.execute('select * from {} {}'.format(cls._table, where),
                             values)
        return r.fetchall()
    def save(self):
        print('save', self.__dict__)

class Player(BaseDb):
    _table = 'player'
    _fields = (('name', 'text primary key'),
               ('player_id', 'int'), ('level', 'int'))
    _store = dict()
    def __init__(self, **kwargs):
        if 'level' in kwargs and self.level > kwargs['level']:
            kwargs.pop('level')
        super().__init__(**kwargs)

        self.save()
        self._store[kwargs[self._pkey]] = self

class Stuff(BaseDb):
    _table = 'stuff'
    _fields = (('name', 'text primary key'), ('id', 'int'),
               ('id_short_1', 'int'), ('id_short_2', 'int'),
               ('price', 'int'))
    _store = dict()

class Recipe(BaseDb):
    _table = 'recipe'
    _fields = (('recipe', 'text primary key'),
               ('i1', 'int'), ('q1', 'int'), ('i2', 'int'), ('q2', 'int'),
               ('i3', 'int'), ('q3', 'int'), ('i4', 'int'), ('q4', 'int'),
               ('i5', 'int'), ('q5', 'int'), ('i6', 'int'), ('q6', 'int'),
               ('i7', 'int'), ('q7', 'int'))
    _store = dict()
