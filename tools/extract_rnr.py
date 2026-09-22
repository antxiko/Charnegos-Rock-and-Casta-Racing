"""Read-only Rock n Roll Racing (Europe) asset extraction. Requires Pillow."""
from pathlib import Path
import hashlib, json, struct
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "Rock 'n' Roll Racing (Europe).md"
OUT = ROOT / 'extracted'

def decompress(src):
    ring = bytearray(4096)
    out = bytearray()
    pos = cursor = 0
    while pos < len(src):
        flags = src[pos]; pos += 1
        for bit in range(8):
            if pos == len(src): return bytes(out)
            if flags & (1 << bit):
                values = [src[pos]]; pos += 1
                for value in values:
                    out.append(value); ring[cursor] = value; cursor = (cursor+1)&4095
            else:
                if pos+2 > len(src): raise ValueError('Truncated reference')
                a,b = src[pos:pos+2]; pos += 2
                offset = a | ((b&15)<<8)
                for k in range((b>>4)+3):
                    value = ring[(offset+k)&4095]
                    out.append(value); ring[cursor] = value; cursor = (cursor+1)&4095
    return bytes(out)

def tiles(data, palette=None, columns=16):
    count = len(data)//32
    im = Image.new('P', (columns*8, max(8, ((count+columns-1)//columns)*8)))
    im.putpalette(palette or [v for i in range(256) for v in (i*17 if i<16 else 0,)*3])
    for t in range(count):
        for y in range(8):
            for x in range(4):
                v=data[t*32+y*4+x]
                im.putpixel(((t%columns)*8+x*2,(t//columns)*8+y),v>>4)
                im.putpixel(((t%columns)*8+x*2+1,(t//columns)*8+y),v&15)
    return im

def main():
    r=ROM.read_bytes()
    assert hashlib.sha256(r).hexdigest()=='b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb', 'Unsupported ROM'
    OUT.mkdir(exist_ok=True)
    base=0x6b000
    n=(struct.unpack_from('>I',r,base)[0]&0xffffff)//4-1
    records=[]; previews=[]
    for i in range(n):
        v,w=struct.unpack_from('>II',r,base+i*4)
        start=base+(v&0xffffff); end=base+(w&0xffffff)-(1 if v&0x20000000 else 0)
        raw=r[start:end]
        try: data=decompress(raw[2:])
        except ValueError as e:
            print(i,e); continue
        name=f'{i:03d}_{start:06X}'
        (OUT/(name+'.bin')).write_bytes(data)
        im=tiles(data); im.save(OUT/(name+'_tiles_gray.png'))
        thumb=im.convert('RGB'); thumb.thumbnail((128,192))
        previews.append((name,len(data),thumb))
        records.append(dict(id=i,offset=hex(start),end=hex(end),header=raw[:2].hex(),decompressed_bytes=len(data),file=name))
    for page in range((len(previews)+47)//48):
        sheet=Image.new('RGB',(8*144,6*224),'#303040'); draw=ImageDraw.Draw(sheet)
        for j,(name,size,im) in enumerate(previews[page*48:(page+1)*48]):
            x=j%8*144;y=j//8*224
            draw.text((x+2,y+2),f'{name}\n{size} bytes',fill='white'); sheet.paste(im,(x,y+30))
        sheet.save(OUT/f'contact_{page}.png')
    (OUT/'manifest.json').write_text(json.dumps(records,indent=2))
    print('Extracted',len(records),'assets')

if __name__=='__main__': main()
