"""Extract and reinsert the Interplay, Blizzard and animated title graphics."""
from pathlib import Path
import argparse,hashlib,json,struct
from PIL import Image,ImageDraw
from extract_rnr import ROOT,ROM,decompress,tiles

OUT=ROOT/'intro_png';SHA='b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb'
TABLE=0x6b000
SCENES={
 'interplay':dict(map=25,gfx=26,palette=27),
 'blizzard':dict(map=22,gfx=23,palette=24),
}
TITLE=dict(back_map=46,front_map=221,gfx=47,letters=50,palette=48)
# Final resting positions observed in IntroTitulo.State. Tile ordering is 4x4 column-major.
TITLE_SPRITES=[
 (1088,53,8),(1104,85,8),(1520,117,8),(1120,149,8),(1136,181,8),
 (1280,32,40),(1296,64,40),(1312,96,40),(1328,128,40),(1344,160,40),(1360,192,40),
 (1376,32,72),(1392,64,72),(1408,96,72),(1424,128,72),(1440,160,72),(1456,192,72)]

def resource_info(r,n):
    a,b=struct.unpack_from('>II',r,TABLE+n*4);start=TABLE+(a&0xffffff);end=TABLE+(b&0xffffff)-bool(a&0x20000000)
    return dict(id=n,start=start,end=end,header=r[start:start+2],payload=r[start+2:end],data=decompress(r[start+2:end]))

def colors(pal):
    return [tuple(((w>>s)&7)*255//7 for s in (1,5,9)) for w in struct.unpack('>64H',pal)]
def flat_palette(pal):return [v for c in colors(pal) for v in c]+[0]*(256*3-64*3)

def plane(mapdata,vram,pal):
    im=Image.new('P',(256,224));im.putpalette(flat_palette(pal))
    for ty in range(28):
      for tx in range(32):
        a=struct.unpack_from('>H',mapdata,(ty*32+tx)*2)[0];t=a&2047;line=(a>>13)&3
        for y in range(8):
          sy=7-y if a&0x1000 else y
          for x in range(8):
            sx=7-x if a&0x800 else x;b=vram[t*32+sy*4+sx//2];n=b&15 if sx&1 else b>>4
            im.putpixel((tx*8+x,ty*8+y),line*16+n)
    return im

def composite(back,front):
    out=back.copy()
    for y in range(out.height):
      for x in range(out.width):
        p=front.getpixel((x,y))
        if p&15:out.putpixel((x,y),p)
    return out

def sprite_logo(vram,pal):
    im=Image.new('P',(192,96));im.putpalette(flat_palette(pal));im.info['transparency']=0
    for tile,x,y in TITLE_SPRITES:
      for t in range(16):
        ox=(t//4)*8+x-32;oy=(t%4)*8+y-8
        for yy in range(8):
          for xx in range(4):
            b=vram[(tile+t)*32+yy*4+xx]
            im.putpixel((ox+xx*2,oy+yy),b>>4);im.putpixel((ox+xx*2+1,oy+yy),b&15)
    return im

def paste_logo(screen,logo):
    out=screen.copy()
    for y in range(logo.height):
      for x in range(logo.width):
        p=logo.getpixel((x,y))
        if p&15:out.putpixel((x+32,y+8),p)
    return out

def native_pixels(path,pal):
    source=Image.open(path)
    expected=flat_palette(pal)
    if source.mode=='P' and source.getpalette()[:192]==expected[:192]:
      out=source.copy();out.putpalette(expected)
      return out
    im=source.convert('RGBA');lookup={c:i for i,c in reversed(list(enumerate(colors(pal))))};out=Image.new('P',im.size);out.putpalette(expected)
    for y in range(im.height):
      for x in range(im.width):
        r,g,b,a=im.getpixel((x,y))
        if a<128:out.putpixel((x,y),0)
        elif (r,g,b) in lookup:out.putpixel((x,y),lookup[(r,g,b)])
        else:raise ValueError(f'{path.name}: color {(r,g,b)} at {x},{y} is outside the original 64-color palette')
    return out

def tile_bytes(values):
    out=bytearray()
    for y in range(8):
      for x in range(0,8,2):out.append((values[y][x]&15)<<4|(values[y][x+1]&15))
    return bytes(out)

def encode_plane(im,mapdata,gfx,base_tile,updates):
    count=len(gfx)//32
    for ty in range(28):
      for tx in range(32):
        a=struct.unpack_from('>H',mapdata,(ty*32+tx)*2)[0];tile=a&2047;line=(a>>13)&3
        if not base_tile<=tile<base_tile+count:continue
        px=[[0]*8 for _ in range(8)]
        for y in range(8):
          for x in range(8):
            p=im.getpixel((tx*8+x,ty*8+y))
            if p&15 and p//16!=line:raise ValueError(f'Wrong palette line at tile {tile}, pixel {x},{y}: expected {line}, found {p//16}')
            sx=7-x if a&0x800 else x;sy=7-y if a&0x1000 else y;px[sy][sx]=p&15
        raw=tile_bytes(px)
        if tile in updates and updates[tile]!=raw:raise ValueError(f'Tile {tile} is reused with conflicting edits')
        updates[tile]=raw

def encode_logo(im,gfx,base_tile):
    out=bytearray(gfx)
    for tile,x,y in TITLE_SPRITES:
      for t in range(16):
        px=[[im.getpixel(((t//4)*8+xx+x-32,(t%4)*8+yy+y-8))&15 for xx in range(8)] for yy in range(8)]
        p=(tile-base_tile+t)*32
        if not 0<=p<=len(out)-32:raise ValueError('Title sprite outside resource')
        out[p:p+32]=tile_bytes(px)
    return bytes(out)

def compress(data):
    positions={};matches=[None]*len(data)
    for pos in range(len(data)):
        best_len=0;best_q=0;key=data[pos:pos+3]
        if len(key)==3:
            for q in reversed(positions.get(key,())[-1024:]):
                if pos-q>4096:break
                n=3
                while n<18 and pos+n<len(data) and data[q+n]==data[pos+n]:n+=1
                if n>best_len:best_len,best_q=n,q
                if n==18:break
            if pos<4096 and data[pos]==0:
                n=0
                while n<18 and pos+n<len(data) and data[pos+n]==0:n+=1
                if n>best_len:best_len,best_q=n,pos
            positions.setdefault(key,[]).append(pos)
        if best_len>=3:matches[pos]=(best_len,best_q&4095)
    inf=10**9;n=len(data);dp=[[inf]*8 for _ in range(n+1)];choice=[[None]*8 for _ in range(n)]
    for mod in range(8):dp[n][mod]=0
    for pos in range(n-1,-1,-1):
      for mod in range(8):
        overhead=1 if mod==0 else 0;nm=(mod+1)&7
        dp[pos][mod]=overhead+1+dp[pos+1][nm];choice[pos][mod]=(1,0)
        if matches[pos]:
          maximum,off=matches[pos]
          for take in range(3,maximum+1):
            cost=overhead+2+dp[pos+take][nm]
            if cost<dp[pos][mod]:dp[pos][mod]=cost;choice[pos][mod]=(take,off)
    tokens=[];pos=mod=0
    while pos<n:
        take,off=choice[pos][mod]
        if take==1:tokens.append((True,bytes((data[pos],))))
        else:tokens.append((False,bytes((off&255,((take-3)<<4)|(off>>8)))))
        pos+=take;mod=(mod+1)&7
    out=bytearray()
    for p in range(0,len(tokens),8):
        group=tokens[p:p+8];flags=sum((1<<i) for i,t in enumerate(group) if t[0]);out.append(flags)
        for _,value in group:out.extend(value)
    if decompress(out)!=data:raise AssertionError('Internal compression roundtrip failed')
    return bytes(out)

def patch_resource(rom,info,data):
    comp=compress(data);capacity=info['end']-info['start']-2
    if len(comp)>capacity:raise ValueError(f"Resource {info['id']} needs {len(comp)} compressed bytes; slot allows {capacity}")
    start=info['start'];rom[start:start+2]=len(data).to_bytes(2,'little');rom[start+2:start+2+len(comp)]=comp
    rom[start+2+len(comp):info['end']]=b'\0'*(capacity-len(comp))
    return len(comp),capacity

def export(r):
    OUT.mkdir(exist_ok=True);(OUT/'paletas').mkdir(exist_ok=True);(OUT/'tiles').mkdir(exist_ok=True)
    manifest=[]
    for name,spec in SCENES.items():
        mi,gi,pi=(resource_info(r,spec[k]) for k in ('map','gfx','palette'));v=bytearray(65536);v[0x400:0x400+len(gi['data'])]=gi['data']
        im=plane(mi['data'],v,pi['data']);im.save(OUT/f'{name}_logo.png')
        tiles(gi['data'],flat_palette(pi['data']),16).save(OUT/'tiles'/f'{name}_tiles.png')
        manifest.append(dict(name=name,map_resource=mi['id'],graphics_resource=gi['id'],palette_resource=pi['id'],png=f'{name}_logo.png',native_roundtrip=True))
    bm,fm,gi,li,pi=(resource_info(r,TITLE[k]) for k in ('back_map','front_map','gfx','letters','palette'));v=bytearray(65536);v[0x400:0x400+len(gi['data'])]=gi['data'];v[0x8000:0x8000+len(li['data'])]=li['data']
    back=plane(bm['data'],v,pi['data']);front=plane(fm['data'],v,pi['data']);background=composite(back,front);logo=sprite_logo(v,pi['data'])
    back.save(OUT/'titulo_fondo_capa_trasera.png');front.save(OUT/'titulo_fondo_capa_frontal.png',transparency=0);background.save(OUT/'titulo_fondo.png');logo.save(OUT/'titulo_letras.png',transparency=0);paste_logo(background,logo).save(OUT/'titulo_completo.png')
    tiles(gi['data'],flat_palette(pi['data']),16).save(OUT/'tiles'/'titulo_fondo_tiles.png');tiles(li['data'],flat_palette(pi['data']),16).save(OUT/'tiles'/'titulo_letras_tiles.png')
    for name,pid in [('interplay',27),('blizzard',24),('titulo',48)]:
        pal=resource_info(r,pid)['data'];(OUT/'paletas'/f'{name}.bin').write_bytes(pal)
        (OUT/'paletas'/f'{name}.gpl').write_text('GIMP Palette\nName: '+name+'\nColumns: 16\n#\n'+'\n'.join(f'{a} {b} {c} indice_{i:02d}' for i,(a,b,c) in enumerate(colors(pal))),encoding='ascii')
    (OUT/'manifest.json').write_text(json.dumps(dict(rom_sha256=SHA,format='Indexed PNG; four 16-color CRAM lines',screens=manifest,title=dict(back_map=46,front_map=221,graphics=47,letters=50,palette=48)),indent=2),encoding='utf8')
    print('Exported Interplay, Blizzard, title background layers and animated title letters.')

def import_edits(r,folder,target):
    rom=bytearray(r);report=[]
    for name,spec in SCENES.items():
        mi,gi,pi=(resource_info(r,spec[k]) for k in ('map','gfx','palette'));im=native_pixels(folder/f'{name}_logo.png',pi['data']);updates={};encode_plane(im,mi['data'],gi['data'],0x20,updates);data=bytearray(gi['data'])
        for tile,raw in updates.items():p=(tile-0x20)*32;data[p:p+32]=raw
        if data!=gi['data']:report.append(dict(name=name,resource=gi['id'],compressed=patch_resource(rom,gi,data)))
    bm,fm,gi,li,pi=(resource_info(r,TITLE[k]) for k in ('back_map','front_map','gfx','letters','palette'))
    updates={};back=native_pixels(folder/'titulo_fondo_capa_trasera.png',pi['data']);front=native_pixels(folder/'titulo_fondo_capa_frontal.png',pi['data']);encode_plane(back,bm['data'],gi['data'],0x20,updates);encode_plane(front,fm['data'],gi['data'],0x20,updates);data=bytearray(gi['data'])
    for tile,raw in updates.items():p=(tile-0x20)*32;data[p:p+32]=raw
    if data!=gi['data']:report.append(dict(name='titulo_fondo',resource=gi['id'],compressed=patch_resource(rom,gi,data)))
    logo=native_pixels(folder/'titulo_letras.png',pi['data']);letters=encode_logo(logo,li['data'],0x400)
    if letters!=li['data']:report.append(dict(name='titulo_letras',resource=li['id'],compressed=patch_resource(rom,li,letters)))
    if report:rom[0x18e:0x190]=(sum(struct.unpack('>'+str((len(rom)-512)//2)+'H',rom[512:]))&65535).to_bytes(2,'big')
    if target.exists():raise FileExistsError(target)
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(rom);print(json.dumps(dict(output=str(target),changes=report,identical=bytes(rom)==r)))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--import-dir',type=Path);ap.add_argument('--output-rom',type=Path);args=ap.parse_args();r=ROM.read_bytes()
    if hashlib.sha256(r).hexdigest()!=SHA:raise ValueError('Unexpected source ROM')
    if args.import_dir:
        if not args.output_rom:ap.error('--import-dir requires --output-rom')
        import_edits(r,args.import_dir,args.output_rom)
    else:export(r)

if __name__=='__main__':main()
