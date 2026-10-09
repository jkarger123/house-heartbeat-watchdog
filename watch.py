import json, os, time, urllib.request
from pathlib import Path

def decide(h, now):
    reasons=[]
    if not isinstance(h,dict): return ['heartbeat unreadable']
    at=h.get('at')
    if not isinstance(at,(int,float)) or at>now+60 or now-at>720: reasons.append('heartbeat missing or stale')
    if h.get('dell_up') is not True: reasons.append('house computer unreachable')
    status=str(h.get('ups_status','UNKNOWN')).split()
    if 'OB' in status: reasons.append('house power out: UPS on battery')
    elif 'OL' not in status: reasons.append('UPS status unknown')
    if h.get('cameras_ok') is not True: reasons.append('camera health degraded or unknown')
    return reasons

def transition(state,reasons,now):
    # 2026-10-09: one failed check is not an outage. Except a UPS on battery (real and urgent), a problem must
    # be seen on two consecutive runs (~10 min) before James is alerted. 'heartbeat unreadable' was flapping.
    state=dict(state); state['bad']=state.get('bad',0)+1 if reasons else 0
    urgent=any(r.startswith('house power out') for r in reasons)
    if reasons and not urgent and state['bad']<2:
        return state,None
    if reasons and (not state.get('active') or now-state.get('sent',0)>=1800):
        return {'active':True,'sent':now,'bad':state['bad']},('House alert','; '.join(reasons))
    if not reasons and state.get('active'):
        return {'active':False,'sent':now,'bad':0},('House all clear','Heartbeat, computer, cameras and mains power are healthy again.')
    return state,None

def main():
    now=time.time()
    h=None
    hdr={'User-Agent':'heartbeat-watchdog'}
    if os.environ.get('GITHUB_TOKEN'): hdr['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']  # anonymous calls were rate-limited
    for attempt in range(3):
        try:
            req=urllib.request.Request('https://api.github.com/gists/'+os.environ['GIST_ID'],headers=hdr)
            with urllib.request.urlopen(req,timeout=20) as r: gist=json.load(r)
            h=json.loads(gist['files']['heartbeat.json']['content'])
            print('Heartbeat fetched and parsed'); break
        except Exception:
            print('Heartbeat fetch failed (attempt %d)' % (attempt+1)); time.sleep(5*(attempt+1))
    p=Path('.state/status.json'); state=json.loads(p.read_text()) if p.exists() else {}
    next_state,msg=transition(state,decide(h,now),now)
    if msg:
        req=urllib.request.Request('https://ntfy.sh/'+os.environ['NTFY_TOPIC'],data=msg[1].encode(),headers={'Title':msg[0],'Priority':'high'})
        with urllib.request.urlopen(req,timeout=30) as r: ack=json.load(r)
        if not ack.get('id'): raise RuntimeError('Notification was not acknowledged')
        print('Notification accepted')
    else: print('Checked: no notification due')
    p.parent.mkdir(exist_ok=True); p.write_text(json.dumps(next_state))
if __name__=='__main__':
    try: main()
    except Exception as e:
        print('Watchdog failed: '+type(e).__name__); raise SystemExit(1)
