"""Sound Images v1.20: native music, MIDI interchange and separate ROM builds."""
from pathlib import Path
import argparse, hashlib, json, struct
import mido

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "Rock 'n' Roll Racing (Europe).md"
OUT = ROOT / 'musicas'
SHA = 'b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb'
BASE, END, RAM = 0x20000, 0x234d2, 0x1400
ORDER = 0x18e2
ARGS = {0x83:4, 0x84:1, 0x86:1, 0x87:1, 0x8a:1, 0x8f:1,
        0x91:1, 0x92:1, 0x95:2, 0x98:1, 0x99:2, 0x9b:1}
NAMES = {0x80:'next_pattern',0x81:'rest',0x82:'hold',0x83:'vibrato',
         0x84:'volume',0x85:'stop_song',0x86:'transpose',0x87:'global_transpose',
         0x88:'stop_channel',0x89:'stop_song',0x8a:'tempo',0x8b:'pan_left',
         0x8c:'pan_right',0x8d:'pan_center',0x8e:'wait_forever',0x8f:'loop_begin',
         0x90:'loop_end',0x91:'volume_add',0x92:'volume_sub',0x93:'legato_on',
         0x94:'legato_off',0x95:'jump',0x96:'stop_song',0x97:'stop_song',
         0x98:'master_volume',0x99:'portamento',0x9a:'portamento_off',0x9b:'duration'}

def le(b, p): return int.from_bytes(b[p:p+2], 'little')
def putle(b, p, n): b[p:p+2] = n.to_bytes(2, 'little')
def check_tempo(bpm, ppq):
    if not 1<=bpm<=255 or not 1<=ppq<=64:raise ValueError('Invalid native tempo/grid')
    divider=int(225/ppq+0.5)
    if 1+(bpm*8)//divider>128:raise ValueError('Tempo/grid exceeds native timer: lower --ticks-per-beat or BPM')
def op_name(op):
    return 'note' if op < 128 else ('duration_short' if op >= 224 else
           'instrument' if op >= 160 else NAMES.get(op, 'unknown'))

def original_songs(r):
    starts = [BASE + int.from_bytes(r[BASE+4+i*4:BASE+8+i*4], 'big') for i in range(6)]
    return [r[s:e] for s,e in zip(starts, starts[1:]+[END])]

def decode(b):
    """Follow native pattern lists and counted loops for one intro + loop per channel."""
    h = le(b,0)-RAM+2
    if not 2 <= h <= len(b)-16: raise ValueError('Invalid song header')
    instruments = [b[p:p+32].hex() for p in range(2,h,32)]
    if (h-2)%32: raise ValueError('Unaligned instrument bank')
    events, channels = {}, []
    def off(addr):
        n=addr-RAM+2
        if not 2 <= n < len(b): raise ValueError(f'Pointer outside song: {addr:04x}')
        return n
    for ch in range(6):
        addr=le(b,h+4+ch*2)
        if not addr: channels.append(dict(channel=ch+1,notes=[],ticks=0,loop_tick=None)); continue
        lp=off(addr); list_ticks={lp:0}; pc=off(le(b,lp)); lp+=2
        duration=1; inst=0; trans=0; glob=0; volume=127; tick=0; loop_pc=0; loops=0
        seen={}; notes=[]; tempos=[]; last=None; loop_tick=None; first_inst=None; legato=False
        for step in range(100000):
            state=(pc,lp,duration,inst,trans,glob,volume,loop_pc,loops,legato)
            if state in seen: loop_tick=seen[state]; break
            seen[state]=tick
            op=b[pc]; n=ARGS.get(op,0)
            if 0x9c<=op<0xa0: raise ValueError(f'Unknown command {op:02x}')
            if pc+1+n>len(b): raise ValueError('Truncated command')
            args=list(b[pc+1:pc+1+n]); pos=pc; pc+=1+n
            events[pos]=dict(offset=pos,ram=hex(RAM+pos-2),kind=op_name(op),op=op,args=args)
            if op<128:
                if not 0<=inst<len(instruments): raise ValueError('Instrument outside bank')
                gate=b[2+inst*32+28]
                pitch=((op+trans+glob)&255)+24
                last=dict(tick=tick,duration=max(1,duration-gate),step_ticks=duration,
                          midi_note=pitch,native_note=op,instrument=inst,velocity=volume,
                          offset=pos,legato=legato)
                notes.append(last); tick+=duration
            elif op>=224: duration=op-223
            elif op>=160:
                inst=op-160
                if inst>=len(instruments): raise ValueError('Instrument outside bank')
                trans=b[2+inst*32+27]; volume=127; legato=False
                if first_inst is None:first_inst=inst
            elif op==0x80:
                list_ticks.setdefault(lp,tick)
                nxt=le(b,lp); lp+=2
                if not nxt:
                    loop_tick=list_ticks.get(off(le(b,lp)),0)
                    break
                pc=off(nxt)
            elif op==0x81: last=None; tick+=duration
            elif op==0x82:
                if last: last['duration']=tick+duration-last['tick']
                tick+=duration
            elif op in (0x85,0x88,0x89,0x8e,0x96,0x97): break
            elif op==0x84: volume=args[0]&127
            elif op==0x86: trans=args[0]
            elif op==0x87: glob=args[0]
            elif op==0x8a: tempos.append(dict(tick=tick,bpm=args[0],offset=pos+1))
            elif op==0x8f: loops=args[0]; loop_pc=pc
            elif op==0x90:
                loops=(loops-1)&255
                if loops:pc=loop_pc
            elif op==0x91: volume=(volume+args[0])&127
            elif op==0x92: volume=(volume-args[0])&127
            elif op==0x93:legato=True
            elif op==0x94:legato=False
            elif op==0x95:pc=off(args[0]|args[1]<<8)
            elif op==0x9b:duration=args[0] or 256
        else: raise ValueError('Sequence did not terminate or loop')
        channels.append(dict(channel=ch+1,notes=notes,tempos=tempos,ticks=tick,loop_tick=loop_tick,first_instrument=first_inst))
    return dict(tempo=b[h],ticks_per_beat=b[h+1],lfo=b[h+2],master_volume=b[h+3],
                instruments=instruments,events=sorted(events.values(),key=lambda x:x['offset']),channels=channels)

def native_json(b, song_id):
    d=decode(b)
    return dict(format='Sound Images 1.20 / RnR Europe',id=song_id,data_hex=b.hex(),
                tempo=d['tempo'],ticks_per_beat=d['ticks_per_beat'],lfo=d['lfo'],
                master_volume=d['master_volume'],instruments=d['instruments'],events=d['events'])

def from_json(d):
    b=bytearray.fromhex(d['data_hex']); h=le(b,0)-RAM+2
    original=decode(b)
    if len(d['instruments'])!=len(original['instruments']):raise ValueError('Use MIDI import to rebuild layout')
    for i,s in enumerate(d['instruments']):
        x=bytes.fromhex(s)
        if len(x)!=32:raise ValueError('Each FM instrument must contain 32 bytes')
        b[2+i*32:34+i*32]=x
    for e in d['events']:
        p=e['offset']; op=e['op']; a=e['args']
        if not 0<=op<=255 or len(a)!=ARGS.get(op,0):raise ValueError('Invalid event length')
        if ARGS.get(b[p],0)!=len(a):raise ValueError('Event cannot grow in native editing; use MIDI rebuild')
        b[p:p+1+len(a)]=bytes([op]+a)
    vals=[d[k] for k in ('tempo','ticks_per_beat','lfo','master_volume')]
    check_tempo(vals[0],vals[1])
    b[h:h+4]=bytes(vals); decoded=decode(b)
    if any(not 24<=n['midi_note']<=119 for c in decoded['channels'] for n in c['notes']):
        raise ValueError('A note plus instrument transpose exceeds the native pitch table')
    return bytes(b)

def midi_timeline(d):
    """Keep all looping channels playing until the common export endpoint."""
    end=max(c['ticks'] for c in d['channels']);rows=[];tempos={0:d['tempo']}
    for c in d['channels']:
        row=dict(c);row['notes']=[dict(n) for n in c['notes']];ts=list(c.get('tempos',[]))
        loop=c['loop_tick'];period=c['ticks']-loop if loop is not None else 0
        if period>0:
            for shift in range(period,end+period,period):
                if c['ticks']+shift-period>=end:break
                row['notes'].extend(dict(n,tick=n['tick']+shift) for n in c['notes'] if n['tick']>=loop and n['tick']+shift<end)
                ts.extend(dict(t,tick=t['tick']+shift) for t in c.get('tempos',[]) if t['tick']>=loop and t['tick']+shift<end)
        for n in row['notes']:n['duration']=min(n['duration'],end-n['tick'])
        for t in ts:tempos[t['tick']]=t['bpm']
        row['ticks']=end if row['notes'] else 0;rows.append(row)
    return rows,tempos

def write_midi(b, target):
    d=decode(b); ppq=d['ticks_per_beat']; mid=mido.MidiFile(ticks_per_beat=ppq)
    rows,tempos=midi_timeline(d)
    meta=mido.MidiTrack();mid.tracks.append(meta)
    meta.append(mido.MetaMessage('track_name',name='Sound Images: nominal timing; FM patches in JSON'))
    last=0
    for tick,bpm in sorted(tempos.items()):
        meta.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(bpm),time=tick-last));last=tick
    for row in rows:
        if not row['notes']:continue
        ch=row['channel']-1; tr=mido.MidiTrack(); mid.tracks.append(tr); ev=[]
        tr.append(mido.MetaMessage('track_name',name=f'FM {ch+1} - program = native instrument'))
        inst=None
        for n in row['notes']:
            if not 0<=n['midi_note']<=127:raise ValueError('MIDI pitch overflow')
            if n['instrument']!=inst:
                inst=n['instrument'];ev.append((n['tick'],1,mido.Message('program_change',channel=ch,program=inst)))
            ev.append((n['tick'],2,mido.Message('note_on',channel=ch,note=n['midi_note'],velocity=max(1,n['velocity']))))
            ev.append((n['tick']+n['duration'],0,mido.Message('note_off',channel=ch,note=n['midi_note'],velocity=0)))
        if row['loop_tick'] is not None:
            ev.append((row['loop_tick'],3,mido.MetaMessage('marker',text='LOOP_START')))
        ev.append((row['ticks'],3,mido.MetaMessage('marker',text='LOOP_END')))
        last=0
        for t,_,msg in sorted(ev,key=lambda e:(e[0],e[1])):tr.append(msg.copy(time=t-last));last=t
    mid.save(target)

def compress_repeats(stream):
    """Exact consecutive token runs -> native counted loops (no nested loops)."""
    tokens=[];p=0
    while p<len(stream):
        n=1+ARGS.get(stream[p],0);tokens.append(bytes(stream[p:p+n]));p+=n
    result=bytearray();i=0
    while i<len(tokens):
        best=None
        for span in range(1,min(128,(len(tokens)-i)//2)+1):
            block=tokens[i:i+span];count=1
            while count<255 and tokens[i+count*span:i+(count+1)*span]==block:count+=1
            gain=sum(map(len,block))*(count-1)-3
            if gain>0 and (best is None or gain>best[0]):best=(gain,span,count,block)
        if best:
            _,span,count,block=best;result.extend([0x8f,count]);result.extend(b''.join(block));result.append(0x90);i+=span*count
        else:result.extend(tokens[i]);i+=1
    return result

def patch_midi(path, template):
    """Preserve native effects/compression when MIDI only edits pitches/constant tempo."""
    mid=mido.MidiFile(path); d=decode(template); time=0; programs={}; active={}; notes={}; tempos={}
    for msg in mido.merge_tracks(mid.tracks):
        if not msg.is_meta and msg.type not in ('program_change','note_on','note_off'):return None
        time+=msg.time;tick=time*d['ticks_per_beat']/mid.ticks_per_beat
        if msg.type=='set_tempo':tempos[round(tick)]=round(mido.tempo2bpm(msg.tempo))
        if msg.type=='program_change':programs[msg.channel]=msg.program
        if msg.type=='note_on' and msg.velocity:
            key=(msg.channel,msg.note)
            if key in active:return None
            active[key]=(tick,msg.velocity,programs.get(msg.channel))
        elif msg.type=='note_off' or msg.type=='note_on' and not msg.velocity:
            key=(msg.channel,msg.note)
            if key not in active:continue
            start,vel,inst=active.pop(key)
            notes.setdefault(msg.channel,[]).append((start,tick-start,msg.note,vel,inst))
    if active:return None
    rows,original_tempos=midi_timeline(d)
    if len(tempos)>1 and tempos!=original_tempos:return None
    if len(original_tempos)>1 and tempos!=original_tempos:return None
    changes={};count=0
    for c in rows:
        got=sorted(notes.pop(c['channel']-1,[]));expected=c['notes']
        if len(got)!=len(expected):return None
        for n,e in zip(got,expected):
            if abs(n[0]-e['tick'])>0.001 or abs(n[1]-e['duration'])>0.001 or n[3]!=max(1,e['velocity']) or n[4]!=e['instrument']:return None
            value=e['native_note']+n[2]-e['midi_note'];pos=e['offset']
            if not 0<=value<128:return None
            if pos in changes and changes[pos]!=value:
                raise ValueError(f'MIDI edits conflict in shared pattern at byte {pos}. Edit every repetition equally, or use --rebuild-midi.')
            changes[pos]=value;count+=value!=e['native_note']
    if notes:return None
    b=bytearray(template)
    for pos,value in changes.items():b[pos]=value
    h=le(b,0)-RAM+2
    if tempos and len(original_tempos)==1:
        bpm=next(iter(tempos.values()))
        if not 1<=bpm<=255:raise ValueError('Native tempo range: 1..255')
        check_tempo(bpm,d['ticks_per_beat'])
        b[h]=bpm
    decode(b)
    return bytes(b),dict(mode='native_pattern_patch',changed_note_occurrences=count,bytes=len(b),tempo=b[h])

def compile_midi(path, template, ppq=12):
    """Compile up to five monophonic MIDI channels, retaining template FM instruments."""
    mid=mido.MidiFile(path); d=decode(template); channels={}; active={}; programs={}; tempos=set(); time=0
    quantized=0; end=0
    for msg in mido.merge_tracks(mid.tracks):
        if not msg.is_meta and msg.type not in ('program_change','note_on','note_off'):
            raise ValueError(f'MIDI event {msg.type} is not implemented; convert it to notes/durations first')
        time+=msg.time
        exact=time*ppq/mid.ticks_per_beat;t=round(exact);end=max(end,t)
        if msg.type=='set_tempo':tempos.add(msg.tempo)
        if msg.type=='program_change':programs[msg.channel]=msg.program
        if msg.type not in ('note_on','note_off'):continue
        if abs(t-exact)>0.001:quantized+=1
        ch=msg.channel;key=(ch,msg.note)
        if msg.type=='note_on' and msg.velocity:
            if any(k[0]==ch for k in active):raise ValueError(f'MIDI channel {ch+1} is polyphonic; split chords into channels')
            active[key]=(t,msg.velocity,programs.get(ch,None))
        elif key in active:
            start,vel,inst=active.pop(key)
            if t<=start:raise ValueError('Note shorter than native grid; increase --ticks-per-beat')
            channels.setdefault(ch,[]).append(dict(tick=start,duration=t-start,note=msg.note,velocity=vel,instrument=inst))
    if active:raise ValueError('MIDI contains notes without note-off')
    if not channels or len(channels)>5:raise ValueError('Use 1 to 5 monophonic MIDI channels; FM6 remains available for voices')
    if len(tempos)>1:raise ValueError('Import currently requires one constant MIDI tempo')
    bpm=round(mido.tempo2bpm(next(iter(tempos),mido.bpm2tempo(d['tempo']))))
    check_tempo(bpm,ppq)
    instruments=[bytearray.fromhex(x) for x in d['instruments']]
    # MIDI note lengths are explicit, so disable the native early note-off for this rebuild.
    for x in instruments:x[28]=0
    b=bytearray(2)+b''.join(instruments);h=len(b);putle(b,0,RAM+h-2)
    b.extend(bytes([bpm,ppq,d['lfo'],d['master_volume']])+bytes(12))
    details=[]
    for i,(ch,notes) in enumerate(sorted(channels.items())):
        lp=len(b);putle(b,h+4+i*2,RAM+lp-2);b.extend(bytes(6));start=len(b)
        putle(b,lp,RAM+start-2);putle(b,lp+4,RAM+lp-2)
        current_inst=None;current_dur=None;current_vol=None;cursor=0
        def timed(op,dur):
            nonlocal current_dur
            first=True
            while dur:
                n=min(255,dur)
                if n!=current_dur:
                    b.extend([223+n] if n<=32 else [0x9b,n]);current_dur=n
                b.append(op if first or op==0x81 else 0x82);first=False;dur-=n
        default=d['channels'][i].get('first_instrument')
        if default is None:default=1
        for note in sorted(notes,key=lambda n:n['tick']):
            if note['tick']<cursor:raise ValueError('Overlapping MIDI notes')
            if note['tick']>cursor:timed(0x81,note['tick']-cursor)
            inst=default if note['instrument'] is None else note['instrument']
            if not 0<=inst<len(instruments):raise ValueError(f'Program {inst} not in template (0..{len(instruments)-1})')
            if inst!=current_inst:
                b.extend([0xa0+inst,0x86,0]);current_inst=inst;current_vol=127
            if note['velocity']!=current_vol:b.extend([0x84,note['velocity']]);current_vol=note['velocity']
            pitch=note['note']-24
            if not 0<=pitch<=95:raise ValueError('Supported MIDI pitches: 24..119 (C1..B8)')
            timed(pitch,note['duration']);cursor=note['tick']+note['duration']
        if cursor<end:timed(0x81,end-cursor)
        b.append(0x80);b[start:]=compress_repeats(b[start:])
        details.append(dict(midi_channel=ch+1,fm_channel=i+1,notes=len(notes)))
    if len(b)>3073:raise ValueError(f'Song needs {len(b)} bytes; Z80 limit is 3073. Shorten/simplify MIDI.')
    decode(b)
    return bytes(b),dict(tempo=bpm,ticks_per_beat=ppq,quantized_note_events=quantized,bytes=len(b),channels=details)

def build(r,songs,order):
    if len(order)!=6 or any(x not in range(1,7) for x in order):raise ValueError('Order requires six IDs, each from 1 to 6')
    for b in songs:
        if len(b)>3073:raise ValueError('Song exceeds Z80 music RAM')
        decode(b)
    if sum(map(len,songs))>END-(BASE+28):raise ValueError('Songs exceed available music bank (13494 bytes)')
    result=bytearray(r);p=BASE+28
    for i,b in enumerate(songs):
        result[BASE+4+i*4:BASE+8+i*4]=(p-BASE).to_bytes(4,'big')
        result[p:p+len(b)]=b;p+=len(b)
    result[ORDER:ORDER+6]=bytes(order)
    if result!=r:result[0x18e:0x190]=(sum(struct.unpack('>'+str((len(result)-512)//2)+'H',result[512:]))&65535).to_bytes(2,'big')
    return bytes(result)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--export',action='store_true')
    ap.add_argument('--import-dir',type=Path)
    ap.add_argument('--midi',type=Path)
    ap.add_argument('--song',type=int,choices=range(1,7))
    ap.add_argument('--ticks-per-beat',type=int,default=12)
    ap.add_argument('--rebuild-midi',action='store_true',help='Force new composition; otherwise preserve native patterns when possible')
    ap.add_argument('--order',help='Six comma-separated native song IDs')
    ap.add_argument('--output-rom',type=Path)
    args=ap.parse_args();r=ROM.read_bytes()
    if hashlib.sha256(r).hexdigest()!=SHA:raise ValueError('Unexpected original ROM')
    songs=original_songs(r);order=list(r[ORDER:ORDER+6])
    if args.export or not any((args.import_dir,args.midi,args.order)):
        OUT.mkdir(exist_ok=True);catalog=[]
        for i,b in enumerate(songs,1):
            folder=OUT/f'cancion_{i:02d}';folder.mkdir(exist_ok=True)
            (folder/'original.bin').write_bytes(b)
            obj=native_json(b,i);(folder/'editable.json').write_text(json.dumps(obj,indent=2),encoding='utf8')
            assert from_json(obj)==b
            write_midi(b,folder/'notas.mid');d=decode(b)
            (folder/'secuencia.json').write_text(json.dumps(d['channels'],indent=2),encoding='utf8')
            catalog.append(dict(id=i,bytes=len(b),tempo_nominal=d['tempo'],ticks_per_beat=d['ticks_per_beat'],
                                instruments=len(d['instruments']),notes=sum(len(c['notes']) for c in d['channels']),
                                channels=[{k:v for k,v in c.items() if k!='notes'} for c in d['channels']]))
        (OUT/'orden.json').write_text(json.dumps(order),encoding='utf8')
        (OUT/'catalogo.json').write_text(json.dumps(dict(sha256_original=SHA,order=order,songs=catalog),indent=2),encoding='utf8')
        (OUT/'datos.js').write_text('const originales='+json.dumps([native_json(b,i) for i,b in enumerate(songs,1)])+';',encoding='utf8')
        assert build(r,songs,order)==r
        print(json.dumps(catalog));print('Native JSON roundtrip: all 6 songs and entire ROM identical.')
    if args.import_dir:
        for i in range(6):
            p=args.import_dir/f'cancion_{i+1:02d}'/'editable.json'
            if p.exists():songs[i]=from_json(json.loads(p.read_text(encoding='utf8')))
        p=args.import_dir/'orden.json'
        if p.exists():order=json.loads(p.read_text(encoding='utf8'))
    if args.midi:
        if args.song is None:ap.error('--midi requires --song 1..6')
        converted=None if args.rebuild_midi else patch_midi(args.midi,songs[args.song-1])
        songs[args.song-1],report=converted or compile_midi(args.midi,songs[args.song-1],args.ticks_per_beat)
        print(json.dumps(report))
    if args.order:order=[int(s) for s in args.order.split(',')]
    if any((args.import_dir,args.midi,args.order)):
        if not args.output_rom:ap.error('Changes require --output-rom (new file)')
        result=build(r,songs,order)
        with args.output_rom.open('xb') as f:f.write(result)
        print(json.dumps(dict(output=str(args.output_rom),identical=result==r,order=order,sha256=hashlib.sha256(result).hexdigest())))

if __name__=='__main__':main()
