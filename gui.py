import os, sys, time, queue
import tkinter as tk
from datetime import timedelta, datetime
from multiprocessing import Process, Queue
import getopt
import traceback
from boq import sniffer

todo = []

class MineW(tk.Frame):
    def __init__(self, master):
        super().__init__(master, relief=tk.RAISED, border=1)
        tk.Label(self, text='M').grid(row=0, column=0, sticky=tk.W)
        self.nodes = CInfo(self, fields=('purple', 'blue', 'green'))
        self.cd = CountDown(self, when=None, next=600)
        self.nodes.grid(row=0, column=1, sticky=tk.E+tk.W)
        self.cd.grid(row=0, column=2, sticky=tk.E)
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)
    def set_cd(self, *args, **kwargs):
        self.cd.set_cd(*args, **kwargs)

class ManorCount(tk.Frame):
    def __init__(self, master, what, data):
        super().__init__(master, relief=tk.RAISED, border=1)
        self.green = 0
        self.orange = 0
        self.black = 0
        max_cd = 0
        min_cd = 99999999999
        for x in data:
            self.black += 1
            if x['left_times']:
                self.orange += 1
                if x['cd']:
                    if x['cd'] < min_cd:
                        min_cd = x['cd']
                    if x['cd'] > max_cd:
                        max_cd = x['cd']
                else:
                    self.green += 1

        self.what = CInfo(self, name='F', fields=('black', 'green', 'orange'))
        self.cd1 = CountDown(self, when=min_cd)
        self.cd2 = CountDown(self, when=max_cd)

        self.what.grid(row=0, column=0, sticky=tk.W)
        self.cd1.grid(row=0, column=1, sticky=tk.W+tk.E)
        self.cd2.grid(row=0, column=2, sticky=tk.E)
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)


class ManorLine(tk.Frame):
    def __init__(self, master, who, data):
        super().__init__(master, relief=tk.RAISED, border=1)
        self.who = tk.Label(self, text=who)
        self.flowers = ManorCount(self, 'Flowers', data[1])
        self.fruits = ManorCount(self, 'Fruits', data[2])
        self.who.grid(row=0, column=0, sticky=tk.W)
        self.flowers.grid(row=0, column=1, sticky=tk.W+tk.E)
        self.fruits.grid(row=0, column=2, sticky=tk.E)
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)

class Manor(tk.Toplevel):
    def __init__(self, master, manors):
        super().__init__(master, relief=tk.RAISED, border=1)
        self.title = ManorLine(self, 'My Self', manors['My Self'])
        self.title.grid(row=0, column=0, sticky=tk.E+tk.W)
        self.columnconfigure(0,weight=1)

        
    

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
        register(self.tick)
    def tick(self):
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
            if val >= self.when and self.next:
                self.start = time.time()
                self.when = self.next
                val = 0

            val = self.when - val
        return int(val)
    def set_cd(self, new_val):
        self.start = time.time()
        self.when = new_val

class Detach(tk.Toplevel):
    def __init__(self, master, name='', **kwargs):
        super().__init__(master)
        self.name = name
        self.what = tk.Label(self, text=self.name)
        self.inside = tk.Frame(self, relief=tk.RAISED, border=1)
        self.q = tk.Button(self, text='Close', command=self.destroy)
        self.__dict__.update(kwargs)


class CInfo(tk.Frame):
    def __init__(self, master, name=None, fmt=None, fields={}, **kwargs):
        super().__init__(master, relief=tk.RAISED, border=1, bg='grey')
        self.name = name
        self.fmt = fmt
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
            setattr(self, fname, '')
            self.format[fname] = fmt
            self.values[fname] = tk.Label(self, text='', fg=fname, bg='grey')
            self.values[fname].grid(row=0, column=col, sticky=tk.E+tk.W)
            self.columnconfigure(col,weight=1)
            col+=1
        for k,v in kwargs.items():
            setattr(self,k,v)
        self.refresh()
    def set(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self,k,v)
        self.refresh()
    def refresh(self, **kwargs):
        v = vars(self)
        v.update(kwargs)
        for f in self.values:
            try:
                tx = self.format[f].format(**v)
            except:
                tx = sys.exc_info()[1]
            self.values[f].config(text=tx)
            
class Info(tk.Frame):
    def __init__(self, master, name='', fmt=None, centered=False, **kwargs):
        super().__init__(master, relief=tk.RAISED, border=1)
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
        self.title = Info(self, name='', tag=tag, centered=True, fmt='{tag}')
        self.exo = CountDown(self, name='E_M', when=None, next=3600,
                             fmt='{nb}', nb='')
        self.d_content = CInfo(self, name='D',
                               fields=(('black', '{black}/10'),
                                       'blue', 'purple', 'yellow'))
        self.exp = Info(self, name='X', fmt='{current_xp}/{next_level}',
                        current_xp='?', next_level='??')
        self.title.grid(sticky=tk.E+tk.W)
        self.exo.grid(sticky=tk.E+tk.W)
        self.d_content.grid(sticky=tk.E+tk.W)
        self.exp.grid(sticky=tk.E+tk.W)
        self.columnconfigure(0,weight=1)
        self.last_upd = time.time()
    def tick(self):
        self.last_upd = time.time()


class MainHud(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.started = CountDown(self, name='Started', up=True)
        self.dailies = CountDown(self, name='D', when=None, next=1800)
        self.mine = MineW(self)
        # self.orcs = CountDown(self, name='O', when=None, next=1800)
        self.creeps = CountDown(self, name='C', at=([7,0],[13,30],[16,0]))
        self.bossS = CountDown(self, name='BW', at=([9, 0],[14,30]))
        self.bossG = CountDown(self, name='GB')
        self.started.grid(sticky=tk.E+tk.W)
        self.dailies.grid(sticky=tk.E+tk.W)
        self.mine.grid(sticky=tk.E+tk.W)
        # self.orcs.grid(sticky=tk.E+tk.W)
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
                # print('Read', xx)
                who = xx.pop('who')
                if who not in self.huds:
                    h = Hud(self.main_frame, tag=who)
                    self.huds[who] = h
                    h.grid(row=0, column=len(self.huds))
                else:
                    h = self.huds[who]

                h.tick()
                # print('got', xx, 'from', who)
                for k in xx:
                    print('Proc', k, 'for', who)
                    if hasattr(self, k):
                        getattr(self, k)(xx[k], h)
        for k,h in self.huds.items():
            if time.time() - h.last_upd > 60:
                print('nuke idle', k)
                h.destroy()
                del self.huds[k]



    def xp(self, d, hud):
        for i in d:
            setattr(hud.exp, i, d[i])
        hud.exp.refresh()
        hud.tick()

    def tick(self, d, hud):
        hud.tick()

    def set_orcs(self, d, hud):
        self.general.orcs.set_cd(d)

    def mine_refresh(self, d, hud):
        self.general.mine.set_cd(d)

    def merchant_refresh(self, d, hud):
        n = 0
        for (a,b) in [x.split(':') for x in d['mystic_status'].split(',')]:
            n += int(b)
        hud.exo.nb = n if n else ' '
        hud.exo.set_cd(d['left_time'])
        hud.tick()

    def dailies(self, d, hud):
        self.general.dailies.set_cd(d['next_refresh']);
        p = {3: 0, 4: 0, 5: 0}
        for i in d['possible']:
            if i['quality'] in p:
                p[i['quality']] += 1
            else:
                p[i['quality']] = 1
        hud.d_content.set(black=d['done'], blue=p[3], purple=p[4], yellow=p[5])
        hud.tick()

    def manor(self, d, hud):
        if 'self' in d:
            self.I_am({'player_name':  d['lands'][0]['planter_name']})

            for k in d['friends']:
                if 'name' in k and 'player_id' in k:
                    players[d['name']] = k['player_id']
                    players[d['player_id']] = k['name']
            
        p_list = [(x['cd'], x['left_times'], x['plant_level'],
                   x['seed_level'], x['lev']) for x in d['lands']]
        f_list = [(x['cd'], x['left_times'], x['plant_level'],
                   x['seed_level'], x['lev']) for x in d['flowers']]

        if 'self' in d:
            manor['My Self'] = (0, p_list, f_list)
        else:
            manor[players[d['player_id']]] = (d['level'], p_list, f_list)


        if not hasattr(self, 'manor'):
            self.manor=Manor(self, 'Manor', manors=manor)
        else:
            self.manor.set(manors=manor)
        self.manor.refresh()

        
    def I_am(self, d, hud=None):
        hud.title.tag = d['player_name']
        hud.title.refresh()
        hud.tick()

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
