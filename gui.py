import os, sys, time, queue, math
import tkinter as tk
from datetime import timedelta, datetime
from multiprocessing import Process, Queue
import getopt, traceback
from boq import sniffer
import sqlite3
from ndb2 import Player, Stuff, Recipe
from dbnext import GenView, Chooser

todo = []
manors = dict()
stuff = dict()

levels = {
    47: 1656640,
    48: 1826140,
    53: 2900200,
    54: 3165972,
    55: 3446932,
    58: 4425480,
    59: 4797672,
    64: 7050400,
    65: 7592000,
    67: 8771660,
    68: 9421863,
    69: 10094900,
    70: 10818200,
    71: 11584000,
    72: 12393900,
    73: 13249800,
    74: 14150000,
    80: 37131760,
    87: 313300000,
    88: 331638660,
    89: 351134060,
    93: 112e6,
    99: 241e6,
    101: 261e6,
    102: 262e6,
    103: 263e6,
    104: 264e6,
    105: 265e6,
    106: 266e6,
    107: 267e6,
    108: 268e6,
    109: 269e6,
}



def num_reduce(n):
    try:
        v = math.log(n,10)
    except:
        return n
    if v >= 9:
        p = 'G'
        v = 7
    elif v >= 6:
        p = 'M'
        v = 4
    elif v >= 3:
        p = 'K'
        v = 1
    else:
        return n

    rv = n // (10 ** v)
    return '{} {}'.format(rv / 100, p)


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
    def refresh(self):
        self.nodes.refresh()
        self.cd.refresh()

class ManorGroup(tk.Frame):
    def __init__(self, master, what, data, col, row):
        super().__init__(master, relief=tk.RAISED, border=1)
        self.group(data)
        self.grp = []
        self.what = tk.Label(self, text=what[0:2])
        self.grp = [CountDown(self, next=False,
                              name=self.groups[g]['nb'],
                              when=self.groups[g]['min'])
                    for g in sorted(self.groups)]
        self.what.grid(row=0, column=0, sticky=tk.W)
        self.columnconfigure(0,weight=1)
        for n in range(len(self.grp)):
            self.grp[n].grid(row=0, column=n+1, sticky=tk.W+tk.E)
            self.columnconfigure(n+1,weight=1)
        self.grid(row=row, column=col, sticky=tk.E+tk.W)

    def group(self, lst):
        grp_lst = dict()
        for entry in lst:
            if entry['plant_level'] and entry['left_times']:
                this_cd = entry['cd']
                for grp_cd, grp_value in grp_lst.items():
                    if abs(grp_cd - this_cd) < 60:
                        grp_value['nb'] += 1
                        if this_cd < grp_value['min']:
                            grp_value['min'] = this_cd
                        if this_cd > grp_value['max']:
                            grp_value['max'] = this_cd
                        break
                else:
                    grp_lst[this_cd] = {'min': this_cd, 'max': this_cd, 'nb': 1}
        self.groups = grp_lst
    def refresh(self):
        for g in self.grp:
            g.refresh()

class ManorLine():
    def __init__(self, master, data, row):
        p = Player(name=data[1])
        self.who = tk.Label(master,
                            text='{:<30s} {:>3d}'.format(p.name, p.level))
        print('ManorLine', data)
        self.who.grid(row=row, column=0, sticky=tk.W)
        self.flowers = ManorGroup(master, 'Flowers', data[2], col=1, row=row)
        self.fruits = ManorGroup(master, 'Fruits', data[3], col=2, row=row)
    def refresh(self):
        self.flowers.refresh()
        self.fruits.refresh()
    def set(self, data):
        self.who.config(text=data[1])
        self.flowers.group(data[2])
        self.fruits.group(data[3])
        self.flowers.refresh()
        self.fruits.refresh()

class Manor(tk.Toplevel):
    def __init__(self, master, player, friends):
        super().__init__(master, relief=tk.RAISED, border=1)
        self.title = ManorLine(self, manors[player.name], row=0)
        self.mlines = dict()
        self.friends = friends
        self.set()
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)

        
    def set(self):
        by_level = sorted(manors.values(), reverse=True,
                          key=lambda x: x[0] if x[1] in self.friends else 0)

        print('set', len(by_level), '/', len(manors))
        for i in range(len(by_level)):
            if i > 25:
                break
            who = by_level[i][1]
            
            if who in self.mlines:
                self.mlines[who].set(by_level[i])
            else:
                self.mlines[who] = ManorLine(self, by_level[i], row=i+1)
            # self.mlines[who].grid(row=i+1, column=0, sticky=tk.E+tk.W)
            print('line for', who, 'at', i+1)

    def refresh(self):
        self.title.refresh()
        for m in self.mlines.values():
            if m:
                m.refresh()
    

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

class CInfo(tk.Frame):
    def __init__(self, master, name=None, fmt=None, fields={}, debug=False, **kwargs):
        super().__init__(master, relief=tk.RAISED, border=1, bg='lightgrey')
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
            self.values[fname] = tk.Label(self, text='', fg=fname, bg='grey')
            self.values[fname].grid(row=0, column=col, sticky=tk.E+tk.W)
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

class Hud(tk.Frame):
    def __init__(self, master, tag, who='Unknown'):
        super().__init__(master)
        self.tmp = dict()
        self.title = Info(self, name='', tag=tag, centered=True, fmt='{tag}')
        self.exo = CountDown(self, name='E_M', when=None, next=3600,
                             fmt='{nb}', nb='')
        self.d_content = CInfo(self, name='D',
                               fields=(('black', '{black}/10'),
                                       'blue', 'purple', 'yellow'))
        self.exp = Info(self, name='X', fmt='{current_xp}/{next_level}',
                        current_xp='?', next_level='??', transf=num_reduce)
        self.title.grid(sticky=tk.E+tk.W)
        self.exo.grid(sticky=tk.E+tk.W)
        self.d_content.grid(sticky=tk.E+tk.W)
        self.exp.grid(sticky=tk.E+tk.W)
        self.columnconfigure(0,weight=1)
        self.last_upd = time.time()
        self.master = master
    def tick(self):
        self.last_upd = time.time()
    def refresh(self):
        self.title.refresh()
        self.exo.refresh()
        self.d_content.refresh()
        self.exp.refresh()

class MainHud(tk.Frame):
    def __init__(self, root, master):
        super().__init__(master)
        self.root = root
        self.started = CountDown(self, name='Started', up=True)
        self.dailies = CountDown(self, name='D', when=None, next=1800)
        self.mine = MineW(self)
        self.orcs = CountDown(self, name='O', when=None, next=1800)
        self.creeps = CountDown(self, name='C', at=([7,0],[13,30],[16,0]))
        self.bossS = CountDown(self, name='BW', at=([9, 0],[14,30]))
        self.bossG = CountDown(self, name='GB')
        self.show_db = tk.Button(self, text='Show Db',
                                 command=lambda m=master: Chooser(master,
                                                                  'boq_data.db'))
        self.bye = tk.Button(self, text='Quit', command=self.bye)
        self.started.grid(sticky=tk.E+tk.W)
        self.dailies.grid(sticky=tk.E+tk.W)
        self.mine.grid(sticky=tk.E+tk.W)
        self.creeps.grid(sticky=tk.E+tk.W)
        self.orcs_on = False
        self.columnconfigure(0,weight=1)
        self.show_db.grid(sticky=tk.E+tk.W)
        self.bye.grid(sticky=tk.E+tk.W)
    def refresh(self):
        self.started.refresh()
        self.dailies.refresh()
        self.mine.refresh()
        self.creeps.refresh()
        self.bossS.refresh()
        self.bossG.refresh()
    def bye(self):
        self.root.destroy()

class Gui():
    huds = dict()
    def __init__(self, master, queue, nb=None):
        self.master = master
        self.queue = queue
        self.main_frame = tk.Frame(master)
        self.main_frame.grid()
        self.general = MainHud(self.master, self.main_frame)
        self.general.grid()
        for i in range(len(nb)):
            h = Hud(self.main_frame, i)
            h.grid(row=0)
            self.huds[i['tag']] = h
        self.master.after(500, self.refresh)
        self.Manors = dict()

    def refresh(self):
        try:
            self.read_command()
            self.general.refresh()
            for k, h in self.huds.items():
                if h:
                    h.refresh()
            for k, m in self.Manors.items():
                if m:
                    m.refresh()
        except:
            traceback.print_exc()

        # self.master.lift()
        self.master.after(500, self.refresh)

    def read_command(self):
        while not self.queue.empty():
            try:
                xx = self.queue.get(timeout=1)
            except:
                xx = None
            if xx:
                # print('Read', xx)
                who = xx.pop('who')
                if who not in self.huds or not self.huds[who]:
                    print('new HUD for', who)
                    h = Hud(self.main_frame, tag=who)
                    self.huds[who] = h
                    h.grid(row=0, column=len(self.huds))
                else:
                    h = self.huds[who]

                h.tick()
                # print('got', xx, 'from', who)
                for k in xx:
                    if hasattr(self, k):
                        getattr(self, k)(xx[k], h)
        
        for k,h in self.huds.items():
            if h and time.time() - h.last_upd > 300:
                print('nuke idle', k)
                h.destroy()
                self.huds[k] = None


    def xp(self, d, hud):
        hud.exp.set(**d)
        hud.exp.refresh()
        hud.tick()

    def tick(self, d, hud):
        hud.tick()

    def set_orcs(self, d, hud):
        if not self.orcs_on:
            self.orcs.grid(sticky=tk.E+tk.W)
            self.orcs_on = True
        self.general.orcs.set_cd(d)

    def mine_refresh(self, d, hud):
        self.general.mine.set_cd(d)

    def mine(self, d, hud):
        name = 'Mine ' + d.pop('what_cmd')
        GenView(self.master, hud, name=name, js=d)

    def player(self, d, hud):
        p = Player(**d)

    def merchant_refresh(self, d, hud):
        n = 0
        for (a,b) in [x.split(':') for x in d['mystic_status'].split(',')]:
            n += int(b)
        hud.exo.nb = n if n else ' '
        hud.exo.set_cd(d['left_time'])
        hud.tick()

    def inventory(self, d, hud):
        n = 0
        max = 2
        if 'backpack' in d:
            for x in d['backpack']:
                r = n // 6
                c = n % 6
                n += 1
                obj = Stuff.get(id=x['id'])
                if obj and len(obj) and not obj[0].name:
                    if max:
                        if 'price' in x and 'num' in x:
                            x['price'] //= x['num']
                        Asker(self.master, cls=Stuff, **x, row=r, col=c)
                        max -= 1
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

    def play_gen(self, d, hud):
        GenView(self.master, hud, name=d.pop('what_cmd'), js=d)

    def manor(self, d, hud):
        cm = d.pop('what_cmd')
        GenView(self.master, hud, name='Manor ' + cm, js=d)

        fields = ('cd', 'left_times', 'plant_level', 'seed_level', 'lev')
        p_list = [{k: x[k] for k in fields} for x in d['lands']]
        f_list = [{k: x[k] for k in fields} for x in d['flowers']]

        
        if 'self' in d and d['self']:
            pls = Player.get(player_id = d['player_id'])
            me = pls[0]
            print('I am ', me.name, 'id', d['player_id'], 'self', d['self'])
            self.I_am(me, hud)
            friends = [x['name'] for x in d['friends']]
        else:
            friends = []


        return
        p = Player(player_id = d['player_id'])
        manors[p.name] = (p.level, p.name, p_list, f_list)
        print(me, 'added manor for', p.name)
        if me:
            if me not in self.Manors:
                self.Manors[me.name]=Manor(self.master, me, friends)
            else:
                self.Manors[me.name].set()
            self.Manors[me.name].refresh()

        
    def I_am(self, p, hud=None):
        if hud.title.tag != p.name:
            print('Hud', hud.title.tag, '-->', p.name)
            hud.title.tag = p.name
        hud.exp.next_level = levels[p.level] if p.level in levels else '--> {}'.format(p.level)
        hud.title.refresh()
        hud.tick()

    def associate(self, d, hud):
        # d.pop('what_cmd')
        if 'player_name' in d:
            d['name'] = d.pop('player_name')
        try:
            p = Player(**d).save()
        except:
            traceback.print_exc()


    def quit(self):
        print('bubye')
        self.master.destroy()

class Client():
    def __init__(self, master, q):
        self.master = master
        self.queue = q
        self.gui = Gui(self.master, self.queue, {})
        self.master.after(100, self.gui.refresh)

        

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
