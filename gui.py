import os, sys, time, queue, math
import tkinter as tk
from tkinter import ttk
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
    120: 285e6,
    121: 291e6,
    122: 292e6,
    123: 293e6,
    124: 294e6,
    125: 295e6,
    126: 296e6,
    127: 297e6,
    128: 298e6,
    129: 299e6,
    130: 300e6,
    131: 306e6,
    132: 307e6,
    133: 308e6,
    134: 309e6,
    135: 310e6,
    136: 311e6,
    137: 312e6,
    138: 313e6,
    139: 314e6,
    140: 315e6,
    141: 385e6,
    142: 451e6,
    143: 517e6,
    144: 583e6,
    145: 650e6,
    146: 717e6,
    147: 785e6,
    148: 853e6,
    149: 921e6,

    
    152: 115e7,
    153: 122e7,
    
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




class ManorGroup():
    def __init__(self, data):
        self.group(data)
        self.tag = 'white'
        
    def group(self, lst):
        grp_lst = dict()
        for entry in lst:
            if entry['plant_level'] and entry['left_times']:
                this_cd = entry['cd']
                for grp_cd, grp_value in grp_lst.items():
                    if abs(grp_cd - this_cd) < 180:
                        grp_value['nb'] += 1
                        if this_cd < grp_value['min']:
                            grp_value['min'] = this_cd
                        if this_cd > grp_value['max']:
                            grp_value['max'] = this_cd
                        break
                else:
                    grp_lst[this_cd] = {'min': this_cd, 'max': this_cd, 'nb': 1}
        self.groups = grp_lst
        self.now = time.time()
    def show(self):
        return ' | '.join([
            "{nb}: {when}".format(**g, when=str(timedelta(seconds=int(g['min']))))
            for g in self.groups.values()])

    def refresh(self):
        delta = time.time() - self.now
        self.now = time.time()
        self.tag = 'white'
        for d in self.groups.values():
            if d['min'] > delta:
                d['min'] -= delta
            else:
                self.tag = 'green'
                d['min'] = 0

class ManorLine():
    def __init__(self, player, level, fl_line, fr_line):
        self.player = player
        self.level = level
        self.flowers = ManorGroup(fl_line)
        self.fruits = ManorGroup(fr_line)
        self.tag = self.fruits.tag
    def update(self, level, fl_line, fr_line):
        self.level = level
        self.flowers.group(fl_line)
        self.fruits.group(fr_line)
        self.tag = self.fruits.tag
    def vals(self):
        return (self.player, self.level,
                self.flowers.show(), self.fruits.show())
    def refresh(self):
        self.flowers.refresh()
        self.fruits.refresh()
        self.tag = self.fruits.tag
    def tags(self):
        return list(self.tag)

class Manor(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master, relief=tk.RAISED, border=1)
        self.fields = ('Name', 'Lvl', 'Flowers', 'Fruits')
        self.tree = ttk.Treeview(self, columns=self.fields,
                                 displaycolumns='#all')
        self.tree.column('#0', width=2)
        for f in self.fields:
            self.tree.heading(f,
                              text=f,
                              command=lambda f=f: self.sort(f, False))
            
        self.tree.column('#1', width=100)
        self.tree.column('#2', width=20)

        sb = ttk.Scrollbar(self, orient=tk.VERTICAL, command= self.tree.yview)
        self.tree['yscroll'] = sb
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        sb.grid(row=0, column=1, sticky=tk.NS)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.green = self.tree.tag_configure('green', background='green')
        self.red = self.tree.tag_configure('red', background='red')
        self.white = self.tree.tag_configure('white', background='white')
        self.manors = dict()

    def set(self, player, level, fl_line, fr_line):
        if self.tree.exists(player):
            self.manors[player].update(level, fl_line, fr_line)
            self.tree.item(player,
                           values=self.manors[player].vals(),
                           tags=self.manors[player].tags())
        else:
            self.manors[player]=ManorLine(player, level, fl_line, fr_line)
            for i, v in enumerate(self.tree.get_children()):
                if int(self.tree.set(v, 1)) < level:
                    self.tree.insert('', i, player,
                                     values=self.manors[player].vals(),
                                     tags=self.manors[player].tags())
                    return
            self.tree.insert('', tk.END, player,
                             values=self.manors[player].vals(),
                             tags=self.manors[player].tags())

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



    def refresh(self):
        for m in self.manors.values():
            if m:
                m.refresh()
                self.tree.item(m.player, values=m.vals())

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
        self.note.refresh()

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
        self.orcs.refresh()
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
        self.orcs_on = False
        self.general.grid()
        for i in range(len(nb)):
            h = Hud(self.main_frame, i)
            h.grid(row=0)
            self.huds[i['tag']] = h
        self.master.after(500, self.refresh)
        self.Manors = Manor(self.master)
        self.Asked = dict()

    def refresh(self):
        self.general.in_refresh = True
        try:
            self.read_command()
            self.general.refresh()
            for k, h in self.huds.items():
                if h:
                    h.refresh()
            self.Manors.refresh()
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
            self.general.orcs.grid(sticky=tk.E+tk.W)
            self.orcs_on = True
        print('orc cd ', d)
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
        exo_str = list()
        for (a,b) in [x.split(':') for x in d['mystic_record'].split(',')]:
            o = Stuff.get(id_short_1=b) if b != '0' else None
            if not (o and len(o) and o[0].name):
                unk += 1
                exo_str.append(b)
            else:
                exo_str.append(' ')
        if unk:
            hud.note.add(tag='Exo_Unk', text=str(exo_str))

    def inventory(self, d, hud):
        n = 0
        max = 2
        if 'backpack' in d:
            loc = 'backpack'
            loc_ln = 6
        elif 'warehouse' in d:
            loc = 'warehouse'
            loc_ln = 9
        else:
            return
        for x in d[loc]:
            if not x['id']:
                continue
            r = n // loc_ln
            c = n % loc_ln
            n += 1
            obj = Stuff.get(id=x['id'])

            if not obj or (len(obj) and not obj[0].name):
                if x['id'] not in self.Asked:
                    if 'price' in x and 'num' in x:
                        x['price'] //= x['num']
                    locs = '{} of {}'.format(loc, hud.title.tag)
                    self.Asked[x['id']] = Asker(self.master, cls=Stuff, **x,
                                                row=r+1, col=c+1,
                                                location=locs, ask=self)
        hud.tick()
    def unask(self, i):
        self.Asked[i] = None

    def dailies(self, d, hud):
        self.general.dailies.set_cd(d['next_refresh']);
        p = {3: 0, 4: 0, 5: 0}
        for i in d['possible']:
            if i['type'] == 3 and i['quality'] > 3:
                hud.note.add(tag=str(i), remove=d['next_refresh'],
                             text='Instance %d' % i['quality'])
            elif i['type'] == 4 and i['required_times'] < 5 and i['quality'] > 3:
                hud.note.add(tag=str(i), remove=d['next_refresh'],
                             text='Gold({}) {}'.format(i['required_times'],
                                                       i['quality']))

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
            # print('I am ', me.name, 'id', d['player_id'], 'self', d['self'])
            self.I_am(pls[0], hud)
            friends = [Player(**x).save() for x in d['friends']]
            
            hud.manor.nb=len([x for x in d['lands'] if x['harm'] > 1])
            hud.manor.nb += 1 if d['flowers'][0]['harm'] > 1 else 0
            self.general.manor.set_cd(d['next_update_time'])
            hud.manor.refresh()
        else:
            friends = []

        p = Player(player_id = d['player_id'])
        self.Manors.set(p.name, p.level, p_list, f_list)
        self.Manors.refresh()

        
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
