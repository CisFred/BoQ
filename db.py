import sqlite3

TheDb = None
AllDbIns = dict()

DbFields =  {'player': (('player_id', 'int primary key'),
                      ('name', 'text'), ('level', 'int')),
           'stuff':  (('name', 'text primary key'), ('id', 'int'),
                      ('id_short_1', 'int'), ('id_short_2', 'int'),
                      ('price', 'int')),
           'recipe': (('name', 'text primary key'),
                      ('Rprice', 'int'), ('Oprice', 'int'),
                      ('i1', 'int'), ('q1', 'int'),
                      ('i2', 'int'), ('q2', 'int'),
                      ('i3', 'int'), ('q3', 'int'),
                      ('i4', 'int'), ('q4', 'int'),
                      ('i5', 'int'), ('q5', 'int'),
                      ('i6', 'int'), ('q6', 'int')),
           }

class Generic():
    def __init__(self, row):
        self.__dict__.update({ k: row[k] for k in row.keys() })

class MyDb():
    def __init__(self, db, table, fields): 
        self.table = table
        self.fields = fields

        self.fnames = [x[0] for x in fields]
        self.db = db
        fdef = ','.join(['{} {}'.format(x[0], x[1]) for x in fields])
        db.execute('create table if not exists {} ({})'.format(table, fdef))
        db.row_factory = sqlite3.Row
    def get(self, **kwargs):
        if kwargs:
            where = 'where ' + ' and '.join('{} = ?'.format(k) for k in kwargs)
            vals = list(kwargs.values())
        else:
            where = ''
            vals = []
        q = 'select * from {} {}'.format(self.table, where)
        # print(q, vals)
        c = self.db.execute(q, vals)
        r = [Generic(r) for r in c.fetchall()]
        return r
    def update(self, vals, **kwargs):
        sets = ', '.join([k + ' = ?' for k in vals])
        where = ' and '.join([k + ' = ?' for k in kwargs])
        q = 'update {} set {} where {}'.format(self.table, sets, where)
        print(q, kwargs.values())
        self.db.execute(q, kwargs.values())
    def insert(self, **kwargs):
        fd = ','.join([k for k in kwargs])
        mk = ','.join(['?' for k in kwargs])
        vl = list(kwargs.values())
        q = 'insert into {} ({}) values({})'.format(self.table, fd, mk)
        self.db.execute(q, vl)
    def upsert(self, **kwargs):
        """ Generic upsert. If t"""
        v = list()
        vv = list()
        pkey = self.fnames[0]
        pval = kwargs[pkey]
        for f in self.fnames:
            if f in kwargs and kwargs[f] != '':
                v.append('?')
                vv.append(kwargs[f])
            else:
                t = "(select {} from {} where {} = ?)".format(f,self.table,
                                                              pkey)
                vv.append(pval)
                print('Add', t)
                v.append(t)
        q = 'insert or replace into {} ({}) values({})'
        q = q.format(self.table, ','.join(self.fnames), ','.join(v))
        print(q, vv)
        self.db.execute(q, vv)
                

def instance_db(name=None):
    global TheDb
    if not TheDb:
        TheDb = sqlite3.connect('boq_data.db')
    if name not in AllDbIns:
        AllDbIns[name] = MyDb(db=TheDb, table=name, fields=DbFields[name])
    return AllDbIns[name]


def memoize(name=''):
    """ 
    Basic memoizer
    """
    var = dict()
    fdefs = DbFields[name]
    the_key = fdefs[0][0]
    def wrap(f):
        def memoized(*args, **kwargs):
            if kwargs[the_key] not in var:
                f._fdefs = fdefs
                f._name = name
                var[kwargs[the_key]] = f(*args, **kwargs)
            else:
                var[kwargs[the_key]].update(**kwargs)
            return var[kwargs[the_key]]
        return memoized
    return wrap

@memoize(name='player')
class Player():
    def __init__(self, auto_save=False, **kwargs):
        print('New player', kwargs['name'])
        self._db = instance_db(name=self._name)
        self._fields = (x[0] for x in self._fdefs)
        self.__dict__.update(kwargs)
        if auto_save:
            self.save()
    def update(self, **kwargs):
        save = False
        for k, v in kwargs.items():
            if getattr(self, k, False) != v:
                save = True
                setattr(self, k, v)
        if save:
            self.save()
    def save(self):
        """insert or update. Special care about level so it doesn decrease"""
        old_p = self._db.get(player_id=self.player_id)
        if not old_p:
            vl = {k: getattr(self,k) for k in self._fields}
            self._db.insert(**vl)
        elif old_p.level < getattr(self,'level',0):
            self._db.update({'name': self.name, 'level': self.level},
                           player_id=self.player_id)
        else:
            self._db.update({'name': self.name}, player_id=self.player_id)


@memoize(name='stuff')
class Stuff():
    def __init__(self, auto_save=False, **kwargs):
        print('New stuff', kwargs['name'] if 'name' in kwargs else kwargs['id'])
        self._db = instance_db(name=self._name)
        self._fields = (x[0] for x in self._fdefs)
        self.__dict__.update(kwargs)
        if auto_save:
            self.save()
    def update(self, **kwargs):
        save = False
        for k, v in kwargs.items():
            if getattr(self, k, False) != v:
                save = True
                setattr(self, k, v)
        if save:
            self.save()
    def save(self):
        vl = {k: getattr(self,k) for k in self._fields}
        print('ups', vl)
        self._db.upsert(**vl)

def find(what, **kwargs):
    db = instance_db(name=what)
    return ([x[0] for x in DbFields[what]], db.get(**kwargs))

@memoize(name='recipe')
class Recipe():
    def __init__(self, auto_save=False, **kwargs):
        print('New Recipe', kwargs['name'])
        self._db = instance_db(name=self._name)
        self._fields = (x[0] for x in self._fdefs)
        self.__dict__.update(kwargs)
        if auto_save:
            self.save()
    def update(self, **kwargs):
        save = False
        for k, v in kwargs.items():
            if getattr(self, k, False) != v:
                save = True
                setattr(self, k, v)
        if save:
            self.save()
    def save(self):
        vl = {k: getattr(self,k) for k in self._fields}
        self._db.upsert(**vl)

def SaveEntry(key, vd):
    return
    id = DbFields[key][0]
    pval = vd.pop(id)
    AllDbIns[key].update()

def DeleteEntry(*a, **k):
    pass

def InitDbs():
    for i in ('stuff', 'player', 'recipe'):
        instance_db(name=i)

def CommitDb():
    TheDb.commit()
