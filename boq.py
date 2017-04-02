import traceback, sys, os
from struct import *
import getopt, pprint, datetime
from collections import namedtuple
import amfy
from scapy.all import sniff
import math
from decode import handled, ignored

packets = {}

players = {}

def log(tag, *args, **kwargs):
  with open('errlog', 'a'):
    print(tag, ':', *args, kwargs)


def handle_command(t, b):
  if hasattr(b,'load'):
    load = b.load
    if len(load) > 5:
      try:
        (ln,c1,c2) = unpack(">I2B", load[0:6])
        r = amfy.loads(load[10:])
        print("Sending {:02x}_{:02X} {}".format(c1,c2,r))
      except:
        log('short load outbound', sys.exc_info(), load)
  # else:
  #   print("Sending ACK")

def handle_info(t, b):
  try:
    (ln,c1,c2) = unpack(">I2B", b[0:6])
  except:
    print("Received bytes {} ({})".format(len(b), b))
  cmd = '{:02X}_{:02X}'.format(c1,c2)
  try:
    r = amfy.loads(b[10:])
  except:
    print('amfy fail ({}) on {}'.format(sys.exc_info(), b[10:]))
    with open('amfy_fail', 'a') as o:
      print('amfy fail ({}) on {}'.format(sys.exc_info(), b[10:]), file=o)
    return

  if cmd not in ignored:
    try:
      print(cmd, '-->', r)
    except:
      # print('burp on {:02x}_{:02x}'.format(c1,c2), sys.exc_info()[1])
      pass

  try:
    os.makedirs('amf/{:02X}'.format(c1))
  except OSError:
    pass
  except:
    print(sys.exc_info())
    pass

  try:
    with open('amf/{:02X}/{:02X}'.format(c1,c2), 'a') as o:
      pprint.pprint(r, stream=o)
  except:
    pass
    

  if cmd in handled:
    res = handled[cmd](r, what_cmd=cmd)
    if res:
      res.update({'who': t})
      # print('res is', res)
    return res

def pkt_split(tag):
  res = list()
  org = bt = packets[tag]
  packets[tag] = b''
  while True:
    (ln,) = unpack('>I', bt[0:4])
    if ln+10 == len(bt):
      res.append(bt)
      return res
    elif ln+10 > len(bt):
      print('Shorted multi', 'len', ln, 'instead of', len(bt))
      with open('pkt/short', 'a') as o:
        print(org, file=o)
        print('len', ln, len(bt), 'in', bt, file=o)
        print('----------\n', file=o)
      packets[tag] = b''
      return res
    res.append(bt[0:ln+10])
    bt = bt[ln+10:]

def assemble(tag, p):
  global packets

  if tag not in packets:
    packets[tag] = p.load
  else:
    packets[tag] += p.load
    
  if p['TCP'].flags & 0x08:
    return pkt_split(tag)
  return ()

def handle_pck(p, outf=None):

  tag = p['IP'].src + '/' + str(p['TCP'].dport)

  if hasattr(p, 'load'):
    print(tag, ':', p.load, file=outf)

  if tag.startswith('192.168'):
    handle_command(tag, p)
  elif 'Padding' in p:
    return None
  else:
    p_list = assemble(tag, p)
    ret = {}
    for pkt in p_list:
      cur = len(pkt)
      (ln,) = unpack(">I", pkt[0:4])
      ln += 10
      if ln == len(pkt):
        res = handle_info(tag, pkt)
        if res:
          ret.update(res)
      else:
        print("Expected ({0} {1}) got ({2} {2:x})".format(ln, pkt[0:4], len(pkt)))
        with open('pkt/strg', 'a') as o:
          print('base', pkt, 'ln', ln, file=o)
    ret.update({'who': tag})
    return ret
    
def sniffer(q, filter, outf):
  if outf:
    if outf == '-':
        sniff(filter=filter,
              prn=lambda p:q.put(handle_pck(p, outf=sys.stdout)))
    else:
        with open(outf, 'a') as outf:
            sniff(filter=filter,
                  prn=lambda p:q.put(handle_pck(p, outf=outf)))

  else:
      with open(os.devnull, 'w') as outf:
          sniff(filter=filter,
                prn=lambda p:q.put(handle_pck(p, outf=outf)))



if __name__ == '__main__':
  from scapy.all import sniff
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
