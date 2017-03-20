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
    def set(self, **kwargs):
        fd = ','.join([k for k in kwargs])
        mk = ','.join(['?' for k in kwargs])
        vl = list(kwargs.values())
        q = 'insert into {} ({}) values({})'.format(self.table, fd, mk)
        self.db.execute(q, vl)

def player_db():
    global TheDb, Player_Db
    _fields = (('player_id', 'int primary key'),
               ('name', 'text'),
               ('level', 'int'))
    _name = 'player'               
    if not TheDb:
        TheDb = sqlite3.connect('boq_data.db')
    if not Player_Db:
        Player_Db = MyDb(db=TheDb, table=_name, fields=_fields)
    return Player_Db

