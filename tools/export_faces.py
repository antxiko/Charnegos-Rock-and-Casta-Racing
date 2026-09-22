"""Export all driver/rival portraits from the checked European ROM."""
from extract_rnr import ROOT, ROM, decompress, tiles
from PIL import Image, ImageDraw
import struct, json, hashlib

OUT=ROOT/'caras_png'
NAMES=['Snake Sanders','Cyberhawk','Ivanzypher','Katarina Lyons','Jake Badlands','Tarquinn','Olaf',
       'Viper Mackay','Grinder X19','Ragewortt','Roadkill Kelly','Butcher Icebone','J.B. Slash','Rip','Shred']

def resource(r,n):
    a,b=struct.unpack_from('>II',r,0x6b000+n*4)
    start=0x6b000+(a&0xffffff);end=0x6b000+(b&0xffffff)-bool(a&0x20000000)
    return decompress(r[start+2:end]),start,end

def positions():
    for t in range(64):
        block,j=divmod(t,16)
        yield block%2*32+j//4*8,block//2*32+j%4*8

def encode(im):
    data=bytearray()
    for tx,ty in positions():
        for y in range(8):
            for x in range(4):data.append(im.getpixel((tx+x*2,ty+y))*16+im.getpixel((tx+x*2+1,ty+y)))
    return bytes(data)

def main():
    r=ROM.read_bytes();sha=hashlib.sha256(r).hexdigest()
    assert sha=='b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb'
    OUT.mkdir(exist_ok=True);pd=OUT/'paletas';pd.mkdir(exist_ok=True)
    v=(OUT/'captura/VRAM.bin').read_bytes();cr=(OUT/'captura/CRAM.bin').read_bytes()
    records=[];overview=Image.new('RGB',(5*180,3*170),'#303040');draw=ImageDraw.Draw(overview)
    for i,name in enumerate(NAMES):
        gfx=78+i if i<7 else 92+min(i-7,6)
        pid=85+i if i<7 else 99+i-7
        data,offset,end=resource(r,gfx);pal,po,pe=resource(r,pid)
        assert len(data)==2048 and len(pal)==32
        words=struct.unpack('>16H',pal)
        colors=[tuple(((w>>s)&7)*255//7 for s in (1,5,9)) for w in words]
        rgb=[c for color in colors for c in color]+[0]*720
        strip=tiles(data,rgb,64);im=Image.new('P',(64,64));im.putpalette(rgb)
        for t,xy in enumerate(positions()):im.paste(strip.crop((t*8,0,t*8+8,8)),xy)
        slug=f'{i+1:02d}_'+name.lower().replace(' ','_').replace('.','')
        file=OUT/(slug+'.png');im.save(file,transparency=0)
        assert encode(Image.open(file))==data
        (pd/(slug+'.bin')).write_bytes(pal)
        (pd/(slug+'.gpl')).write_text('GIMP Palette\nName: '+name+'\nColumns: 16\n#\n'+'\n'.join(f'{a} {b} {c} indice_{j:02d}' for j,(a,b,c) in enumerate(colors)))
        sw=Image.new('RGB',(512,48),'#303040');sd=ImageDraw.Draw(sw)
        for j,c in enumerate(colors):sd.rectangle((j*32,0,j*32+31,27),fill=c);sd.text((j*32,30),str(j),fill='white')
        sw.save(pd/(slug+'.png'))
        address=v.find(data);line=cr.find(pal)
        verified=False
        if address>=0 and line>=0 and line%32==0:
            # Check the actual SAT layout independently for these three visible faces.
            sat={0x8000:0xf000,0x8800:0xf020,0x9000:0xf040}[address]
            parts=[struct.unpack_from('>4H',v,sat+j*8) for j in range(4)]
            x0,y0=parts[0][3],parts[0][0]
            for j,(y,sz,attr,x) in enumerate(parts):
                assert sz>>8==15 and attr&0x1800==0
                assert attr&2047==address//32+j*16
                assert attr>>13&3==line//32
                assert (x-x0,y-y0)==(j%2*32,j//2*32)
            verified=True
        x=i%5*180;y=i//5*170
        draw.text((x+4,y+4),f'{i+1:02d} {name}',fill='white')
        big=im.convert('RGBA').resize((128,128),Image.Resampling.NEAREST);overview.paste(big,(x+24,y+25),big)
        records.append(dict(name=name,png=file.name,graphics_id=gfx,palette_id=pid,graphics_rom_offset=hex(offset),graphics_rom_end=hex(end),palette_rom_offset=hex(po),palette_rom_end=hex(pe),native_roundtrip=True,verified_in_supplied_state=verified,vram_offset=hex(address) if verified else None,palette_line=line//32 if verified else None))
    overview.save(OUT/'TODAS_LAS_CARAS.png')
    assert sum(row['verified_in_supplied_state'] for row in records)==3
    (OUT/'manifest.json').write_text(json.dumps(dict(rom_sha256=sha,dimensions=[64,64],layout='Four 32x32 sprites, row-major blocks, column-major tiles',portraits=records),indent=2))
    print('15 portraits, 14 unique graphics, 15 palettes. 15/15 native roundtrips; 3/3 live VRAM+CRAM+SAT matches.')

if __name__=='__main__':main()
