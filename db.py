import sqlite3

TheDb = None
Player_Db = None

class Generic():
    def __init__(self, row):
        self.__dict__.update({ k: row[k] for k in row.keys() })

class MyDb():
    def __init__(self, db, table, fields): 
        self.table = table
        self.fields = fields
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
        print(q, vals)
        c = self.db.execute(q, vals)
        r = [Generic(r) for r in c.fetchall()]
        return r if len(r) != 1 else r[0]
    def update(self, vals, **kwargs):
        sets = ', '.join([k + ' = ?' for k in vals])
        where = ' and '.join([k + ' = ?' for k in kwargs])
        self.db.execute('update {} set {} where {}'.format(self.table, sets, where))
    def insert(self, **kwargs):
        fd = ','.join([k for k in kwargs])
        mk = ','.join(['?' for k in kwargs])
        vl = list(kwargs.values())
        q = 'insert into {} ({}) values({})'.format(self.table, fd, mk)
        self.db.execute(q, vl)


    
def player_db(*args, **kwargs):
    global TheDb, Player_Db
    _fields = (('player_id', 'int primary key'),
               ('name', 'text'),
               ('level', 'int'))
    _name = 'player'               
    if not TheDb:
        TheDb = sqlite3.connect('boq_data.db')
    print('pdb', args, kwargs)
    if not Player_Db:
        Player_Db = MyDb(db=TheDb, table=_name, fields=_fields)
        print('New player DB')
    return Player_Db

def memoize(var=None, fields=('key',)):
    """ 
    Some basic memoizer
    """
    var = dict() if not var else var
    def wrap(f):
        def memoized(*args, **kwargs):
            for ft in fields:
                if ft in kwargs:
                    key = ft
                    break
            if kwargs[key] not in var:
                var[kwargs[key]] = f(*args, **kwargs)
            return var[kwargs[key]]
        return memoized
    return wrap

@memoize(fields=('player_id',))
class Player():
    db = player_db()
    _fields = ('name', 'level', 'player_id')
    def __init__(self, key=None, **kwargs):
        print('New player', key)
        self.key = key
        self.__dict__.update(kwargs)
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
        old_p = self.db.get(player_id=self.player_id)
        if not old_p:
            vl = {k: getattr(self,k) for k in self._fields}
            self.db.insert(**vl)
        elif old_p.level < self.level:
            self.db.update({'name': self.name, 'level': self.level},
                           player_id=self.player_id)
        else:
            self.db.update({'name': self.name}, player_id=self.player_id)
    @staticmethod
    def get(player_id):
        print('Pl get with db', Player_Db)
        op = Player_Db,get(player_id=player_id)
        return Player(**op.__dict__)
