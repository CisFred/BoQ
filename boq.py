import traceback, sys
from struct import *
import getopt, pprint, datetime
from scapy.all import sniff
from collections import namedtuple
import amfy
# import dsp.py

packets = {}

handled = {}

players = {}

def handler(*tags):
  global handled
  def wrap(f):
    def newf(*args, **kwargs):
      return f(*args, **kwargs)
    for tag in tags:
      handled[tag] = newf
    return newf
  return wrap

@handler('02_08', '1C_04', '08_07', '08_0B')
def decode(d):
  pass

@handler('1B_03', '08_08')
def decode(d):
  if 'name' in d and 'player_id' in d:
    players[d['name']] = d['player_id']
    players[d['player_id']] = d['name']

@handler('19_09')
def decode(d):
  list_manor = list()
  if 'friends' in d:
    for k in d['friends']:
      # print(k, ':', len(k))
      handled['1B_03'](k)
      list_manor.append(k)
    lm = sorted(list_manor, key=lambda f: f['level'], reverse=True)
    for i in range(0,10):
      print(lm[i]['name'], lm[i]['can_steal'])
  else:
    for x in d['lands']:
      #print(x)
      print('  ', str(datetime.timedelta(seconds=x['cd'])), x['left_times'], x['plant_level'], x['seed_level'], x['lev'])

@handler('03_07', '04_07')
def decode(d):
  where = list(d.keys())[0]
  items = d[where]
  size = len(items)
  print(where, size, 'items')
  if False:
    for i in items:
      print('{num} {id} {price}'.format(i))


def handle_command(b):
  if hasattr(b,'load'):
    (ln,c1,c2) = unpack(">I2B", b.load[0:6])
    print("Sending {:02x}_{:02X} ({})".format(c1,c2,ln))
  # else:
  #   print("Sending ACK")

def handle_info(b):
  (ln,c1,c2) = unpack(">I2B", b[0:6])
  # print("Received bytes {}/{} ({})".format(len(packets[b]), ln, packets[b]))
  cmd = '{:02X}_{:02X}'.format(c1,c2)
  try:
    r = amfy.loads(b[10:])
  except:
    print('amfy fail ({}) on {}'.format(sys.exc_info(), b[10:]))
    with open('amfy_fail', 'a') as o:
      print('amfy fail ({}) on {}'.format(sys.exc_info(), b[10:]), file=o)

  if cmd in handled:

      handled[cmd](r)

  else:
    print(cmd, '-->', r)
      

def handle_pck(p, outf=None):
  global packets

  tag = p['IP'].src + '/' + str(p['TCP'].dport)
  if tag not in packets:
    packets[tag] = b''

  # print("Packet type 0x{:x}".format(p['TCP'].flags), "from", tag, "cur", len(packets[tag]))

  if hasattr(p, 'load'):
    print(tag, ':', p.load, file=outf)

  if tag.startswith('192.168'):
    handle_command(p)
  else:
    cur = len(packets[tag])
    packets[tag] += p.load
    (ln,) = unpack(">I", packets[tag][0:4])
    ln += 10
    # print('-- {}: len {} - {} - {}, flag {:x}'.format(tag, ln, len(p.load), len(packets[tag]), p['TCP'].flags))
    if ln == len(packets[tag]):
      handle_info(packets[tag])
      packets[tag] = b''
    elif ln < len(packets[tag]):
      print("oops, went over {} ({}) resetting".format(ln, len(packets[tag])))
      with open('pkt/over', 'a') as o:
        print('base', packets[tag], 'ln', ln, 'flags {:x}'.format(p['TCP'].flags), file=o)
      packets[tag] = b''
    elif p['TCP'].flags & 0x08:
      print("oops, strange {} ({}) resetting".format(ln, len(packets[tag])))
      with open('pkt/strg', 'a') as o:
        print('base', packets[tag], 'ln', ln, 'flags {:x}'.format(p['TCP'].flags), file=o)
      packets[tag] = b''
    else:
      print("  Added {} to {} (goal is {})".format(len(p.load), cur, ln))
    
if __name__ == '__main__':
  f = []
  out=None
  clear = False

  opts, args = getopt.getopt(sys.argv[1:], "h:p:f:o:?c",
                             ["host=", "port=", "file=", "output=", "help", "clear"])
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
    sys.unlink('pkt/over')
    sys.unlink('pkt/strg')
  if out:
    if out == '-':
      sniff(filter=' and '.join(f), prn=lambda p: handle_pck(p,outf=sys.stdout))
    else:
      if clear:
        sys.unlink(out)
      with open(out, 'a') as o:
        sniff(filter=' and '.join(f), prn=lambda p: handle_pck(p, outf=o))
  else:
    sniff(filter=' and '.join(f), prn=lambda p: handle_pck(p, outf=None))
