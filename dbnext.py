import sys
import tkinter as tk
from tkinter import ttk     #@Reimport
import sqlite3
import traceback
# from peewee import *

root = None

class GenView(tk.Toplevel):
    def __new__(cls, master, hud, name, js):
        if name in hud.tmp:
            print('Old GV', name, super())
        else:
            print('New GV', name, super(GenView, cls))
            hud.tmp[name] = super().__new__(cls)
        return hud.tmp[name]

    def __init__(self, master, hud, name, js):
        if hasattr(self, 'hud'):
            print('Already there', self.name)
            return
        super().__init__(master, name=name.lower())
        self.grid()
        self.master = master
        self.hud = hud
        print('DbView', name)
        self.name = name
        tk.Label(self, text=name).grid(columnspan=2, sticky=tk.EW)
        self.protocol('WM_DELETE_WINDOW', lambda h=hud,n=name: self.unreg(h,n))
        c = 1
        try:
            for k in js.keys():
                lb = tk.Label(self, text=k)
                if isinstance(js[k], list):
                    v = '{} entries'.format(len(js[k]))
                    vl = tk.Label(self, text=v)
                    fn = lambda e,v=js[k],f=k: self.show(v, f)
                    vl.bind('<Double-1>', fn)
                    lb.bind('<Double-1>', fn)
                else:
                    v = '{:.30s}'.format(str(js[k]))
                    vl = tk.Label(self, text=v)
                lb.grid(row=c, column=0, sticky=tk.W)
                vl.grid(row=c, column=1, sticky=tk.W)
                c += 1
            self.rowconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
        except:
            try:
                cln = [x for x in js[0].keys()]
                self.tree = ttk.Treeview(self, columns=cln,
                                         displaycolumns='#all')
                self.tree.column('#0', stretch=0, width=2)
                for f in cln:
                    self.tree.heading(f, text=f,
                                      command=lambda f=f: self.sort(f, False))
                    self.tree.column(f, width=70)

                sb = ttk.Scrollbar(self, orient=tk.VERTICAL,
                                   command= self.tree.yview)
                self.tree['yscroll'] = sb
                self.tree.grid(row=0, column=0, sticky=tk.NSEW)
                sb.grid(row=0, column=1, sticky=tk.NS)
                self.rowconfigure(0, weight=1)
                self.columnconfigure(0, weight=1)
                for a in js:
                    self.tree.insert('', tk.END, None,
                                     values=[a[f] for f in cln])
            except:
                traceback.print_exc()
                print('js', js)

    def unreg(self, h, n):
        h.tmp.pop(n)
        self.destroy()


    def sort(self, col, d):
        l = [(self.tree.set(k,col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=self.s_val, reverse=d)
        except:
            l.sort(key=lambda x: x[0], reverse=d)
        for i, (v, k) in enumerate(l):
            self.tree.move(k, '', i)
        self.tree.heading(col, text=col,
                          command=lambda f=col: self.sort(f, not d))

    def show(self, v, f):
        GenView(self.master, self.hud, self.name + ' ' + f, v)



class DbView(ttk.Frame):
    def __init__(self, master, name):
        super().__init__(master, name=None)
        self.grid()
        self.db = MyDb(table=name) 
        q = 'select * from ' + name
        r = self.db.execute(q)
        self.fields = [x[0] for x in r.description]
        self.master = master
        self.name = name
        self.tree = ttk.Treeview(self, columns=self.fields,
                                displaycolumns='#all')

        self.tree.column('#0', stretch=0, width=2)
        for f in self.fields:
            self.tree.heading(f,
                              text=f,
                              command=lambda f=f: self.sort(f, False))
            self.tree.column(f, width=70)
            
        sb = ttk.Scrollbar(self, orient=tk.VERTICAL, command= self.tree.yview)
        self.tree['yscroll'] = sb
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        sb.grid(row=0, column=1, sticky=tk.NS)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.tree.bind('<Double-1>', self.edit)
        self.populate(map(list,r.fetchall()))
    def s_val(self, v):
        try:
            return int(v[0])
        except:
            return v[0]
    def sort(self, col, d):
        l = [(self.tree.set(k,col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=self.s_val, reverse=d)
        except:
            l.sort(key=lambda x: x[0], reverse=d)
        for i, (v, k) in enumerate(l):
            self.tree.move(k, '', i)
        self.tree.heading(col, text=col,
                          command=lambda f=col: self.sort(f, not d))


    def get_db(self, name):
        q = 'select * from ' + name
        r = self.db.execute(q)
        fields = [x[0] for x in r.description]
        return r

    def edit(self, event):
        x = self.tree.identify_column(event.x)
        node = self.tree.focus()
        Edit(self, node, self.fields, self.tree.set(node), self.tree.column(x,'id'))

    def populate(self, args):
        try:
            for a in args:
                print('aa', a)
                self.tree.insert('', tk.END, a[0], values=a)
        except:
            try:
                for a in args(self.name, self.fields):
                    print('a', a)
                    self.tree.insert('', tk.END, a[0], values=a)
            except:
                self.tree.insert('', tk.END, a[0], values=a)
        
    def s_val(self, v):
        try:
            return int(v[0])
        except:
            return v[0]
    def sort(self, col, d):
        l = [(self.tree.set(k,col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=self.s_val, reverse=d)
        except:
            l.sort(key=lambda x: x[0], reverse=d)
        for i, (v, k) in enumerate(l):
            self.tree.move(k, '', i)
        self.tree.heading(col, text=col,
                          command=lambda f=col: self.sort(f, not d))

class Edit(tk.Toplevel):
    def __init__(self, view=None, node=None, fields=(), values=None, col=0):
        super().__init__(view.master if view else root)
        self.node = node
        self.view = view
        self.values = values
        r = 0
        if not values:
            values = {x: '' for x in fields}
        for k in fields:
            v = values[k]
            l = tk.Label(self, text=k)
            var = tk.StringVar()
            var.set(v)
            e = tk.Entry(self, textvariable=var)
            l.grid(row=r, column=0, sticky=tk.W)
            e.grid(row=r, column=2, sticky=tk.W)
            self.values[k] = (v, var)
            if k == col:
                e.focus()
            r += 1
        c = tk.Button(self, text='Cancel', command=self.destroy)
        d = tk.Button(self, text='Delete', command=self.delete)
        s = tk.Button(self, text='Apply', command=self.save)
        c.grid(row=r, column=0)
        d.grid(row=r, column=1)
        s.grid(row=r, column=2)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
    def delete(self):
        new_values = dict()
        pk = self.view.db.fields[0]
        new_values[pk] = self.values[pk][0]
        self.view.db.delete(**new_values)
        self.view.db.commit()
        self.view.tree.delete(self.node)
        
    def save(self):
        new_values = dict()
        for k, (o, w) in self.values.items():
            new_v = w.get()
            if new_v != o:
                changes = True
                self.view.tree.set(self.node, column=k, value=new_v)
                new_values[k] = new_v
        if new_values:
            pk = self.view.db.fields[0]
            new_values[pk] = self.values[pk][0]
            if not new_values[pk]:
                new_values[pk] = self.values[pk][1].get()
            print('save', pk, new_values[pk])
            self.view.db.upsert(**new_values)
            self.view.db.commit()
        self.destroy()

class MyDb():
    class Meta():
        db = None
    def __init__(self, dbn=None, table = None, cr_flds = None):
        if not self.Meta.db:
            self.Meta.db = sqlite3.connect(dbn)
            self.Meta.db.row_factory = sqlite3.Row
        if table:
            if cr_flds:
                fnames = [x[0] for x in cr_flds]
                fdef = ','.join(['{} {}'.format(x[0], x[1]) for x in cr_flds])
                q = 'create table if not exists {} ({})'.format(table, fdef)
                db.execute(q)
            self.table = table
            self.fields = self.get_fields()
            
    def __getattr__(self, k):
        if hasattr(self.Meta.db, k):
            return getattr(self.Meta.db, k)
        raise AttributeError('MyDb', k)
    def __setattr__(self, k, v):
        if hasattr(self.Meta.db, k):
            setattr(self.Meta.db, k, v)
        else:
            object.__setattr__(self, k, v)
    def get_fields(self):
        q = 'select * from ' + self.table + ' limit 0'
        fl = [x[0] for x in map(list,self.execute(q).description)]
        print('fl:', fl)
        return fl
    def delete(self, **kwargs):
        v = [x + ' = ?' for x in kwargs.keys()]
        vv = [x for x in kwargs.values()]
        q = 'delete from {} where {}'.format(self.table, ' and '.join(v))
        self.execute(q, vv)
    def upsert(self, **kwargs):
        """ Generic upsert. If t"""
        v = list()
        vv = list()
        pkey = self.fields[0]
        pval = kwargs[pkey]
        for f in self.fields:
            if f in kwargs and kwargs[f] != '':
                v.append('?')
                vv.append(kwargs[f])
            else:
                t = "(select {} from {} where {} = ?)".format(f,self.table,
                                                              pkey)
                vv.append(pval)
                print('Add', t, vv)
                v.append(t)
        q = 'insert or replace into {} ({}) values({})'
        q = q.format(self.table, ','.join(self.fields), ','.join(v))
        print(q, vv)
        self.execute(q, vv)
        

class Chooser(tk.Frame):
    def __init__(self, master, dbn, *args):
        super().__init__(master)
        self.master = master
        self.db = MyDb(dbn)
        self.grid()
        col = 1
        if not args:
            args = self.get_all()
        for nm in args:
            b = tk.Button(self, text=nm,
                          command=lambda nm=nm: DbView(tk.Toplevel(self.master),
                                                       nm))
            b.grid(row=0, column=col, sticky=tk.EW)
            col += 1
        qt = tk.Button(self, text='Quit', command=self.bye)
        qt.grid(row=0,column=0, sticky=tk.EW)


    def bye(self):
        self.master.destroy()

    def get_all(self):
        q = "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY 1"
        r = self.db.execute(q)
        res = [x['name'] for x in r.fetchall()]
        return res


if __name__ == '__main__':
    root = tk.Tk()
    gui = Chooser(root, *sys.argv[1:])
    root.mainloop()
    
        
