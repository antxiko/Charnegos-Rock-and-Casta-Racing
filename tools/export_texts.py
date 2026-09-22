"""Extract and reinsert every editable text string from the European ROM."""
from pathlib import Path
import argparse, hashlib, json, re, struct

ROOT=Path(__file__).resolve().parents[1]
ROM=ROOT/"Rock 'n' Roll Racing (Europe).md"
OUT=ROOT/'textos'
SHA='b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb'
MAIN_START,MAIN_END=0x398c,0x4bea
SKIP=((0x4608,0x462e),)  # Password/font glyph lookup, not language text.
EXTRA=((0x481,0x49c,'system'),(0x4a1,0x4a9,'system'),
       (0x4ab,0x4ba,'system'),(0x4bc,0x4c8,'system'),(0x4ca,0x4e9,'system'))
SECTIONS=((0x398c,'status'),(0x39f4,'pilots'),(0x3c01,'planets'),
          (0x3e43,'menus'),(0x3eb4,'shop'),(0x42b8,'score'),
          (0x42f1,'planet_names'),(0x4321,'garage'),(0x43c5,'equipment'),
          (0x4485,'password'),(0x44c8,'options'),(0x4503,'league_and_names'),
          (0x45c8,'results'),(0x4658,'ending'),(0x4960,'credits'),
          (0x4bc1,'system'))

def section_for(offset):
    return max((name for start,name in SECTIONS if start<=offset),default='misc',key=lambda name:next(start for start,n in SECTIONS if n==name))

def valid(data):return bool(data) and all(b==13 or 32<=b<=126 for b in data)
def skipped(start,end):return any(start<a1 and end>a0 for a0,a1 in SKIP)
def slug(data):
    text=data.replace(b'\r',b' ').decode('ascii','replace').strip()
    text=re.sub(r'[^A-Z0-9]+','_',text.upper()).strip('_')[:28]
    return text or 'BLANK'

def entries(r):
    rows=[];p=MAIN_START
    while p<MAIN_END:
        if r[p]==0:p+=1;continue
        end=r.find(b'\0',p,MAIN_END+1)
        if end<0:raise ValueError('Unterminated main text bank')
        raw=r[p:end]
        if valid(raw) and not skipped(p,end):rows.append(make_row(p,end,raw,section_for(p)))
        p=end+1
    for start,end,section in EXTRA:
        raw=r[start:end]
        if not valid(raw) or r[end]!=0:raise ValueError(f'Invalid extra string at {start:x}')
        rows.append(make_row(start,end,raw,section))
    rows.sort(key=lambda x:x['offset'])
    used={}
    for row in rows:
        base=f"{row['offset']:06X}_{slug(bytes.fromhex(row['original_hex']))}"
        used[base]=used.get(base,0)+1;row['id']=base if used[base]==1 else f'{base}_{used[base]}'
    return rows

def make_row(start,end,raw,section):
    lines=raw.split(b'\r')
    return dict(id='',section=section,offset=start,max_bytes=end-start,
                line_widths=[len(x) for x in lines],text=raw.replace(b'\r',b'\n').decode('ascii'),
                original_hex=raw.hex())

def encode(row):
    text=row['text']
    try:data=text.replace('\r\n','\n').replace('\r','\n').encode('ascii').replace(b'\n',b'\r')
    except UnicodeEncodeError as e:raise ValueError(f"{row['id']}: only ASCII is supported; use N instead of Ñ and omit accents") from e
    lines=data.split(b'\r');widths=row['line_widths']
    if len(lines)!=len(widths):raise ValueError(f"{row['id']}: requires {len(widths)} line(s), found {len(lines)}")
    for i,(line,width) in enumerate(zip(lines,widths),1):
        if len(line)>width:raise ValueError(f"{row['id']}: line {i} has {len(line)} chars; maximum {width}")
    if len(data)>row['max_bytes']:raise ValueError(f"{row['id']}: {len(data)} bytes; maximum {row['max_bytes']}")
    if any(b<32 or b>126 for b in data.replace(b'\r',b'')):raise ValueError(f"{row['id']}: unsupported control character")
    return data

def checksum(rom):return sum(struct.unpack('>'+str((len(rom)-0x200)//2)+'H',rom[0x200:]))&0xffff

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--import-file',type=Path,help='Edited textos.json')
    ap.add_argument('--output-rom',type=Path,help='New ROM; existing files are never overwritten')
    args=ap.parse_args();r=ROM.read_bytes()
    if hashlib.sha256(r).hexdigest()!=SHA:raise ValueError('Unexpected source ROM; European 1 MiB ROM required')
    original=entries(r)
    if not args.import_file:
        OUT.mkdir(exist_ok=True)
        doc=dict(format='Charnego Rock & Casta text v1',rom_sha256=SHA,
                 encoding='ASCII; LF in JSON becomes 0x0D in ROM',strings=original)
        (OUT/'textos.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
        editable=[]
        for row in original:
            editable.append(f"[{row['id']}] section={row['section']} offset=0x{row['offset']:06X} max={row['max_bytes']}")
            editable.append(row['text']);editable.append('')
        (OUT/'textos_lectura.txt').write_text('\n'.join(editable),encoding='utf-8')
        print(json.dumps(dict(strings=len(original),output=str(OUT/'textos.json'))))
        return
    if not args.output_rom:ap.error('--import-file requires --output-rom')
    doc=json.loads(args.import_file.read_text(encoding='utf-8'));edited=doc.get('strings')
    if not isinstance(edited,list):raise ValueError('Invalid strings list')
    by_id={x['id']:x for x in edited};expected={x['id'] for x in original}
    if set(by_id)!=expected:raise ValueError('String IDs differ from the original catalog')
    result=bytearray(r);changed=[]
    for native in original:
        row=by_id[native['id']]
        for key in ('offset','max_bytes','line_widths','original_hex'):
            if row.get(key)!=native[key]:raise ValueError(f"{native['id']}: protected field {key} changed")
        data=encode(row);start=native['offset'];size=native['max_bytes']
        result[start:start+size+1]=data+b'\0'*(size+1-len(data))
        if data!=bytes.fromhex(native['original_hex']):changed.append(native['id'])
    if changed:result[0x18e:0x190]=checksum(result).to_bytes(2,'big')
    if args.output_rom.exists():raise FileExistsError(f'Output already exists: {args.output_rom}')
    args.output_rom.parent.mkdir(parents=True,exist_ok=True);args.output_rom.write_bytes(result)
    print(json.dumps(dict(output=str(args.output_rom),changed=len(changed),changed_ids=changed,
                          identical_to_original=bytes(result)==r,sha256=hashlib.sha256(result).hexdigest()),ensure_ascii=False))

if __name__=='__main__':main()
