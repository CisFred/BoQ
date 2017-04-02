import math
from datetime import timedelta

handled = {}
ignored = {}

players = {}

equip_level = ('bronze', 'iron', 'silver', 'gold', 'aurian',
               'rubian', 'mithrillan', 'argentian', 'ferrian')
               
def num_reduce(n):
  v = math.log(n,10)
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

def handler(*tags):
  global handled
  def wrap(f):
    def newf(*args, **kwargs):
      return f(*args, **kwargs)
    for tag in tags:
      handled[tag] = newf
    return newf
  return wrap

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

def num_reduce(n):
  v = math.log(n,10)
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

@handler('02_08')
def decode(d, what_cmd):
  return {'xp': {'current_xp': num_reduce(d['zhujue_exp'])}}


# Player stuff
@handler('08_04')
def decode(d, what_cmd):
  if 'name' in d and 'player_id' in d:
    players[d['name']] = d['player_id']
    players[d['player_id']] = d['name']
  return {'I_am': {'player_id': d['player_id'], 'player_name': d['name']}}
  

# Mine stuff
@handler('41_11', '41_0C', '41_08')
def decode(d, what_cmd):
  d.update({'what_cmd': what_cmd})
  return {'mine': d}



@handler('1B_03', '08_08')
def decode(d, what_cmd):
  if 'name' in d and 'player_id' in d:
    players[d['name']] = d['player_id']
    players[d['player_id']] = d['name']
  return {'associate': [d['player_id'], d['name']]}

@handler('19_09')
def decode(d, what_cmd):
  d.update({'what_cmd': what_cmd})
  return {'manor': d}

@handler('35_04')
def decode(d, what_cmd):
  return {'merchant_refresh': d}

# 0A/0A  potions
@handler('4C_0A', '02_05', '09_08', '02_0B', '0A_0A')
def decode(d, what_cmd):
  d.update({'what_cmd': what_cmd})
  return {'play_gen': d}

@handler('03_07', '04_07')
def decode(d, what_cmd):
  return {'inventory': d}

@handler('49_08')
def decode(d, what_cmd):
  n = None
  try:
    n = d['next_refresh']
  except:
    pass
  return {'set_orcs': n}


@handler('25_0F')
def decode(d, what_cmd):
    res = {'next_refresh': d['next_refresh_left_time'],
           'done': d['award_times'], 'possible': list()}
    for quest in d['pending']:
        if quest['quality'] > 1 and not quest['finished']:
            res['possible'].append(quest)
    return {'dailies': res}
