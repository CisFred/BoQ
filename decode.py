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

ignore('08_0B', '08_0C')

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
def decode(d):
  return {'xp': {'current_xp': num_reduce(d['zhujue_exp'])}}


# Player stuff
@handler('08_04')
def decode(d):
  if 'name' in d and 'player_id' in d:
    players[d['name']] = d['player_id']
    players[d['player_id']] = d['name']
  return {'I_am': [d['player_id'], d['name']]}
  

# Mine stuff
@handler('41_11')
def decode(d):
  return {'mine_refresh': d['next_refresh']}



@handler('1B_03', '08_08')
def decode(d):
  if 'name' in d and 'player_id' in d:
    players[d['name']] = d['player_id']
    players[d['player_id']] = d['name']
  return {'associate': [d['player_id'], d['name']]}

@handler('19_09')
def decode(d):
  return {'manor': d}

@handler('35_04')
def decode(d):
  return {'merchant_refresh': d}

@handler('03_07', '04_07')
def decode(d):
  where = list(d.keys())[0]
  items = d[where]
  size = len(items)
  print(where, size, 'items')
  if False:
    for i in items:
      print('{num} {id} {price}'.format(i))

@handler('49_08')
def decode(d):
  n = None
  try:
    n = d['next_refresh']
  except:
    pass
  return {'set_orcs': n}


@handler('25_0F')
def decode(d):
    res = {'next_refresh': d['next_refresh_left_time'],
           'done': d['award_times'], 'possible': list()}
    for quest in d['pending']:
        if quest['quality'] > 1 and not quest['finished']:
            res['possible'].append(quest)
    return {'dailies': res}
