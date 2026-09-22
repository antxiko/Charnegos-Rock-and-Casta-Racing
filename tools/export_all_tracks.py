"""Execute the ROM's pure 68000 map builder and export all 72 track designs."""
from pathlib import Path
import struct, json, base64, zlib, hashlib, csv
import numpy as np
from PIL import Image, ImageDraw
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
from unicorn.m68k_const import *
from export_faces import resource, ROOT, ROM

OUT=ROOT/'todos_los_circuitos'
NAMES=['CHEM VI','DRAKONIS','BOGMIRE','NEW MOJAVE','NHO','INFERNO']
W,H=384,115

def pointer(r,n):return 0x6b000+(int.from_bytes(r[0x6b000+n*4:0x6b004+n*4],'big')&0xffffff)

def build(r,initial,track,world):
    u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    u.mem_map(0,0x110000);u.mem_write(0,r);u.mem_map(0xff0000,65536);u.mem_write(0xff0000,initial)
    u.reg_write(UC_M68K_REG_SR,0x2700);u.reg_write(UC_M68K_REG_A4,0xff8000)
    def run(pc):
        u.reg_write(UC_M68K_REG_A7,0xfffefc);u.mem_write(0xfffefc,(0x100).to_bytes(4,'big'))
        u.emu_start(pc,0x100,count=5000000)
        assert u.reg_read(UC_M68K_REG_PC)==0x100,f'Builder did not return: {pc:X}'
    definition,_,_=resource(r,106+track)
    u.mem_write(0x100000,definition);u.reg_write(UC_M68K_REG_A0,0x100000);run(0xbbe0)
    u.mem_write(0xff0444,r[0xbba2+world:0xbba3+world])
    lookupid=struct.unpack_from('>H',r,0xbbb4+world*2)[0]
    dictid=struct.unpack_from('>H',r,0xbba8+world*2)[0]
    u.mem_write(0xff0450,pointer(r,lookupid).to_bytes(4,'big')+pointer(r,dictid).to_bytes(4,'big'))
    run(0x1a400);run(0xa14c)
    ram=bytes(u.mem_read(0xff0000,65536));maps=[];refs=[]
    for start in (0x458,0x5a98):
        ref=np.frombuffer(ram[start:start+22080],dtype='>u2').reshape(H,96).copy()
        m=np.empty((H,W),np.uint16)
        for key in np.unique(ref&0x7ff8):
            k=int(key);data=ram if k&0x4000 else r
            off=0xb0d8+(k&0x3ff8) if k&0x4000 else pointer(r,dictid)+k
            vals=struct.unpack_from('>4H',data,off)
            m.reshape(H,96,4)[(ref&0x7ff8)==key]=vals
        maps.append(m);refs.append(ref)
    return maps,refs,definition,ram

def tile_pixels(raw):
    b=np.frombuffer(raw,dtype=np.uint8).reshape(-1,8,4);a=np.zeros((len(b),8,8),np.uint8)
    a[:,:,::2]=b>>4;a[:,:,1::2]=b&15;return a

def main():
    r=ROM.read_bytes();initial=(ROOT/'circuitos_png/captura/RAM.bin').read_bytes()
    assert hashlib.sha256(r).hexdigest()=='b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb'
    OUT.mkdir(exist_ok=True);(OUT/'mapas').mkdir(exist_ok=True)
    # Derive world membership from the game's championship schedule, not resource order.
    worlds={}
    starts=r[0x17fe:0x180a];schedule=r[0x180a:0x189a]
    for world in range(6):
        lo=starts[world*2];hi=starts[world*2+2] if world<5 else len(schedule)
        for track in schedule[lo:hi]:
            assert track not in worlds or worlds[track]==world
            worlds[track]=world
    assert set(worlds)==set(range(1,73))
    themes=[];catalog=[];used_by_world=[set() for _ in range(6)]
    for world,name in enumerate(NAMES):
        folder=OUT/'bancos'/f'{world:02d}';folder.mkdir(parents=True,exist_ok=True)
        gid=struct.unpack_from('>H',r,0xbbcc+world*2)[0];pid=struct.unpack_from('>H',r,0xbbc0+world*2)[0]
        bank,off,end=resource(r,gid);pal,_,_=resource(r,pid);aux,_,_=resource(r,189)
        pix=np.zeros((2048,8,8),np.uint8);pix[1:len(bank)//32+1]=tile_pixels(bank);pix[1015:1023]=tile_pixels(aux)
        # Player palettes are shared transient slots; background slots come from this world.
        pal=(ROOT/'circuitos_png/captura/CRAM.bin').read_bytes()[:64]+pal[64:]
        colors=np.array([tuple(((v>>s)&7)*255//7 for s in (1,5,9)) for v in struct.unpack('>64H',pal)],np.uint8)
        rgba=np.empty((4,2048,8,8,4),np.uint8)
        for p in range(4):
            rgba[p,:,:,:,:3]=colors[p*16+pix];rgba[p,:,:,:,3]=np.where(pix==0,0,255)
            atlas=rgba[p].reshape(64,32,8,8,4).transpose(0,2,1,3,4).reshape(512,256,4)
            Image.fromarray(atlas).save(folder/f'paleta_{p}_tileset.png')
            (folder/f'paleta_{p}.bin').write_bytes(pal[p*32:p*32+32])
            (folder/f'paleta_{p}.gpl').write_text('GIMP Palette\nName: '+name+'\nColumns: 16\n#\n'+'\n'.join(f'{a} {b} {c} indice_{j}' for j,(a,b,c) in enumerate(colors[p*16:p*16+16])))
            tsx=f'<tileset version="1.10" name="{name} paleta {p}" tilewidth="8" tileheight="8" tilecount="2048" columns="32"><image source="paleta_{p}_tileset.png" width="256" height="512"/></tileset>'
            (folder/f'paleta_{p}.tsx').write_text(tsx)
        themes.append(dict(name=name,id=world,resource_id=gid,rom_offset=hex(off),rom_end=hex(end),tiles=len(bank)//32,pix=pix,rgba=rgba,colors=colors,folder=folder))

    for track in range(1,73):
        world=worlds[track];theme=themes[world];maps,refs,definition,ram=build(r,initial,track,world)
        folder=OUT/'mapas'/f'{track:02d}';folder.mkdir(exist_ok=True)
        (folder/'definicion_original.bin').write_bytes(definition)
        (folder/'mapas_generados.bin').write_bytes(b''.join(m.astype('>u2').tobytes() for m in maps))
        layers=[]
        for plane,m in enumerate(maps):
            used_by_world[world].update((int(x)&2047,(int(x)>>13)&3) for x in np.unique(m))
            assert all(1<=(int(x)&2047)<=theme['tiles'] or 1015<=(int(x)&2047)<=1022 or (int(x)&2047)==0 for x in np.unique(m)),(track,'Unexpected tile')
            blocks=theme['rgba'][(m>>13)&3,m&2047].copy()
            flip=(m&0x800)!=0;blocks[flip]=blocks[flip][:,:,::-1,:]
            flip=(m&0x1000)!=0;blocks[flip]=blocks[flip][:,::-1,:,:]
            a=blocks.transpose(0,2,1,3,4).reshape(H*8,W*8,4);im=Image.fromarray(a)
            im.save(folder/f'capa_{plane}.png');layers.append(a)
        full=Image.new('RGBA',(W*8,H*8),(0,0,0,255))
        for priority in (0,1):
            for plane in (1,0):
                a=layers[plane].copy();mask=np.repeat(np.repeat(((maps[plane]>>15)&1)==priority,8,axis=0),8,axis=1)
                a[:,:,3]*=mask.astype(np.uint8);full=Image.alpha_composite(full,Image.fromarray(a))
        full.convert('RGB').save(folder/'circuito.png')
        thumb=full.convert('RGB');thumb.thumbnail((768,230));thumb.save(folder/'miniatura.png')
        # Tiled stores four draw-order layers so that VDP priority is preserved.
        xml=f'<map version="1.10" orientation="orthogonal" renderorder="right-down" width="{W}" height="{H}" tilewidth="8" tileheight="8" infinite="0">'
        xml+=f'<properties><property name="ROM_track_id" type="int" value="{track}"/><property name="world" value="{theme["name"]}"/></properties>'
        for p in range(4):xml+=f'<tileset firstgid="{1+p*2048}" source="../../bancos/{world:02d}/paleta_{p}.tsx"/>'
        layerid=0;decoded=[np.zeros((H,W),np.uint16) for _ in range(2)]
        for priority in (0,1):
            for plane in (1,0):
                m=maps[plane].astype(np.uint32);gid=((m&2047)+((m>>13)&3)*2048+1)
                gid|=np.where(m&0x800,0x80000000,0).astype(np.uint32);gid|=np.where(m&0x1000,0x40000000,0).astype(np.uint32)
                gid=np.where(((m>>15)&1)==priority,gid,0).astype('<u4')
                packed=base64.b64encode(zlib.compress(gid.tobytes())).decode();layerid+=1
                xml+=f'<layer id="{layerid}" name="Capa {plane} prioridad {priority}" width="{W}" height="{H}"><data encoding="base64" compression="zlib">{packed}</data></layer>'
                back=np.frombuffer(zlib.decompress(base64.b64decode(packed)),dtype='<u4').reshape(H,W);mask=back!=0;local=(back&0x1fffffff)-1
                native=((local%2048)|((local//2048)<<13)|np.where(back&0x80000000,0x800,0)|np.where(back&0x40000000,0x1000,0)|(priority<<15)).astype(np.uint16)
                decoded[plane][mask]=native[mask]
        assert all(np.array_equal(a,b) for a,b in zip(maps,decoded))
        (folder/'mapa_editable.tmx').write_text(xml+'</map>')
        data=dict(track=track,world=world,width=W,height=H,words=base64.b64encode(b''.join(m.astype('<u2').tobytes() for m in maps)).decode(),refs=base64.b64encode(b''.join(a.astype('<u2').tobytes() for a in refs)).decode())
        (folder/'datos.js').write_text('loadTrack('+json.dumps(data,separators=(',',':'))+');')
        record=dict(id=track,world=world,world_name=theme['name'],resource_id=106+track,path=f'mapas/{track:02d}',tmx_roundtrip=True)
        catalog.append(record)
        print(f'Map {track:02d}/72: {theme["name"]}',flush=True)

    pngcount=0
    for world,theme in enumerate(themes):
        variants=used_by_world[world]|{(i,3) for i in range(1,theme['tiles']+1)}
        for t,p in sorted(variants):
            folder=theme['folder']/'tiles'/f'paleta_{p}';folder.mkdir(parents=True,exist_ok=True)
            im=Image.fromarray(theme['pix'][t]).convert('P');im.putpalette(theme['colors'][p*16:p*16+16].reshape(-1).tolist()+[0]*720)
            file=folder/f'tile_{t:04d}.png';im.save(file,transparency=0)
            a=np.asarray(Image.open(file));assert np.array_equal(a,theme['pix'][t]);pngcount+=1
        pixels=base64.b64encode(theme['pix'].tobytes()).decode()
        (theme['folder']/'datos.js').write_text('loadBank('+json.dumps(dict(world=world,pixels=pixels,colors=theme['colors'].tolist(),files=[f'{t}_{p}' for t,p in sorted(variants)]),separators=(',',':'))+');')
        atlas=Image.new('RGB',(32*40,((theme['tiles']+31)//32)*52),'#303040');draw=ImageDraw.Draw(atlas)
        for t in range(1,theme['tiles']+1):
            p=next((p for tt,p in sorted(used_by_world[world]) if tt==t),3);x=(t-1)%32*40;y=(t-1)//32*52
            tile=Image.fromarray(theme['rgba'][p,t]).resize((32,32),Image.Resampling.NEAREST);atlas.paste(tile,(x,y),tile);draw.text((x,y+34),str(t),fill='white')
        atlas.save(theme['folder']/'ATLAS_NUMERADO.png')
    publicthemes=[{k:v for k,v in t.items() if k in ('name','id','resource_id','rom_offset','rom_end','tiles')} for t in themes]
    manifest=dict(tracks=catalog,banks=publicthemes,track_count=72,tile_pngs=pngcount,seed_source='circuitos_png/captura/RAM.bin',all_tmx_roundtrips=True)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));(OUT/'catalogo.js').write_text('const CATALOG='+json.dumps(manifest,separators=(',',':'))+';')
    print(f'Finished: 72 maps, 6 banks, {pngcount} indexed tiles, all TMX roundtrips exact.',flush=True)

if __name__=='__main__':main()
