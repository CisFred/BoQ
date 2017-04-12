import math
from datetime import timedelta

handled = {}
ignored = {}

equip_level = ('bronze', 'iron', 'silver', 'gold', 'aurian',
               'rubian', 'mithrillan', 'argentian', 'ferrian')
               
def handler(*tags):
  global handled
  def wrap(f):
    def newf(*args, **kwargs):
      return f(*args, **kwargs)
    for tag in tags:
      handled[tag] = newf
    return newf
  return wrap

def gen_handler(d):
  global handled
  for tag, tags in d.items():
    for t in tags:
      handled[t] = lambda d,w,tg=tag: (lambda i,r: r)(d.update({'what_cmd': w}),{tg:d})


def ignore(*tags):
  global ignored
  for tag in tags:
    ignored[tag] = None

ignore('08_0B', '08_0C', '19_09', '1C_04', '02_08')

# ignore('18_0A',
#        '1C_04',
#        '02_05', '02_08', '02_0B',
#        '08_06', '08_07', '08_0B', '08_0C',
#        '34_0C',
#        '3E_06',
# )

@handler('02_08')
def decode(d, w):
  return {'xp': {'current_xp': d['zhujue_exp']}}


gen_handler({'player': ('08_04', '08_06'),
             'play_gen': ('4C_0A', '02_05', '09_08', '02_0B', '0A_0A'),
             'mine': ('41_11', '41_0C', '41_08', '41_09'),
             'associate': ('xx1B_03', '08_08', '3E_06'),
             'manor': ('19_09',),
             'merchant_refresh': ('35_04',),
             'inventory': ('03_07', '04_07')})


@handler('49_08')
def decode(d, w):
  return {'set_orcs': d['next_refresh'] if 'next_refresh' in d else None}


@handler('25_0F')
def decode(d, w):
    res = {'next_refresh': d['next_refresh_left_time'],
           'done': d['award_times'], 'possible': list()}
    for quest in d['pending']:
        if quest['quality'] > 1 and not quest['finished']:
            res['possible'].append(quest)
    return {'dailies': res}
