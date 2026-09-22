"""Cross-check exported race frames against BizHawk VRAM, CRAM and SAT."""
from export_cars import *
from extract_rnr import tiles

CAP=ROOT/'validation_bizhawk'

def main():
    r=ROM.read_bytes(); remap=r[0x6abe:0x6bbe]
    report=[];thumbs=[]
    for n in (1800,2400,4800):
        v=(CAP/f'frame-{n:04d}-VRAM.bin').read_bytes()
        cram=(CAP/f'frame-{n:04d}-CRAM.bin').read_bytes()
        for slot,start in enumerate((0x9000,0xb280,0xb700,0xf280)):
            data=v[start:start+STRIDE]; matches=[]
            for k in range(225):
                native=r[BASE+k*STRIDE:BASE+(k+1)*STRIDE]
                expected=bytes(remap[b] for b in native) if slot%2 else native
                if data==expected:matches.append((k//45+1,k%45))
            assert matches, (n,slot,'No matching exported frame')
            # SAT is at F000 in these captured race scenes; find this sprite group.
            candidates=[]
            for a in range(0xf000,0xf280,8):
                y,sl,attr,x=struct.unpack_from('>4H',v,a)
                if attr&2047==start//32:candidates.append(a)
            assert len(candidates)==1
            sat=candidates[0];parts=[struct.unpack_from('>4H',v,sat+i*8) for i in range(4)]
            p=(parts[0][2]>>13)&3;rawpal=cram[p*32:p*32+32]
            rgb=[tuple(((w>>s)&7)*255//7 for s in (1,5,9)) for w in struct.unpack('>16H',rawpal)]
            pal=[x for c in rgb for x in c]+[0]*720
            im=frame(data,pal)
            if parts[0][2]&0x800:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if parts[0][2]&0x1000:im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            # Independently assemble the four hardware sprites using SAT coordinates.
            assembled=Image.new('P',(48,48));assembled.putpalette(pal)
            ox=min(a[3]&511 for a in parts);oy=min(a[0]&511 for a in parts)
            for y,sl,attr,x in parts:
                assert sl>>8==10 and ((attr>>13)&3)==p
                t=attr&2047
                strip=tiles(v[t*32:(t+9)*32],pal,columns=9)
                part=Image.new('P',(24,24));part.putpalette(pal)
                for k in range(9):part.paste(strip.crop((k*8,0,k*8+8,8)),(k//3*8,k%3*8))
                if attr&0x800:part=part.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                if attr&0x1000:part=part.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                assembled.paste(part,((x&511)-ox,(y&511)-oy))
            assert assembled.tobytes()==im.tobytes(), 'SAT layout mismatch'
            car,f=matches[0];stem=f'frame-{n:04d}_slot-{slot}_coche-{car:02d}_vista-{f:02d}'
            im.save(CAP/(stem+'.png'),transparency=0)
            (CAP/(stem+'.gpl')).write_text('GIMP Palette\nName: BizHawk live\nColumns: 16\n#\n'+'\n'.join(f'{a} {b} {c} indice_{i:02d}' for i,(a,b,c) in enumerate(rgb)))
            thumbs.append((stem,im))
            report.append(dict(frame=n,slot=slot,car=car,view=f,vram=hex(start),palette_line=p,remapped=bool(slot%2),sat=hex(sat),native_match=True,sat_layout_match=True))
    sheet=Image.new('RGB',(4*200,3*180),'#303040');draw=ImageDraw.Draw(sheet)
    for i,(stem,im) in enumerate(thumbs):
        x=i%4*200;y=i//4*180;row=report[i]
        draw.text((x+4,y+4),f"Frame {row['frame']} / coche {row['car']}\nVista {row['view']} / paleta {row['palette_line']}",fill='white')
        big=im.convert('RGBA').resize((144,144),Image.Resampling.NEAREST);sheet.paste(big,(x+20,y+34),big)
    sheet.save(CAP/'COCHES_BIZHAWK.png')
    (CAP/'verification.json').write_text(json.dumps(report,indent=2))
    print(f'{len(report)} live sprites: exact native/remapped match AND independent SAT assembly match.')

if __name__=='__main__':main()
