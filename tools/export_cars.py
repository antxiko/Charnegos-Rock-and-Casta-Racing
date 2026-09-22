"""Export native 48x48 race sprites and the ROM's ten base car palettes."""
from extract_rnr import ROM, ROOT
from PIL import Image, ImageDraw
import json, struct, hashlib

OUT=ROOT/'coches_png'
BASE=0xbf500
STRIDE=0x480
PALBASE=0x6776

def palette(r, n):
    words=struct.unpack_from('>16H',r,PALBASE+n*32)
    rgb=[tuple(((w>>s)&7)*255//7 for s in (1,5,9)) for w in words]
    return words,rgb,[v for color in rgb for v in color]+[0]*720

def coordinates():
    # Two 24-pixel-high bands; tiles advance vertically inside each band.
    for by in range(0,6,3):
        for bx in range(0,6,2):
            for x in range(2):
                for y in range(3): yield (bx+x)*8,(by+y)*8

def frame(data,pal):
    im=Image.new('P',(48,48));im.putpalette(pal)
    for t,(tx,ty) in enumerate(coordinates()):
        for y in range(8):
            for x in range(4):
                v=data[t*32+y*4+x]
                im.putpixel((tx+x*2,ty+y),v>>4)
                im.putpixel((tx+x*2+1,ty+y),v&15)
    im.info['transparency']=0
    return im

def encode(im):
    out=bytearray()
    for tx,ty in coordinates():
        for y in range(8):
            for x in range(4):out.append((im.getpixel((tx+x*2,ty+y))<<4)|im.getpixel((tx+x*2+1,ty+y)))
    return bytes(out)

def main():
    r=ROM.read_bytes(); assert hashlib.sha256(r).hexdigest()=='b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb'
    OUT.mkdir(exist_ok=True)
    pals=[]
    for p in range(10):
        words,rgb,pal=palette(r,p);pals.append(pal)
        (OUT/f'paleta_{p:02d}.bin').write_bytes(r[PALBASE+p*32:PALBASE+(p+1)*32])
        (OUT/f'paleta_{p:02d}.gpl').write_text('GIMP Palette\nName: RnR '+str(p)+'\nColumns: 16\n#\n'+'\n'.join(f'{a} {b} {c} indice_{i:02d}' for i,(a,b,c) in enumerate(rgb)))
        sw=Image.new('RGB',(512,48));d=ImageDraw.Draw(sw)
        for i,c in enumerate(rgb):d.rectangle((i*32,0,i*32+31,27),fill=c);d.text((i*32,30),str(i),fill='white')
        sw.save(OUT/f'paleta_{p:02d}.png')
    overview=Image.new('RGB',(10*100,5*116),'#303040');draw=ImageDraw.Draw(overview)
    records=[]
    for car in range(5):
        folder=OUT/f'coche_{car+1:02d}';folder.mkdir(exist_ok=True)
        for p,pal in enumerate(pals):
            sheet=Image.new('P',(9*48,5*48));sheet.putpalette(pal)
            for f in range(45):
                offset=BASE+(car*45+f)*STRIDE;data=r[offset:offset+STRIDE]
                im=frame(data,pal)
                assert encode(im)==data
                sheet.paste(im,(f%9*48,f//9*48))
                if p==0:
                    file=folder/f'vista_{f:02d}.png';im.save(file,transparency=0)
                    assert encode(Image.open(file))==data
                    records.append(dict(car=car+1,frame=f,rom_offset=hex(offset),bytes=STRIDE,file=str(file.relative_to(OUT))))
            sheet.save(folder/f'hoja_paleta_{p:02d}.png',transparency=0)
            sample=frame(r[BASE+(car*45+5)*STRIDE:BASE+(car*45+6)*STRIDE],pal)
            overview.paste(sample.convert('RGBA').resize((96,96),Image.Resampling.NEAREST),(p*100,car*116+18),sample.convert('RGBA').resize((96,96),Image.Resampling.NEAREST))
            draw.text((p*100+2,car*116+2),f'C{car+1} P{p:02d}',fill='white')
    overview.save(OUT/'VISTA_GENERAL.png')
    (OUT/'manifest.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256(r).hexdigest(),palette_offset=hex(PALBASE),layout='Two 48x24 bands, column-major tiles within each band',frames=records),indent=2))
    print('225 frames, 50 palette sheets, 10 palettes. PNG -> native bytes: 225/225 identical.')

if __name__=='__main__':main()
