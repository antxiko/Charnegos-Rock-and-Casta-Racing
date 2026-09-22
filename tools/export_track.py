"""Reconstruct the loaded circuit from its two RAM maps and ROM dictionaries."""
from pathlib import Path
import sys, struct, json, csv, hashlib
import numpy as np
from PIL import Image, ImageDraw
from export_faces import resource, ROM, ROOT

OUT=ROOT/'circuitos_png'
CAP=OUT/'captura'
W,H=384,115

def native(im):
    a=np.asarray(im,dtype=np.uint8).reshape(8,8)
    return ((a[:,::2]<<4)|a[:,1::2]).tobytes()

def main():
    r=ROM.read_bytes();ram=(CAP/'RAM.bin').read_bytes();v=(CAP/'VRAM.bin').read_bytes();cr=(CAP/'CRAM.bin').read_bytes()
    assert hashlib.sha256(r).hexdigest()=='b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb'
    bank,start,end=resource(r,60);aux,auxstart,auxend=resource(r,189)
    assert v[32:32+len(bank)]==bank
    assert v[1015*32:1023*32]==aux
    dictionary=int.from_bytes(ram[0x454:0x458],'big')
    assert dictionary==0x889a0
    # Entry 59 is uncompressed. Each eight-byte record describes a 32x8 strip.
    dict_end=0x6b000+(int.from_bytes(r[0x6b000+60*4:0x6b000+61*4],'big')&0xffffff)
    strip_count=(dict_end-dictionary)//8
    colors=np.array([tuple(((word>>s)&7)*255//7 for s in (1,5,9)) for word in struct.unpack('>64H',cr)],dtype=np.uint8)
    pixels=np.empty((2048,8,8),np.uint8)
    raw=np.frombuffer(v,dtype=np.uint8).reshape(2048,8,4)
    pixels[:,:,::2]=raw>>4;pixels[:,:,1::2]=raw&15
    maps=[];refs=[];used=set();dynamic=set()
    for base in (0x458,0x5a98):
        ref=np.frombuffer(ram[base:base+22080],dtype='>u2').astype(np.uint16).reshape(H,96)
        words=np.empty((H,W),np.uint16)
        for y in range(H):
            for x in range(96):
                key=int(ref[y,x])&0x7ff8
                data=ram if key&0x4000 else r
                off=0xb0d8+(key&0x3ff8) if key&0x4000 else dictionary+key
                if key&0x4000:dynamic.add(key)
                vals=struct.unpack_from('>4H',data,off);words[y,x*4:x*4+4]=vals
                used.update((val&2047,(val>>13)&3) for val in vals)
        maps.append(words);refs.append(ref)

    def tile_rgba(word):
        a=pixels[word&2047]
        if word&0x800:a=a[:,::-1]
        if word&0x1000:a=a[::-1,:]
        rgb=colors[((word>>13)&3)*16+a]
        return np.dstack((rgb,np.where(a==0,0,255).astype(np.uint8)))

    layers=[]
    for plane,words in enumerate(maps):
        a=np.zeros((H*8,W*8,4),np.uint8)
        for y in range(H):
            for x in range(W):a[y*8:y*8+8,x*8:x*8+8]=tile_rgba(int(words[y,x]))
        im=Image.fromarray(a);im.save(OUT/f'capa_{plane}.png');layers.append(im)
    full=Image.new('RGBA',(W*8,H*8),tuple(colors[0])+(255,))
    # Static background ordering including each tile's VDP priority.
    for priority in (0,1):
        for plane in (1,0):
            a=np.array(layers[plane]);mask=np.repeat(np.repeat(((maps[plane]>>15)&1)==priority,8,axis=0),8,axis=1)
            a[:,:,3]*=mask.astype(np.uint8);full=Image.alpha_composite(full,Image.fromarray(a))
    full.convert('RGB').save(OUT/'CIRCUITO_COMPLETO.png')

    # Export all 830 bank tiles, plus alternative palettes actually used, and pickups.
    variants=used|{(t,3) for t in range(1,831)}
    variants={pair for pair in variants if 1<=pair[0]<=830 or 1015<=pair[0]<=1022}
    tile_records=[]
    for t,p in sorted(variants):
        folder=OUT/'tiles'/f'paleta_{p}';folder.mkdir(parents=True,exist_ok=True)
        im=Image.fromarray(pixels[t]).convert('P');im.putpalette(colors[p*16:p*16+16].reshape(-1).tolist()+[0]*720)
        path=folder/f'tile_{t:04d}.png';im.save(path,transparency=0)
        assert native(Image.open(path))==v[t*32:(t+1)*32]
        rid=60 if t<=830 else 189;local=t-1 if rid==60 else t-1015
        tile_records.append(dict(tile=t,palette=p,file=path.relative_to(OUT).as_posix(),resource_id=rid,decompressed_offset=local*32,uses=sum(int(np.count_nonzero((m&0x67ff)==(p<<13|t))) for m in maps)))
    paldir=OUT/'paletas';paldir.mkdir(exist_ok=True)
    for p in range(4):
        cs=colors[p*16:p*16+16]
        (paldir/f'paleta_{p}.bin').write_bytes(cr[p*32:p*32+32])
        (paldir/f'paleta_{p}.gpl').write_text('GIMP Palette\nName: Circuito '+str(p)+'\nColumns: 16\n#\n'+'\n'.join(f'{a} {b} {c} indice_{i:02d}' for i,(a,b,c) in enumerate(cs)))
    sheet=Image.new('RGB',(32*40,26*52),'#303040');draw=ImageDraw.Draw(sheet)
    for t in range(1,831):
        x=(t-1)%32*40;y=(t-1)//32*52
        p=next((p for tt,p in sorted(used) if tt==t),3)
        ti=Image.fromarray(tile_rgba(t|(p<<13))).resize((32,32),Image.Resampling.NEAREST)
        sheet.paste(ti,(x,y),ti);draw.text((x,y+34),str(t),fill='white')
    sheet.save(OUT/'ATLAS_TILES_NUMERADOS.png')
    blocks=[];bd=OUT/'piezas_32x8';bd.mkdir(exist_ok=True)
    keys=list(range(0,strip_count*8,8))+sorted(dynamic)
    bs=Image.new('RGB',(8*150,((len(keys)+7)//8)*52),'#303040');bdr=ImageDraw.Draw(bs)
    for i,key in enumerate(keys):
        data=ram if key&0x4000 else r;off=0xb0d8+(key&0x3ff8) if key&0x4000 else dictionary+key
        words=struct.unpack_from('>4H',data,off);im=Image.new('RGBA',(32,8))
        for j,word in enumerate(words):im.paste(Image.fromarray(tile_rgba(word)),(j*8,0))
        label=f'{key:04X}';im.save(bd/f'pieza_{label}.png')
        x=i%8*150;y=i//8*52;bdr.text((x,y),label,fill='white');big=im.resize((128,32),Image.Resampling.NEAREST);bs.paste(big,(x,y+16),big)
        blocks.append(dict(key=key,file=f'piezas_32x8/pieza_{label}.png',words=list(words),dynamic=bool(key&0x4000)))
    bs.save(OUT/'ATLAS_PIEZAS_NUMERADAS.png')
    for plane,m in enumerate(maps):
        with (OUT/f'mapa_capa_{plane}.csv').open('w',newline='') as f:
            wr=csv.writer(f);wr.writerow(['x_tile','y_tile','tile','palette','flip_x','flip_y','priority','piece_ref'])
            for y in range(H):
                for x in range(W):
                    word=int(m[y,x]);wr.writerow([x,y,word&2047,(word>>13)&3,bool(word&0x800),bool(word&0x1000),word>>15,f'{int(refs[plane][y,x//4])&0x7ff8:04X}'])
    # Compare the currently streamed VRAM windows to reconstructed map attributes.
    validations=[]
    for plane,vbase in enumerate((0xc000,0xe000)):
        live=np.frombuffer(v[vbase:vbase+4096],dtype='>u2').reshape(32,64)
        best=(0,0,0)
        for oy in range(0,H-28):
            for ox in range(0,W-32):
                if ox%64!=0x10c%64 or oy%32!=0x36%32:continue
                expect=maps[plane][oy:oy+28,ox:ox+32]
                got=live[np.arange(oy,oy+28)%32][:,np.arange(ox,ox+32)%64]
                matches=int(np.count_nonzero(expect==got))
                if matches>best[0]:best=(matches,ox,oy)
        validations.append(dict(plane=plane,matched_words=best[0],checked_words=896,world_tile_x=best[1],world_tile_y=best[2]))
    manifest=dict(dimensions=[3072,920],map_tiles=[W,H],tile_size=8,piece_size=[32,8],resource_id=60,graphics_rom_offset=hex(start),graphics_rom_end=hex(end),dictionary_rom_offset=hex(dictionary),dictionary_resource_id=59,graphics_tiles=830,all_graphics_match_vram=True,tiles=tile_records,pieces=blocks,validation=validations)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    viewer=dict(width=W,height=H,maps=[m.reshape(-1).tolist() for m in maps],refs=[a.reshape(-1).tolist() for a in refs],tiles={str(t):pixels[t].reshape(-1).tolist() for t in {x[0] for x in used}},files={f'{x["tile"]}_{x["palette"]}':x['file'] for x in tile_records})
    (OUT/'datos.js').write_text('const DATA='+json.dumps(viewer,separators=(',',':'))+';')
    print(json.dumps(dict(exported_tile_pngs=len(tile_records),pieces=len(blocks),vram_bank_matches=830,validation=validations)))

if __name__=='__main__':main()
