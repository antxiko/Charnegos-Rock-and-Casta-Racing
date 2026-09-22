"""Extract and reinsert every editable text string from the European ROM."""
from pathlib import Path
import argparse, hashlib, json, re, struct
from export_intro import resource_info, patch_resource

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
POINTER_TABLE=(0x37ce,0x398c)
TEXT_BASE_PATCH=0x3664
RELOCATED_BASE=0x65000
RELOCATED_END=0x6b000
SPANISH={'Ñ':0x40,'ñ':0x40,'Á':0x5b,'á':0x5b,'É':0x5c,'é':0x5c,
         'Í':0x5d,'í':0x5d,'Ó':0x5e,'ó':0x5e,'Ú':0x5f,'ú':0x5f}

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

def encode(row,limit=None):
    data=bytearray()
    for char in row['text'].replace('\r\n','\n').replace('\r','\n'):
        if char=='\n':data.append(13)
        elif char in SPANISH:data.append(SPANISH[char])
        elif 32<=ord(char)<=126:data.append(ord(char))
        else:raise ValueError(f"{row['id']}: caracter no soportado {char!r}")
    data=bytes(data);lines=data.split(b'\r');limits=row.get('max_line_chars',row['line_widths'])
    if len(lines)!=len(limits):raise ValueError(f"{row['id']}: necesita {len(limits)} linea(s), hay {len(lines)}")
    for i,(line,width) in enumerate(zip(lines,limits),1):
        if len(line)>width:raise ValueError(f"{row['id']}: linea {i} tiene {len(line)} caracteres; maximo {width}")
    if limit is not None and len(data)>limit:raise ValueError(f"{row['id']}: {len(data)} bytes; maximo fijo {limit}")
    return data

def spanish_font(raw):
    out=bytearray(raw)
    def pixels(tile):
        block=raw[tile*32:(tile+1)*32]
        return [[(block[y*4+x//2]>>(0 if x&1 else 4))&15 for x in range(8)] for y in range(8)]
    def packed(px):return bytes((px[y][x]<<4)|px[y][x+1] for y in range(8) for x in range(0,8,2))
    for code,source,tilde in ((0x40,'N',True),(0x5b,'A',False),(0x5c,'E',False),(0x5d,'I',False),(0x5e,'O',False),(0x5f,'U',False)):
        px=[[0]*8]+pixels(ord(source)-0x20)[:7]
        if tilde:px[0][2:6]=[5,5,0,5]
        else:px[0][3:5]=[5,5]
        out[(code-0x20)*32:(code-0x1f)*32]=packed(px)
    return bytes(out)

def apply_spanish_font(rom,source):
    for rid in (0,1):
        info=resource_info(source,rid);patch_resource(rom,info,spanish_font(info['data']))

def relocate(result,source,original,edited):
    if source[TEXT_BASE_PATCH:TEXT_BASE_PATCH+4]!=MAIN_START.to_bytes(4,'big'):raise ValueError('Base original del banco no encontrada')
    main=[x for x in original if MAIN_START<=x['offset']<MAIN_END];blob=bytearray();new={}
    for native in main:
        new[native['offset']]=RELOCATED_BASE+len(blob);blob.extend(encode(edited[native['id']]));blob.append(0)
    if len(blob)>RELOCATED_END-RELOCATED_BASE:raise ValueError('El banco recolocado supera los 24576 bytes libres de la ROM')
    if any(source[RELOCATED_BASE:RELOCATED_END]):raise ValueError('La zona interna reservada para textos no esta vacia')
    result[RELOCATED_BASE:RELOCATED_END]=b'\0'*(RELOCATED_END-RELOCATED_BASE)
    result[RELOCATED_BASE:RELOCATED_BASE+len(blob)]=blob
    result[TEXT_BASE_PATCH:TEXT_BASE_PATCH+4]=RELOCATED_BASE.to_bytes(4,'big')
    for p in range(POINTER_TABLE[0],POINTER_TABLE[1],2):
        old=MAIN_START+int.from_bytes(source[p:p+2],'big')
        if old in new:result[p:p+2]=(new[old]-RELOCATED_BASE).to_bytes(2,'big')
    return len(blob)

def checksum(rom):return sum(struct.unpack('>'+str((len(rom)-0x200)//2)+'H',rom[0x200:]))&0xffff

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--import-file',type=Path,help='Edited textos.json')
    ap.add_argument('--output-rom',type=Path,help='New ROM; existing files are never overwritten')
    args=ap.parse_args();r=ROM.read_bytes()
    if hashlib.sha256(r).hexdigest()!=SHA:raise ValueError('Unexpected source ROM; European 1 MiB ROM required')
    original=entries(r)
    section_limits={name:max(max(x['line_widths']) for x in original if x['section']==name) for _,name in SECTIONS}
    for row in original:row['max_line_chars']=[section_limits[row['section']]]*len(row['line_widths'])
    if not args.import_file:
        OUT.mkdir(exist_ok=True)
        doc=dict(format='Charnego Rock & Casta text v2',rom_sha256=SHA,
                 encoding='ASCII + Ñ ñ Á á É é Í í Ó ó Ú ú; LF becomes 0x0D',strings=original)
        (OUT/'textos.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
        editable=[]
        for row in original:
            editable.append(f"[{row['id']}] section={row['section']} offset=0x{row['offset']:06X} max_line={row['max_line_chars'][0]}")
            editable.append(row['text']);editable.append('')
        (OUT/'textos_lectura.txt').write_text('\n'.join(editable),encoding='utf-8')
        print(json.dumps(dict(strings=len(original),output=str(OUT/'textos.json'))))
        return
    if not args.output_rom:ap.error('--import-file requires --output-rom')
    doc=json.loads(args.import_file.read_text(encoding='utf-8'));edited=doc.get('strings')
    if not isinstance(edited,list):raise ValueError('Invalid strings list')
    by_id={x['id']:x for x in edited};expected={x['id'] for x in original}
    if set(by_id)!=expected:raise ValueError('String IDs differ from the original catalog')
    result=bytearray(r);changed=[];needs_relocation=False
    for native in original:
        row=by_id[native['id']]
        for key in ('offset','max_bytes','line_widths','max_line_chars','original_hex'):
            if row.get(key)!=native[key]:raise ValueError(f"{native['id']}: protected field {key} changed")
        data=encode(row);start=native['offset'];size=native['max_bytes']
        if start<MAIN_END and len(data)>size:needs_relocation=True
        elif start>=MAIN_END and len(data)>size:raise ValueError(f"{native['id']}: texto de sistema no recolocable")
        if data!=bytes.fromhex(native['original_hex']):changed.append(native['id'])
    if needs_relocation:bank_size=relocate(result,r,original,by_id)
    else:
        bank_size=MAIN_END-MAIN_START
        for native in original:
            data=encode(by_id[native['id']],native['max_bytes']);result[native['offset']:native['offset']+native['max_bytes']+1]=data+b'\0'*(native['max_bytes']+1-len(data))
    if needs_relocation:
        for native in original:
            if native['offset']>=MAIN_END:
                data=encode(by_id[native['id']],native['max_bytes']);result[native['offset']:native['offset']+native['max_bytes']+1]=data+b'\0'*(native['max_bytes']+1-len(data))
    if any(any(c in row['text'] for c in SPANISH) for row in edited):apply_spanish_font(result,r)
    if changed:result[0x18e:0x190]=checksum(result).to_bytes(2,'big')
    if args.output_rom.exists():raise FileExistsError(f'Output already exists: {args.output_rom}')
    args.output_rom.parent.mkdir(parents=True,exist_ok=True);args.output_rom.write_bytes(result)
    print(json.dumps(dict(output=str(args.output_rom),changed=len(changed),changed_ids=changed,relocated=needs_relocation,text_bank_bytes=bank_size,
                          identical_to_original=bytes(result)==r,sha256=hashlib.sha256(result).hexdigest()),ensure_ascii=False))

if __name__=='__main__':main()
