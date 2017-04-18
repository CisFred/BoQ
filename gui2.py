import os, sys, time, queue, math
import tkinter as tk
from datetime import timedelta, datetime

class Asker(tk.Toplevel):
    def __init__(self, master, cls, **kwargs):
        super().__init__(master)
        self.title = tk.Label(self, text="What is")
        self.cls = cls
        self.vals = dict()
        flds = cls._fnames
        for i in range(len(flds)):
            f = flds[i]
            w1 = tk.Label(self, text=f)
            self.vals[f] = tk.StringVar()
            if f not in kwargs:
                v = ''
                w2 = tk.Entry(self, textvariable=self.vals[f])
            else:
                v = kwargs.pop(f)
                w2 = tk.Label(self, textvariable=self.vals[f])

            self.vals[f].set(v)
            w1.grid(row=i+1, column=0, sticky=tk.W)
            w2.grid(row=i+1, column=1, sticky=tk.E)
        for i2 in range(len(kwargs)):
            f = list(kwargs.keys())[i2]
            w1 = tk.Label(self, text=f)
            w2 = tk.Label(self, text=kwargs[f])
            w1.grid(row=i+i2+2, column=0, sticky=tk.W)
            w2.grid(row=i+i2+2, column=1, sticky=tk.E)
        qt = tk.Button(self, text='Cancel', command=self.destroy)
        ac = tk.Button(self, text='Save', command=self.saveme)
        qt.grid(row=i+i2+3, column=0, sticky=tk.W)
        ac.grid(row=i+i2+3, column=1, sticky=tk.E)
    def saveme(self):
        v = {x: self.vals[x].get() for x in self.vals}
        print("Saveme", v)
        self.cls(**v).save()
        self.destroy()


class CountDown(tk.Frame):
    def __init__(self, master, name=None, when=False, at=False, next=False,
                 fmt=False, up=False, **kwargs):
        super().__init__(master, relief=tk.RAISED, border=1)
        self.start = time.time()
        if at:
            self.when = None
            now = datetime.now()
            for w in at:
                then = now.replace(hour=w[0], minute=w[1])
                if now < then:
                    self.when = (then - now).total_seconds()
                    name += ' ({}:{})'.format(*w)
                    break
        else:
            self.when = when if when is not False else self.start
        self.next = next
        self.up = up
        if name:
            self.name = tk.Label(self, text=name)
        if fmt:
            self.mid = tk.Label(self, text='')
            self.fmt = fmt
        else:
            self.mid = None
        self.value = tk.Label(self, text=self.elapsed())
        if name:
            self.name.grid(row=0, column=0,sticky=tk.W)
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        if self.mid:
            self.mid.grid(row=0, column=1,sticky=tk.E)
            self.value.grid(row=0, column=2,sticky=tk.E)
            self.columnconfigure(2,weight=1)
        else:
            self.value.grid(row=0, column=1,sticky=tk.E)
        for k,v in kwargs.items():
            setattr(self,k,v)

    def refresh(self):
        v = self.elapsed()
        bkg = 'white'
        if not self.up:
            try:
                if v < 60:
                    bkg = 'red'
                elif self.next and v < self.next*0.1:
                    bkg = 'orange'
            except:
                pass
        v = str(timedelta(seconds=v)) if v != '???' else v
        self.value.config(text=v, bg=bkg)
        if self.mid:
            try:
                self.mid.config(text=self.fmt.format(**vars(self)), fg='red')
            except:
                print('oops:', sys.exc_info()[1], vars(self))
                traceback.print_exc()
                pass
    def elapsed(self):
        if self.when is None:
            return '???'
        val = time.time()-self.start
        if not self.up:
            if val >= self.when:
                if self.next:
                    self.start = time.time()
                    self.when = self.next
                    val = 0
                else:
                    self.when = val
            val = self.when - val
        return int(val)
    def set_cd(self, new_val):
        self.start = time.time()
        self.when = new_val

class CInfo(tk.LabelFrame):
    def __init__(self, master, name=None, fmt=None, fields={}, debug=False, **kwargs):
        super().__init__(master, relief=tk.RAISED, border=2)
        self.name = name
        self.fmt = fmt
        self.debug = debug
        if name:
            self.what = tk.Label(self, text=self.name)
            self.what.grid(row=0, column=0, sticky=tk.W)
            self.columnconfigure(0,weight=1)
        self.values = dict()
        self.format = dict()

        col = 1
        for f in fields:
            if isinstance(f,tuple):
                (fname, fmt) = f
            else:
                (fname, fmt) = (f, '{%s}' % f)
            if self.debug:
                print('format for', fname, ':', fmt)
            setattr(self, fname, '')
            self.format[fname] = fmt
            frm = tk.Frame(self, bg=fname, bd=2)
            self.values[fname] = tk.Label(frm, text='')
            self.values[fname].grid(sticky=tk.NSEW)
            self.values[fname].columnconfigure(0,weight=1)
            frm.grid(row=0, column=col, sticky=tk.E+tk.W)
            self.columnconfigure(col,weight=1)
            col+=1
        for k,v in kwargs.items():
            setattr(self,k,v)
        self.refresh()
    def set(self, **kwargs):
        self.__dict__.update(kwargs)
        self.refresh()
    def refresh(self, **kwargs):
        v = vars(self)
        v.update(kwargs)

        for f in self.values:

            try:
                tx = self.format[f].format(**v)
            except:
                tx = sys.exc_info()[1]
            if self.debug:
                print('refresh for', f, ':', tx)
            self.values[f].config(text=tx)
            
class Info(tk.Frame):
    def __init__(self, master, name='', fmt=None, centered=False,
                 transf= lambda x:x, **kwargs):
        super().__init__(master, relief=tk.RAISED, border=1)
        self.name = name
        self.fmt = fmt
        self.transf = transf
        self.what = tk.Label(self, text=self.name)
        self.value = tk.Label(self, text=self.fmt)
        self.what.grid(row=0, column=0, sticky=tk.W)
        self.vals = list(kwargs.keys())
        for f in kwargs:
            setattr(self, f, transf(kwargs[f]))
        if not centered:
            self.value.grid(row=0, column=1, sticky=tk.E)
        else:
            self.value.grid(row=0, column=1, sticky=tk.E+tk.W)
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.refresh()
    def set(self, **kwargs):
        self.__dict__.update(**kwargs)
        self.refresh()
    def refresh(self):
        try:
            v = {x: self.transf(getattr(self,x,'?!?')) for x in self.vals}
            tx = self.fmt.format(**v)
        except:
            tx = sys.exc_info()[1]
        self.value.config(text=tx)


class Removable(tk.Frame):
    def __init__(self, master, tag=None, text=None, action=None, **kwargs):
        super().__init__(master, relief=tk.RAISED, border=1)
        self.tag = tag
        self.up = master
        if text:
            self.widget = tk.Label(self, text=text)
        elif action:
            self.widget = tk.Button(self, text=action[0], command=action[1])
        else:
            self.widget = tk.Label(self, text='?? {} ??'.format(kwargs))
        b = tk.Button(self, text='X', command=self.bye)
        self.widget.grid(column=0, row=0, sticky=tk.EW)
        b.grid(column=1, row=0, sticky=tk.E)
        self.columnconfigure(0,weight=2)
        self.columnconfigure(1,weight=1)
    def bye(self):
        if self.tag:
            print('removing', self.tag)
            self.up.notes[self.tag] = None
        self.destroy()
    def update(self, text=None, action=None):
        self.widget.configure(text=text if text else action[0])

class Note(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, relief=tk.RAISED, border=1)
        self.notes = dict()

        
    def add(self, tag=None, text=None, action=None):
        if tag and tag in self.notes:
            if self.notes[tag]:
                self.notes[tag].update(text=text, action=action)
            return
        self.notes[tag] = Removable(self, tag=tag, text=text)
        self.notes[tag].grid(sticky=tk.EW)
        self.notes[tag].columnconfigure(0,weight=1)
    def delete(self, tag=None, text=None, action=None):
        if tag and tag in self.notes:
            self.notes[tag].destroy()
            self.notes[tag] = None
        
