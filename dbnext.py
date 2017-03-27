import sys
import tkinter as tk
from tkinter import ttk     #@Reimport
import sqlite3
from peewee import *

class DbView(ttk.Frame):
    def __init__(self, master, name, fields):
        super().__init__(master, name=name)
        self.grid()
        self.fields = fields

        self.name = name
        self.tree = ttk.Treeview(self, columns=self.fields,
                                displaycolumns='#all')

        self.tree.column('#0', stretch=0, width=2)
        for f in self.fields:
            self.tree.heading(f,
                              text=f,
                              command=lambda f=f: self.sort(f, False))
            self.tree.column(f, stretch=0, width=70)
            
        sb = ttk.Scrollbar(self, orient=tk.VERTICAL, command= self.tree.yview)
        self.tree['yscroll'] = sb
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        sb.grid(row=0, column=1, sticky=tk.NS)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.tree.bind('<Double-1>', self.update)

    def update(self, event):
        print('update', event.x, event.y, self.tree.item(self.tree.focus()))
        y = self.tree.identify_row(event.y)
        x = self.tree.identify_column(event.x)
        print('  elem', x, y)

    def populate(self, args):
        try:
            for a in args:
                self.tree.insert('', tk.END, a[0], values=a)
        except:
            try:
                for a in args(self.name, self.fields):
                    self.tree.insert('', tk.END, a[0], values=a)
            except:
                self.tree.insert('', tk.END, a[0], values=a)
        
    def sort(self, col, d):
        l = [(self.tree.set(k,col), k) for k in self.tree.get_children('')]
        l.sort(reverse=d)
        for i, (v, k) in enumerate(l):
            self.tree.move(k, '', i)
        self.tree.heading(col, text=col,
                          command=lambda f=col: self.sort(f, not d))


class Chooser(tk.Frame):
    def __init__(self, master, dbn, *args):
        super().__init__(master)
        self.master = master
        self.db = sqlite3.connect(dbn)
        self.db.row_factory = sqlite3.Row
        self.db_top = dict()
        self.grid()
        col = 1
        if not args:
            args = self.get_all()
        for nm in args:
            b = tk.Button(self, text=nm, command=lambda nm=nm: self.show_db(nm))
            b.grid(row=0, column=col, sticky=tk.EW)
            col += 1
        qt = tk.Button(self, text='Quit', command=self.bye)
        qt.grid(row=0,column=0, sticky=tk.EW)


    def bye(self):
        self.master.destroy()

    def show_db(self, name):
        q = 'select * from ' + name
        r = self.db.execute(q)
        fields = [x[0] for x in r.description]
        top = tk.Toplevel(self.master)
        dbv = DbView(top, name, fields)
        dbv.populate(map(list,r.fetchall()))
    
    def get_all(self):
        q = "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY 1"
        r = self.db.execute(q)
        res = [x['name'] for x in r.fetchall()]
        return res


if __name__ == '__main__':
    root = tk.Tk()
    gui = Chooser(root, *sys.argv[1:])
    root.mainloop()
    
        
