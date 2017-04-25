import os, sys, time, queue, math
import tkinter as tk
from datetime import timedelta, datetime
from multiprocessing import Process, Queue
import getopt, traceback
from boq import sniffer
import sqlite3
from ndb2 import Player, Stuff, Recipe
from gui2 import Info, CountDown, CInfo, Asker, Note
from dbnext import GenView, Chooser
from gui3 import MineW

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
    100: 254e6,
    101: 261e6,
    102: 262e6,
    103: 263e6,
    104: 264e6,
    105: 265e6,
    106: 266e6,
    107: 267e6,
    108: 268e6,
    109: 269e6,
    110: 270e6,
    111: 276e6,
    112: 277e6,
    113: 278e6,
    114: 279e6,
    115: 280e6,
    116: 281e6,
    117: 282e6,
    118: 283e6,
    119: 284e6,
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
    

class Hud(tk.Frame):
    def __init__(self, master, tag, who='Unknown'):
        super().__init__(master)
        self.tmp = dict()
        self.title = Info(self, name='', tag=tag, centered=True, fmt='{tag}')
        self.exo = CountDown(self, name='E_M', when=None, next=3600,
                             fmt='{nb}', nb='')
        self.d_content = CInfo(self, name='D',
                               fields=(('white', '{white}/10'),
                                       'blue', 'purple', 'yellow'))
        self.exp = Info(self, name='X', fmt='{current_xp}/{next_level}',
                        current_xp='?', next_level='??', transf=num_reduce)
        self.manor = Info(self, name='Mn', fmt='{nb}', nb='')
        self.note = Note(self)
        self.title.grid(sticky=tk.E+tk.W)
        self.d_content.grid(sticky=tk.E+tk.W)
        self.manor.grid(sticky=tk.E+tk.W)
        self.exo.grid(sticky=tk.E+tk.W)
        self.exp.grid(sticky=tk.E+tk.W)
        self.note.grid(sticky=tk.EW)
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
        self.manor.refresh()

class MainHud(tk.Frame):
    def __init__(self, root, master):
        super().__init__(master)
        self.root = root
        self.in_refresh=False
        self.started = CountDown(self, name='Started', up=True)
        self.dailies = CountDown(self, name='D', when=None, next=1800)
        self.mine = MineW(self)
        self.manor = CountDown(self, name='Ma', when=None, next=None)
        self.creeps = CountDown(self, name='C', at=([7,0],[13,30],[16,0]))
        self.bossS = CountDown(self, name='BW', at=([9, 0],[14,30]))
        self.bossG = CountDown(self, name='GB')
        self.orcs = CountDown(self, name='O', when=None, next=1800)
        self.show_db = tk.Button(self, text='Show Db',
                                 command=lambda m=master: Chooser(tk.Toplevel(master),
                                                                  'boq_data.db'))
        self.bye = tk.Button(self, text='Quit', command=self.bye)
        self.started.grid(sticky=tk.E+tk.W)
        self.dailies.grid(sticky=tk.E+tk.W)
        self.manor.grid(sticky=tk.E+tk.W)
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
        self.manor.refresh()
        self.creeps.refresh()
        self.bossS.refresh()
        self.bossG.refresh()
    def bye(self):
        while self.in_refresh:
            a = [x for x in range(10000)]
            del a
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
        self.general.in_refresh = True
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

        self.master.lift()
        self.general.in_refresh = False
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
                    h.grid(row=0, column=len(self.huds), sticky=tk.N)
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

    def mine(self, d, hud):
        cmd = d.pop('what_cmd')
        if cmd == '41_0C':
            self.general.mine.remove_node(d['index'])
            return
        name = 'Mine ' + cmd

        if 'next_refresh' in d:
            self.general.mine.set_cd(d['next_refresh'])
            return
        try:
            lst = d['mines']
        except:
            try:
                lst = d['new_mines']
            except:
                GenView(self.master, hud, name=name, js=d)
                return
        self.general.mine.set_nodes(lst)
        return
        lst_typ = [0,0,0, 0]
        for m in lst:
            lst_typ[m['type']] += 1
        self.general.mine.nodes.purple = lst_typ[3]
        self.general.mine.nodes.blue = lst_typ[2]
        self.general.mine.nodes.green = lst_typ[1]
        self.general.mine.refresh()


    def player(self, d, hud):
        p = Player(**d)

    def merchant_refresh(self, d, hud):
        n = 0
        for (a,b) in [x.split(':') for x in d['mystic_status'].split(',')]:
            n += int(b)
        hud.exo.nb = n if n else ' '
        hud.exo.set_cd(d['left_time'])
        hud.tick()
        unk = 0
        for (a,b) in [x.split(':') for x in d['mystic_record'].split(',')]:
            if b != '0':
                o = Stuff.get(id_short_1=b)
                if not (o and len(o) and o[0].name):
                    unk += 1
        if unk:
            hud.note.add(tag='Exo_Unk', text='Exo: {} !'.format(unk))

    def inventory(self, d, hud):
        n = 0
        max = 2
        if 'backpack' in d:
            for x in d['backpack']:
                if not x['id']:
                    continue
                r = n // 6
                c = n % 6
                n += 1
                obj = Stuff.get(id=x['id'])

                if not obj or (len(obj) and not obj[0].name):
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
            if i['type'] == 3 and i['quality'] > 3:
                hud.note.add(tag=str(i), text='Instance %d' % i['quality'])
            elif i['type'] == 4 and i['required_times'] < 3 and i['quality'] > 3:
                hud.note.add(tag=str(i), text='Gold({}) {}'.format(i['required_times'], i['quality']))

            if i['quality'] in p:
                p[i['quality']] += 1
            else:
                p[i['quality']] = 1
        hud.d_content.set(white=d['done'], blue=p[3], purple=p[4], yellow=p[5])
        hud.tick()

    def play_gen(self, d, hud):
        try:
            if d['iszhujue']:
                Player(**d)
        except:
            GenView(self.master, hud, name=d.pop('what_cmd'), js=d)

    def manor(self, d, hud):
        cm = d.pop('what_cmd')
        # GenView(self.master, hud, name='Manor ' + cm, js=d)

        fields = ('cd', 'left_times', 'plant_level', 'seed_level', 'lev')
        p_list = [{k: x[k] for k in fields} for x in d['lands']]
        f_list = [{k: x[k] for k in fields} for x in d['flowers']]

        
        if 'self' in d and d['self']:
            pls = Player.get(player_id = d['player_id'])
            me = pls[0]
            # print('I am ', me.name, 'id', d['player_id'], 'self', d['self'])
            self.I_am(me, hud)
            friends = [Player(**x).save() for x in d['friends']]
            
            hud.manor.nb=len([x for x in d['lands'] if x['harm'] > 1])
            hud.manor.nb += 1 if d['flowers'][0]['harm'] > 1 else 0
            self.general.manor.set_cd(d['next_update_time'])
            hud.manor.refresh()
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
            hud.title.tag = p.name
        hud.exp.next_level = levels[p.level+1] if (p.level+1) in levels else '--> {}'.format(p.level+1)
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
