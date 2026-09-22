"""Export and reinsert the editable graphics used by the ending cinematic."""
from pathlib import Path
import argparse, hashlib, json, struct
from PIL import Image
from extract_rnr import ROOT, ROM, tiles
from export_intro import SHA, resource_info, flat_palette, colors, native_pixels, tile_bytes, patch_resource

OUT = ROOT / 'final_png'
PLANET_RED = bytes.fromhex('00000004000200020004000400060008000a000a000c000c000e004e006e00ae')
PLANET_GREEN = bytes.fromhex('0000002000600040004000200020080006000600040004000640066208640884')
SCENES = {
    '01_hangar': dict(gfx=190, maps=[(191,64,28),(192,64,28)], palette=196, palette_parts=[], extras=[193,194,197,198,199,200]),
    # The planet keeps the 64-colour CRAM from the hangar and updates line 0 with resource 203.
    '02_planeta': dict(gfx=201, maps=[(202,64,28)], palette=196, palette_parts=[203], extras=[]),
    '03_ciudad': dict(gfx=204, maps=[(205,64,32),(206,32,32)], palette=207, palette_parts=[], extras=[]),
    '04_escenario': dict(gfx=208, maps=[(209,64,32)], palette=210, palette_parts=[], extras=[]),
}

def padded_palette(raw): return raw + b'\0'*(128-len(raw))

def scene_palette(rom,s):
    pal=bytearray(padded_palette(resource_info(rom,s['palette'])['data']))
    # The cinematic generates two colour-cycle phases for the planet at runtime.
    if s['palette_parts']:pal[96:128]=PLANET_RED
    return bytes(pal)

def render_layer(mapdata,gfx,pal,w,h):
    im=Image.new('P',(w*8,h*8));im.putpalette(flat_palette(pal));im.info['transparency']=0
    for ty in range(h):
      for tx in range(w):
        a=struct.unpack_from('>H',mapdata,(ty*w+tx)*2)[0];tile=a&2047;line=(a>>13)&3;off=(tile-32)*32
        if not 0<=off<=len(gfx)-32: continue
        for y in range(8):
          sy=7-y if a&0x1000 else y
          for x in range(8):
            sx=7-x if a&0x800 else x;b=gfx[off+sy*4+sx//2];n=b&15 if sx&1 else b>>4
            im.putpixel((tx*8+x,ty*8+y),line*16+n)
    return im

def composite(layers):
    out=layers[0].copy()
    for layer in layers[1:]:
      for y in range(min(out.height,layer.height)):
       for x in range(min(out.width,layer.width)):
        p=layer.getpixel((x,y))
        if p&15:out.putpixel((x,y),p)
    return out

def encode_layer(im,mapdata,gfx,w,h,updates):
    for ty in range(h):
      for tx in range(w):
        a=struct.unpack_from('>H',mapdata,(ty*w+tx)*2)[0];tile=a&2047;line=(a>>13)&3;off=(tile-32)*32
        if not 0<=off<=len(gfx)-32:continue
        px=[[0]*8 for _ in range(8)]
        for y in range(8):
          for x in range(8):
            p=im.getpixel((tx*8+x,ty*8+y))
            if p&15 and p//16!=line:raise ValueError(f'Paleta incorrecta en tile {tile}: se esperaba linea {line}, aparece {p//16}')
            sx=7-x if a&0x800 else x;sy=7-y if a&0x1000 else y;px[sy][sx]=p&15
        raw=tile_bytes(px)
        if tile in updates and updates[tile]!=raw:raise ValueError(f'El tile compartido {tile} tiene dos ediciones distintas')
        updates[tile]=raw

def tile_sheet_to_bytes(path,count,pal):
    im=native_pixels(path,pal);cols=16
    if im.size!=(128,max(8,((count+15)//16)*8)):raise ValueError(f'Tamano incorrecto en {path.name}')
    out=bytearray()
    for t in range(count):
      px=[[im.getpixel(((t%cols)*8+x,(t//cols)*8+y))&15 for x in range(8)] for y in range(8)]
      out.extend(tile_bytes(px))
    return bytes(out)

def export(rom):
    OUT.mkdir(exist_ok=True);manifest=[]
    for name,s in SCENES.items():
      folder=OUT/name;folder.mkdir(exist_ok=True);gfx=resource_info(rom,s['gfx'])['data'];pr=resource_info(rom,s['palette'])['data'];pal=scene_palette(rom,s);layers=[]
      for n,(mid,w,h) in enumerate(s['maps'],1):
        md=resource_info(rom,mid)['data'];im=render_layer(md,gfx,pal,w,h);im.save(folder/f'capa_{n:02d}_mapa_{mid}.png',transparency=0);layers.append(im)
      composite(layers).save(folder/'montaje_referencia.png')
      tiles(gfx,flat_palette(pal),16).save(folder/f'tiles_principales_{s["gfx"]}.png')
      for rid in s['extras']:
        raw=resource_info(rom,rid)['data'];tiles(raw,flat_palette(pal),16).save(folder/f'tiles_animacion_{rid}.png')
      (folder/f'paleta_{s["palette"]}.bin').write_bytes(pr)
      (folder/f'paleta_{s["palette"]}.gpl').write_text('GIMP Palette\nName: '+name+'\nColumns: 16\n#\n'+'\n'.join(f'{a} {b} {c} indice_{i:02d}' for i,(a,b,c) in enumerate(colors(pal)[:len(pr)//2])),encoding='ascii')
      for pid in s['palette_parts']:
        part=resource_info(rom,pid)['data'];(folder/f'actualizacion_paleta_{pid}.bin').write_bytes(part)
      if s['palette_parts']:
        (folder/'paleta_efectiva.gpl').write_text('GIMP Palette\nName: '+name+'_efectiva\nColumns: 16\n#\n'+'\n'.join(f'{a} {b} {c} indice_{i:02d}' for i,(a,b,c) in enumerate(colors(pal))),encoding='ascii')
        green=bytearray(pal);green[96:128]=PLANET_GREEN
        for phase,value in [('roja',pal),('verde',bytes(green))]:
          (folder/f'paleta_fase_{phase}.bin').write_bytes(value)
          (folder/f'paleta_fase_{phase}.gpl').write_text('GIMP Palette\nName: planeta_'+phase+'\nColumns: 16\n#\n'+'\n'.join(f'{a} {b} {c} indice_{i:02d}' for i,(a,b,c) in enumerate(colors(value))),encoding='ascii')
      manifest.append(dict(scene=name,graphics=s['gfx'],maps=[x[0] for x in s['maps']],palette=s['palette'],palette_updates=s['palette_parts'],extras=s['extras']))
    (OUT/'manifest.json').write_text(json.dumps(dict(rom_sha256=SHA,scenes=manifest),indent=2),encoding='utf8')
    print('Final exportado por escenas, capas, tiles y paletas.')

def import_edits(source,folder,target):
    rom=bytearray(source);changes=[]
    for name,s in SCENES.items():
      base=folder/name;gi=resource_info(source,s['gfx']);pal=scene_palette(source,s);updates={}
      for n,(mid,w,h) in enumerate(s['maps'],1):
        md=resource_info(source,mid)['data'];im=native_pixels(base/f'capa_{n:02d}_mapa_{mid}.png',pal);encode_layer(im,md,gi['data'],w,h,updates)
      data=bytearray(gi['data'])
      for tile,raw in updates.items():data[(tile-32)*32:(tile-31)*32]=raw
      if data!=gi['data']:changes.append((name,s['gfx'],patch_resource(rom,gi,data)))
      for rid in s['extras']:
        info=resource_info(source,rid);data=tile_sheet_to_bytes(base/f'tiles_animacion_{rid}.png',len(info['data'])//32,pal)
        if data!=info['data']:changes.append((name,rid,patch_resource(rom,info,data)))
    if changes:rom[0x18e:0x190]=(sum(struct.unpack('>'+str((len(rom)-512)//2)+'H',rom[512:]))&65535).to_bytes(2,'big')
    if target.exists():raise FileExistsError(target)
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(rom);print(json.dumps(dict(output=str(target),changes=changes,identical=bytes(rom)==source)))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--import-dir',type=Path);ap.add_argument('--output-rom',type=Path);a=ap.parse_args();rom=ROM.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=SHA:raise ValueError('ROM europea inesperada')
    if a.import_dir:
      if not a.output_rom:ap.error('--import-dir necesita --output-rom')
      import_edits(rom,a.import_dir,a.output_rom)
    else:export(rom)
if __name__=='__main__':main()
