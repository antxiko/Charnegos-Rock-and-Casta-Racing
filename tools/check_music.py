"""Meaningful codec checks and a separate, deliberately edited BizHawk test ROM."""
import json, hashlib
import mido
import export_music as m

def main():
    r=m.ROM.read_bytes();songs=m.original_songs(r);checks=[]
    for i,b in enumerate(songs,1):
        assert m.from_json(m.native_json(b,i))==b
        rebuilt,report=m.patch_midi(m.OUT/f'cancion_{i:02d}'/'notas.mid',b)
        assert rebuilt==b
        checks.append(f'Song {i}: native JSON and unedited MIDI byte roundtrip')
    assert m.build(r,songs,list(r[m.ORDER:m.ORDER+6]))==r
    out=m.OUT/'ejemplos';out.mkdir(exist_ok=True)
    mid=mido.MidiFile(ticks_per_beat=12)
    meta=mido.MidiTrack();mid.tracks.append(meta)
    meta.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(120)))
    for ch,program,melody in [(0,4,[60,64,67,64]*8),(1,5,[36,36,43,43]*8)]:
        tr=mido.MidiTrack();mid.tracks.append(tr)
        tr.append(mido.Message('program_change',channel=ch,program=program))
        for note in melody:
            tr.append(mido.Message('note_on',channel=ch,note=note,velocity=100))
            tr.append(mido.Message('note_off',channel=ch,note=note,velocity=0,time=6))
    midi=out/'melodia_prueba.mid';mid.save(midi)
    new,report=m.compile_midi(midi,songs[1]);d=m.decode(new)
    assert [len(c['notes']) for c in d['channels']]==[32,32,0,0,0,0]
    assert [c['ticks'] for c in d['channels'][:2]]==[192,192]
    assert [n['midi_note'] for n in d['channels'][0]['notes']]==[60,64,67,64]*8
    assert [n['midi_note'] for n in d['channels'][1]['notes']]==[36,36,43,43]*8
    checks.append('New two-channel MIDI compiled with counted loops; all 64 pitches and durations verified')
    (out/'melodia_prueba_nativa.json').write_text(json.dumps(m.native_json(new,2),indent=2))
    edited=list(songs);edited[1]=new
    native=m.native_json(edited[0],1);first=next(e for e in native['events'] if e['kind']=='note');first['op']+=1
    edited[0]=m.from_json(native)
    result=m.build(r,edited,[6,5,4,3,2,1])
    # Only music bank, ordering table and header checksum may change.
    assert all(0x2001c<=i<m.END or 0x20004<=i<0x2001c or m.ORDER<=i<m.ORDER+6 or 0x18e<=i<0x190
               for i,(a,b) in enumerate(zip(r,result)) if a!=b)
    rom=m.OUT/'validacion/prueba_musica.gen'
    if rom.exists():assert rom.read_bytes()==result
    else:rom.write_bytes(result)
    for i,b in enumerate(edited,1):(m.OUT/f'validacion/esperado_{i}.bin').write_bytes(b[2:])
    assert hashlib.sha256(m.ROM.read_bytes()).hexdigest()==m.SHA
    checks.append('Original ROM unchanged; test ROM changes confined to music data, song pointers, order and checksum')
    (m.OUT/'validacion/pruebas_codec.json').write_text(json.dumps(dict(checks=checks,midi_compile=report),indent=2))
    print('\n'.join(checks));print(report)

if __name__=='__main__':main()
