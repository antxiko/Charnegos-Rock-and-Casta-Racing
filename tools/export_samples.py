"""Extract Sound Images PCM and optionally reinsert same-length edited WAVs."""
from pathlib import Path
import argparse, hashlib, json, wave, csv, html

ROOT=Path(__file__).resolve().parents[1]
ROM=ROOT/"Rock 'n' Roll Racing (Europe).md"
OUT=ROOT/'samples_wav'
SHA='b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb'
RATE=7778  # nominal PAL Z80 / (16*22+104); bus stalls/bank switches not included

def entries(r):
    base=0x20000
    table=base+(int.from_bytes(r[base:base+2],'big')&0x7fff)
    count=int.from_bytes(r[table:table+2],'big')
    assert count==42
    for i in range(count):
        p=table+2+i*12;record=r[p:p+12]
        start=base+int.from_bytes(record[1:4],'big');size=int.from_bytes(record[4:6],'big')
        assert size>0 and start+size<=len(r)
        yield dict(id=i+1,table_entry=hex(p),rom_offset=hex(start),bytes=size,wav=f'sample_{i+1:02d}.wav',duration_seconds=round(size/RATE,6),placeholder=size==4)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--import-dir',type=Path,help='Folder of edited sample_XX.wav files')
    ap.add_argument('--output-rom',type=Path,help='New ROM path; never overwrite an existing file')
    args=ap.parse_args()
    r=ROM.read_bytes();assert hashlib.sha256(r).hexdigest()==SHA,'Unexpected source ROM'
    items=list(entries(r));OUT.mkdir(exist_ok=True)
    if args.import_dir:
        if not args.output_rom:ap.error('--output-rom is required with --import-dir')
        result=bytearray(r);changed=[]
        for row in items:
            file=args.import_dir/row['wav']
            if not file.exists():continue
            with wave.open(str(file),'rb') as w:
                if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes(),w.getcomptype())!=(1,1,RATE,row['bytes'],'NONE'):
                    raise ValueError(f'{file.name}: requires mono unsigned 8-bit PCM, {RATE} Hz, exactly {row["bytes"]} samples')
                data=w.readframes(w.getnframes())
            assert len(data)==row['bytes']
            start=int(row['rom_offset'],16)
            if result[start:start+len(data)]!=data:changed.append(row['id'])
            result[start:start+len(data)]=data
        # Sega header checksum changes only when actual audio bytes change.
        if changed:
            checksum=sum(int.from_bytes(result[p:p+2],'big') for p in range(0x200,len(result),2))&65535
            result[0x18e:0x190]=checksum.to_bytes(2,'big')
        with args.output_rom.open('xb') as f:f.write(result)
        print(json.dumps(dict(output=str(args.output_rom),changed_sample_ids=changed,byte_identical_to_original=bytes(result)==r)))
        return
    if args.output_rom:ap.error('--output-rom requires --import-dir')
    for row in items:
        start=int(row['rom_offset'],16);data=r[start:start+row['bytes']]
        with wave.open(str(OUT/row['wav']),'wb') as w:
            w.setnchannels(1);w.setsampwidth(1);w.setframerate(RATE);w.writeframes(data)
        with wave.open(str(OUT/row['wav']),'rb') as w:assert w.readframes(w.getnframes())==data
        row['sha256_pcm']=hashlib.sha256(data).hexdigest()
    with (OUT/'catalogo.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(items[0]));writer.writeheader();writer.writerows(items)
    (OUT/'manifest.json').write_text(json.dumps(dict(rom_sha256=SHA,format='unsigned 8-bit mono PCM',nominal_sample_rate=RATE,rate_note='Nominal PAL loop timing; does not reproduce bus stalls or bank switching delays',samples=items),indent=2))
    rows=''.join(f'<tr><td>{x["id"]:02d}</td><td>{x["duration_seconds"]:.3f} s</td><td>{"Entrada de 4 bytes" if x["placeholder"] else "Escuchar para identificar"}</td><td><audio controls preload="none" src="{html.escape(x["wav"])}"></audio></td><td><a href="{x["wav"]}" download>WAV</a></td></tr>' for x in items)
    (OUT/'ESCUCHAR.html').write_text('<!doctype html><meta charset="utf-8"><title>Samples Rock n Roll Racing</title><style>body{background:#18202a;color:#eee;font:16px system-ui;margin:32px}td{padding:9px}a{color:#8cf}audio{height:34px}</style><h1>Samples de Rock n Roll Racing</h1><p>42 entradas originales. WAV mono de 8 bits, frecuencia nominal 7778 Hz. Seis entradas tienen solo 4 bytes. Los nombres de las frases están pendientes de identificación al escuchar.</p><table><tr><th>ID</th><th>Duración</th><th>Nota</th><th>Reproducir</th><th>Archivo</th></tr>'+rows+'</table>',encoding='utf-8')
    print('42 WAV exported and byte-verified; 36 substantial clips + 6 four-byte entries.')

if __name__=='__main__':main()
