"""Export and reinsert menus, HUD graphics and the Virgin logo."""
from pathlib import Path
import argparse, hashlib, json, shutil, struct
from PIL import Image
from extract_rnr import ROOT, ROM, tiles
from export_intro import SHA, resource_info, flat_palette, native_pixels, patch_resource
from export_ending import padded_palette, render_layer, encode_layer, tile_sheet_to_bytes, write_gpl

OUT=ROOT/'interfaz_png'
UI_PALETTE=bytes.fromhex('000004440222000004440222060804060204044402220eee0aaa04440000000c00000eee000006ce048e026c004a002800060ecc0caa0a88086606440422000e00000eee00000ace06ae048e026a0048002600ee00cc008a006a0e800c4008000e0e000e000c000800060eee0ccc088806660222000004000c4000ae00ee00a0')
RESULTS_PALETTE=bytes.fromhex('00000eee00000ace06ae048e026a0048002600ee00cc008a006a0e800c40080000000eee000006ce048e026c004a002800060ecc0caa0a88086606440422000e00000eee0caa0a8806440422020006ce028c00680026020400e000a0006000400e0e000e000c000800060eee0ccc088806660222000004000c4000ae00ee00a0')
HUD_PALETTE=bytes.fromhex('000004440222000004440222060804060204022204440eee0aaa04440000000c000008880666044404440222084c084a0628022204440eee0aaa04440000000c00e6006800ee00ce008e0046008e00ce0026004600240024002200020022002400e60eee0ccc088806660222000000ae008a006800460024000e000c00080004')
MENUS=((5,32,28,'preparar_carrera'),(7,32,32,'tienda'),(16,32,28,'contrasena'),(17,32,28,'cuatro_participantes'),(18,64,28,'resultados'))
HUD=(179,181,182,183,189)

def export(rom):
    menus=OUT/'menus';hud=OUT/'hud';virgin=OUT/'virgin';refs=OUT/'referencias'
    for p in (menus,hud,virgin,refs):p.mkdir(parents=True,exist_ok=True)
    gfx=resource_info(rom,3)['data']
    for mid,w,h,name in MENUS:
        pal=RESULTS_PALETTE if mid==18 else UI_PALETTE
        render_layer(resource_info(rom,mid)['data'],gfx,pal,w,h).save(menus/f'{name}_mapa_{mid}.png',transparency=0)
    tiles(gfx,flat_palette(UI_PALETTE),16).save(menus/'tiles_interfaz_3.png')
    (menus/'paleta_interfaz.bin').write_bytes(UI_PALETTE);write_gpl(menus/'paleta_interfaz.gpl','interfaz',UI_PALETTE)
    (menus/'paleta_resultados.bin').write_bytes(RESULTS_PALETTE);write_gpl(menus/'paleta_resultados.gpl','resultados',RESULTS_PALETTE)
    vg=resource_info(rom,186)['data'];vp=resource_info(rom,188)['data']
    render_layer(resource_info(rom,187)['data'],vg,vp,32,28).save(virgin/'virgin_logo.png',transparency=0)
    (virgin/'paleta_188.bin').write_bytes(vp);write_gpl(virgin/'paleta_188.gpl','virgin',vp)
    for rid in HUD:
        raw=resource_info(rom,rid)['data'];tiles(raw,flat_palette(HUD_PALETTE),16).save(hud/f'tiles_hud_{rid}.png')
    (hud/'paleta_capturada.bin').write_bytes(HUD_PALETTE);write_gpl(hud/'paleta_capturada.gpl','hud_carrera',HUD_PALETTE)
    captures=ROOT/'validation_bizhawk/audit_states'
    for src,name in ((captures/'PreCarreraHeGanado2.png','preparar_carrera.png'),(captures/'segundaCarreraParticipantesHeGanado.png','resultados.png'),(captures/'CarreraVoyGanando5.png','hud_carrera.png')):
        if src.exists():shutil.copyfile(src,refs/name)
    manifest=dict(menus=[x[0] for x in MENUS],menu_graphics=3,virgin=dict(graphics=186,map=187,palette=188),hud_graphics=list(HUD),rom_sha256=SHA)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('Interfaz, HUD y logo Virgin exportados.')

def import_edits(source,folder,target):
    rom=bytearray(source);changes=[];updates={};gi=resource_info(source,3)
    for mid,w,h,name in MENUS:
        pal=RESULTS_PALETTE if mid==18 else UI_PALETTE
        im=native_pixels(folder/'menus'/f'{name}_mapa_{mid}.png',pal)
        encode_layer(im,resource_info(source,mid)['data'],gi['data'],w,h,updates)
    data=bytearray(gi['data'])
    for tile,raw in updates.items():data[(tile-32)*32:(tile-31)*32]=raw
    if data!=gi['data']:changes.append(('menus',3,patch_resource(rom,gi,bytes(data))))
    vi=resource_info(source,186);vupdates={}
    encode_layer(native_pixels(folder/'virgin'/'virgin_logo.png',resource_info(source,188)['data']),resource_info(source,187)['data'],vi['data'],32,28,vupdates)
    data=bytearray(vi['data'])
    for tile,raw in vupdates.items():data[(tile-32)*32:(tile-31)*32]=raw
    if data!=vi['data']:changes.append(('virgin',186,patch_resource(rom,vi,bytes(data))))
    for rid in HUD:
        info=resource_info(source,rid);data=tile_sheet_to_bytes(folder/'hud'/f'tiles_hud_{rid}.png',len(info['data'])//32,HUD_PALETTE)
        if bytes(data)!=info['data']:changes.append(('hud',rid,patch_resource(rom,info,bytes(data))))
    if changes:rom[0x18e:0x190]=(sum(struct.unpack('>'+str((len(rom)-512)//2)+'H',rom[512:]))&65535).to_bytes(2,'big')
    if target.exists():raise FileExistsError(target)
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(rom)
    print(json.dumps(dict(output=str(target),changes=changes,identical=bytes(rom)==source)))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--import-dir',type=Path);ap.add_argument('--output-rom',type=Path);a=ap.parse_args();rom=ROM.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=SHA:raise ValueError('ROM europea inesperada')
    if a.import_dir:
        if not a.output_rom:ap.error('--import-dir necesita --output-rom')
        import_edits(rom,a.import_dir,a.output_rom)
    else:export(rom)
if __name__=='__main__':main()
