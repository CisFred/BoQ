import os, sys, time, queue
import tkinter as tk
from datetime import timedelta, datetime
from multiprocessing import Process, Queue
import getopt, traceback
from boq import sniffer
import sqlite3
from db import Player, Stuff, Recipe, find, AllDbIns, DbFields, InitDbs, CommitDb, SaveEntry, DeleteEntry
from dbnext import GenView

todo = []
players = dict()
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

class Asker(tk.Toplevel):
    def __init__(self, master, *args, cls, **kwargs):
        super().__init__(master)
        self.title = tk.Label(self, text="What is")
        self.cls = cls
        self.vals = dict()
        for i in range(len(args)):
            f = args[i]
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

class OneDb(tk.Toplevel):
    def __init__(self, master, key):
        super().__init__(master, relief=tk.RAISED, border=1)
        fd = [x[0] for x in DbFields[key]]
        mlen = range(len(fd))
        for i in mlen:
            x = tk.Label(self, text=fd[i])
            x.grid(row=0, column=i, sticky=tk.W+tk.E)
        all = AllDbIns[key].get()
        rlen = range(len(all))
        for j in rlen:
            vdict = dict()
            for i in mlen:
                vdict[fd[i]] = v = tk.StringVar()
                v.set(getattr(all[j],fd[i], '?'+fd[i]+'?'))
                x = tk.Entry(self, text=v)
                x.grid(row=j+1, column=i, sticky=tk.W+tk.E)
            d = tk.Button(self, text='x',
                          command=lambda k=key,v=vdict: DeleteEntry(k,v))
            s = tk.Button(self, text='V',
                          command=lambda k=key,v=vdict: SaveEntry(k,v))
            d.grid(row=j+1, column=i+1)
            s.grid(row=j+1, column=i+2)

        for i in mlen:
            self.columnconfigure(i, weight=1)

class ShowDb(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master, relief=tk.RAISED, border=1)
        for k in AllDbIns:
            w = tk.Button(self, text=k, command=lambda x=k,m=master: OneDb(m,x))
            w.grid(sticky=tk.E+tk.W)
            


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
        p = players[data[1]]
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
        self.title = ManorLine(self, manors[player], row=0)
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
        self.tmp = dict()
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
    def refresh(self):
        self.title.refresh()
        self.exo.refresh()
        self.d_content.refresh()
        self.exp.refresh()

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
        self.show_db = tk.Button(self, text='Show Db',
                                 command=lambda m=master: ShowDb(master))
        self.bye = tk.Button(self, text='Quit', command=self.bye)
        self.started.grid(sticky=tk.E+tk.W)
        self.dailies.grid(sticky=tk.E+tk.W)
        self.mine.grid(sticky=tk.E+tk.W)
        self.orcs.grid(sticky=tk.E+tk.W)
        self.creeps.grid(sticky=tk.E+tk.W)
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
        CommitDb()
        sys.exit(0)

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
                    print('Proc', k, 'for', who)
                    if hasattr(self, k):
                        getattr(self, k)(xx[k], h)
        
        for k,h in self.huds.items():
            if h and time.time() - h.last_upd > 300:
                print('nuke idle', k)
                h.destroy()
                self.huds[k] = None


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

    def mine(self, d, hud):
        GenView(self.master, hud, name='Mine ' + d['what_cmd'], js=d)

    def player(self, d, hud):
        p = Player(**d)

    def merchant_refresh(self, d, hud):
        n = 0
        for (a,b) in [x.split(':') for x in d['mystic_status'].split(',')]:
            n += int(b)
        max = 2
        for (a,b) in [x.split(':') for x in d['mystic_record'].split(',')]:
            (fields, obj) = find('stuff', id_short_1=b)
            if not obj:
                if max:
                    Asker(self.master, *fields, cls=Stuff, id_short_1=b,
                          position=a)
                    max -= 1
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
                (fields, obj) = find('stuff', id=x['id'])
                if not obj:
                    if max:
                        if 'price' in x and 'num' in x:
                            x['price'] //= x['num']
                        Asker(self.master, *fields, cls=Stuff, **x,
                              row=r, col=c)
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

    def play_gen(self, d, huf):
        GenView(self.master, hud, name=d.pop('what_cmd'), js=d)

    def manor(self, d, hud):
        me = getattr(self, 'whoami', None)

        GenView(self.master, hud, name='Manor ' + d['what_cmd'], js=d)

        fields = ('cd', 'left_times', 'plant_level', 'seed_level', 'lev')
        p_list = [{k: x[k] for k in fields} for x in d['lands']]
        f_list = [{k: x[k] for k in fields} for x in d['flowers']]

        
        if 'self' in d and d['self']:
            me = d['lands'][0]['planter_name']
            self.I_am({'player_name':  me}, hud)
            friends = [x['name'] for x in d['friends']]
            for k in d['friends'] + [{'name': me, 'player_id': d['player_id'],
                                      'level': 0}]:
                v = {l: k[l] for l in ('name', 'player_id', 'level')}
                if k['name'] not in players:
                    players[k['name']] = Player(**v)
                else:
                    players[k['name']].update(**v)
                players[k['name']].save()
        else:
            friends = []

        CommitDb()
        return
        p = players[d['player_id']]
        manors[p.name] = (p.level, p.name, p_list, f_list)
        print(me, 'added manor for', p.name)
        if me:
            if me not in self.Manors:
                self.Manors[me]=Manor(self.master, me, friends)
            else:
                self.Manors[me].set()
            self.Manors[me].refresh()

        
    def I_am(self, d, hud=None):
        self.whoami = d['player_name']
        hud.title.tag = self.whoami
        hud.title.refresh()
        hud.tick()

    def associate(self, d, hud):
        global players
        try:
            if d['name'] not in players:
                p = Player(**d).save()
        except:
            traceback.print_exc()
            print('players:', players)

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
    InitDbs()
    for p in AllDbIns['player'].get():
        players[p.name] = players[p.player_id] = p
    
    p = Process(target=sniffer, args=(q, filter, out))
    p.start()
    root.mainloop()
    print('outta here')
    p.terminate()
    sys.exit(0)
