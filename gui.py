import os, sys, time, queue
import tkinter as tk
from datetime import timedelta, datetime
from multiprocessing import Process, Queue
import getopt
from boq import sniffer

todo = []

class CountDown(tk.Frame):
    def __init__(self, master, name, when=False, at=False, next=False, up=False):
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
        self.name = tk.Label(self, text=name)
        self.value = tk.Label(self, text=self.elapsed())
        self.name.grid(row=0, column=0,sticky=tk.W)
        self.value.grid(row=0, column=1,sticky=tk.E)
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        register(self.tick)
    def tick(self):
        self.value.config(text=self.elapsed())
    def elapsed(self):
        if self.when is None:
            return '???'
        val = time.time()-self.start
        if not self.up:
            if val >= self.when and self.next:
                self.start = time.time()
                self.when = self.next
                val = 0

            val = self.when - val
        return str(timedelta(seconds=int(val)))
    def set_cd(self, new_val):
        self.start = time.time()
        self.when = new_val

class CInfo(tk.Frame):
    def __init__(self, master, name='', fmt=None, fields=()):
        super().__init__(master)
        self.name = name
        self.fmt = fmt
        self.what = tk.Label(self, text=self.name)
        self.what.grid(row=0, column=0, sticky=tk.W)
        self.values = dict()
        self.columnconfigure(0,weight=1)
        col = 1
        for f in fields:
            setattr(self, f, '')
            self.values[f] = tk.Label(text='', fg=f)
            self.values[f].grid(row=0, column=col, sticky=tk.E+tk.W)
            self.columnconfigure(col,weight=1)
            col+=1
        self.refresh()
    def set(self, **kwargs):
        self.__dict__.update(kwargs)
        self.refresh()
    def refresh(self, **kwargs):
        v = vars(self)
        v.update(kwargs)
        try:
            tx = self.fmt.format(**v)
        except:
            tx = sys.exc_info()[1]
        self.value.config(text=tx)
            
class Info(tk.Frame):
    def __init__(self, master, name='', fmt=None, centered=False, **kwargs):
        super().__init__(master)
        self.name = name
        self.fmt = fmt
        self.what = tk.Label(self, text=self.name)
        self.value = tk.Label(self, text=self.fmt)
        self.what.grid(row=0, column=0, sticky=tk.W)
        for f in kwargs:
            setattr(self, f, kwargs[f])
        if not centered:
            self.value.grid(row=0, column=1, sticky=tk.E)
        else:
            self.value.grid(row=0, column=1, sticky=tk.E+tk.W)
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.refresh()
    def set(self, **kwargs):
        self.__dict__.update(kwargs)
        self.refresh()
    def refresh(self, **kwargs):
        v = vars(self)
        v.update(kwargs)
        try:
            tx = self.fmt.format(**v)
        except:
            tx = sys.exc_info()[1]
        self.value.config(text=tx)

class Hud(tk.Frame):
    def __init__(self, master, tag, who='Unknown'):
        super().__init__(master)
        self.title = Info(self, name=tag, centered=True, fmt='{name}')
        self.exo = CountDown(self, name='Exotic Merchant', when=None, next=3600)
        self.dailies = CountDown(self, name='Dailies', when=None, next=1800)
        self.exp = Info(self, name='Exp', fmt='{current_xp}/{next_level}',
                        current_xp='?', next_level='??')
        self.exo.grid(sticky=tk.E+tk.W)
        self.dailies.grid(sticky=tk.E+tk.W)
        self.exp.grid(sticky=tk.E+tk.W)
        self.columnconfigure(0,weight=1)



class MainHud(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.started = CountDown(self, name='Started', up=True)
        self.mine = CountDown(self, name='Mining', when=None, next=600)
        self.orcs = CountDown(self, name='Orcs', when=None, next=1800)
        self.creeps = CountDown(self, name='Creeps', at=([7,0],[13,30],[16,0]))
        self.bossS = CountDown(self, name='Boss War', at=([9, 0],[14,30]))
        self.bossG = CountDown(self, name='Guid Boss')
        self.started.grid(sticky=tk.E+tk.W)
        self.mine.grid(sticky=tk.E+tk.W)
        self.orcs.grid(sticky=tk.E+tk.W)
        self.creeps.grid(sticky=tk.E+tk.W)
        self.columnconfigure(0,weight=1)

class Gui():
    huds = dict()
    def __init__(self, master, queue, nb=None):
        self.master = master
        self.queue = queue
        self.main_frame = tk.Frame(master)
        self.main_frame.grid()
        self.general = MainHud(self.main_frame)
        self.general.grid()
        for i in range(len(nb)):
            h = Hud(self.main_frame, i)
            h.grid(row=0)
            self.huds[i['tag']] = h
        self.master.after(500, self.next_tick)

    def next_tick(self):
        global todo
        for f in todo:
            f()
        self.master.after(500, self.next_tick)

    def read_command(self):
        while not self.queue.empty():
            try:
                xx = self.queue.get(timeout=1)
            except:
                xx = None
            if xx:
                print('Read', xx)
                who = xx.pop('who')
                if who not in self.huds:
                    h = Hud(self.main_frame, tag=who)
                    self.huds[who] = h
                    h.grid(row=0, column=len(self.huds))
                else:
                    h = self.huds[who]
                print('got', xx, 'from', who)
                for k in xx:
                    print('Proc', k)
                    if hasattr(self, k):
                        getattr(self, k)(xx[k], h)

    def xp(self, d, hud):
        for i in d:
            setattr(hud.exp, i, d[i])
        hud.exp.refresh()

    def set_orcs(self, d, hud):
        self.general.orcs.set_cd(d)

    def mine_refresh(self, d, hud):
        self.general.mine.set_cd(d)

    def merchant_refresh(self, d, hud):
        hud.exo.set_cd(d['left_time'])
        

    def associate(self, d, hud):
        pass

    def quit(self):
        print('bubye')
        self.master.destroy()

class Client():
    def __init__(self, master, q):
        self.master = master
        self.queue = q
        self.gui = Gui(self.master, self.queue, {})
        register(self.gui.read_command)
        self.master.after(100, self.gui.next_tick)

        
def register(func):
    global todo
    todo.append(func)


if __name__ == '__main__':
    f = []
    out=None
    clear = False

    opts, args = getopt.getopt(sys.argv[1:], "h:p:f:o:?c",
                               ["host=", "port=", "file=", "output=",
                                "help", "clear"])
    for opt, arg in opts:
        if opt in ("-?", "--help"):
            usage()
            sys.exit(0);
        elif opt in ("-h", "--host"):
            f.append("host " + arg)
        elif opt in ("-p", "--port"):
            f.append("port " + arg)
        elif opt in ("-o", "-f", "--file", "--output"):
            out = arg
        elif opt in ("-c", "--clear"):
            clear = True
    
    print("Filter: ", f, ' and '.join(f))

    if clear:
        try:
            os.unlink('pkt/over')
        except:
            pass
        try:
            os.unlink('pkt/strg')
        except:
            pass
        if out and out != '-':
            try:
                os.unlink(out)
            except:
                pass

    filter = ' and '.join(f)
    q = Queue()
    root = tk.Tk()
    g = Client(root, q)
    p = Process(target=sniffer, args=(q, filter, out))
    p.start()
    root.mainloop()
    print('outta here')
    p.terminate()
    sys.exit(0)
