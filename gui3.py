import os, sys, time, queue, math
import tkinter as tk
from datetime import timedelta, datetime
from gui2 import Info, CountDown, CInfo, Asker, Note
from dbnext import GenView, Chooser


cl = ('black', 'green', 'blue', 'purple')

class Minemap(tk.Frame):
    def __init__(self, master):
        super().__init__(master, relief=tk.RAISED, border=1)
        tk.Label(self, text='Map').grid(row=0, column=0, sticky=tk.W)
        self.map = tk.Canvas(self, width=500, height=200)
        self.map.grid()
        self.nodes = dict()
    def set_nodes(self, d):
        self.map.delete(tk.ALL)
        self.nodes = {n['index']: self.make_node(n) for n in d if n}
    def make_node(self, n):
        if not n:
            return None
        x = n['x'] // 5
        y = n['y'] // 5
        return self.map.create_rectangle(x-4, y-4, x+4, y+4, fill=cl[n['type']])
    def remove_node(self, n):
        if n in self.nodes and self.nodes[n]:
            self.map.delete(self.nodes[n])
        self.nodes[n] = None

class MineW(tk.Frame):
    def __init__(self, master):
        super().__init__(master, relief=tk.RAISED, border=1)
        tk.Label(self, text='Mi').grid(row=0, column=0, sticky=tk.W)
        self.lst = [None for i in range(60)]
        self.nodes = CInfo(self, fields=('purple', 'blue', 'green'))
        self.cd = CountDown(self, when=None, next=600)
        self.map = Minemap(tk.Toplevel(master))
        self.nodes.grid(row=0, column=1, sticky=tk.E+tk.W)
        self.cd.grid(row=0, column=2, sticky=tk.E)
        self.map.grid()
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)
    def set_cd(self, *args, **kwargs):
        self.cd.set_cd(*args, **kwargs)
    def remove_node(self, nb):
        if self.lst[nb]:
            n = self.lst[nb]
            self.lst[nb] = None
        else:
            print('removing unknown node', nb, 'in', self.lst)
        self.map.remove_node(nb)
        self.update_nodes()
        self.nodes.refresh()
    def set_nodes(self, d):
        for n in d:
            id = n['index'] if 'index' in n else n['node_id']
            self.lst[id] = n
        self.update_nodes()
        self.map.set_nodes(self.lst)
        self.nodes.refresh()
        
    def update_nodes(self):
        self.nodes.green = self.nodes.blue = self.nodes.purple = 0
        for n in self.lst:
            if not n:
                continue
            if n['type'] == 1:
                self.nodes.green += 1
            elif n['type'] == 2:
                self.nodes.blue += 1
            elif n['type'] == 3:
                self.nodes.purple += 1
            else:
                print('!!!', n)
        
    def refresh(self):
        self.nodes.refresh()
        self.cd.refresh()

class Table(tk.Toplevel):
    def __init__(self, master, row=0, col=0, **kwargs):
        super().__init__(master)
        self.cells = dict()
        for c in range(col):
            for r in range(row):
                self.cells[(r*row)+c] = None
            self.columnconfigure(c, weight=1)
        self.setup(**kwargs)
    def setup(self, **kwargs):
        pass
