"""Run the original Sound Images Z80 driver and log YM2612 writes as VGM."""
from pathlib import Path
import argparse, struct
import z80

ROOT=Path(__file__).resolve().parents[1]
ROM=(ROOT/"Rock 'n' Roll Racing (Europe).md").read_bytes()
OUT=ROOT/'musicas_tracker'
Z80_TEMPLATE=ROOT/'samples_wav/captura/z80_0000.bin'
YM_CLOCK=7_670_454
SAMPLES_PER_TICK=735  # YM2612 Timer B: clock/(144*16*(256-200)) ~= 59.45 Hz

def wait_cmd(n):
    out=bytearray()
    while n:
        part=min(n,65535)
        if part==735:out.append(0x62)
        elif part==882:out.append(0x63)
        elif part<=16:out.append(0x70+part-1)
        else:out.extend((0x61,part&255,part>>8))
        n-=part
    return out

def capture(song,seconds):
    m=z80.Z80Machine();ram=bytearray(Z80_TEMPLATE.read_bytes())
    if len(ram)!=8192:raise ValueError('Expected an 8192-byte Z80 RAM capture')
    m.set_memory_block(0,ram);m.pc=0x004f;m.sp=0x13f0;m.iff1=1;m.iff2=1
    m.memory[0x80]=0x80+song;m.memory[0x81]=0;m.memory[0x84]=0;m.memory[0x96]=0;m.memory[0x97]=0;m.memory[0xafd]=0
    bank=4;bits=0;reg=[0,0];data=bytearray();writes=0
    def read(addr):
        if addr in (0x4000,0x4002):return 2
        if addr>=0x8000:
            pos=bank*0x8000+(addr-0x8000)
            return ROM[pos] if pos<len(ROM) else 0xff
        return m.memory[addr]
    def write(addr,value):
        nonlocal bank,bits,writes
        value&=255
        if addr==0x6000:
            bank=((bank>>1)|((value&1)<<8))&0x1ff;bits=(bits+1)%9
        elif addr in (0x4000,0x4002):reg[(addr-0x4000)//2]=value
        elif addr in (0x4001,0x4003):
            port=(addr-0x4001)//2;data.extend((0x52+port,reg[port],value));writes+=1
    m.set_read_callback(read);m.set_write_callback(write)
    m.mark_addrs(0x8000,0x8000,m.READ_MARK)
    m.mark_addr(0x4000,m.READ_MARK);m.mark_addr(0x4002,m.READ_MARK)
    m.mark_addr(0x6000,m.WRITE_MARK)
    for a in range(0x4000,0x4004):m.mark_addr(a,m.WRITE_MARK)
    m.set_breakpoint(0x004f)
    ticks=round(seconds*44100/SAMPLES_PER_TICK)
    playing=False;first_tick=None
    for tick in range(ticks+180):
        m.step_over_breakpoint();budget=0
        while True:
            m.ticks_to_stop=200000;event=m.run();budget+=200000
            if event&1:break
            if budget>2000000:raise RuntimeError(f'Driver failed to return to main loop: event={event}, PC={m.pc:04x}')
        if m.memory[0x81]==song and not playing:playing=True;first_tick=tick
        if playing:
            data.extend(wait_cmd(SAMPLES_PER_TICK))
            if tick-first_tick>=ticks:break
    if not playing or writes<100:raise RuntimeError(f'Song {song} did not start ({writes} YM writes)')
    data.append(0x66);total=(tick-first_tick+1)*SAMPLES_PER_TICK
    header=bytearray(0x100);header[:4]=b'Vgm '
    struct.pack_into('<I',header,8,0x00000150);struct.pack_into('<I',header,0x18,total)
    struct.pack_into('<I',header,0x2c,YM_CLOCK);struct.pack_into('<I',header,0x34,0xcc)
    blob=header+data;struct.pack_into('<I',blob,4,len(blob)-4)
    return bytes(blob),dict(song=song,seconds=round(total/44100,3),ticks=tick-first_tick+1,ym_writes=writes)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--seconds',type=float,default=0,help='0 captures one decoded native cycle per song');args=ap.parse_args()
    OUT.mkdir(exist_ok=True)
    for song in range(1,7):
        seconds=args.seconds
        if not seconds:
            import export_music
            decoded=export_music.decode(export_music.original_songs(ROM)[song-1])
            seconds=max(c['ticks'] for c in decoded['channels'])/60+1
        blob,info=capture(song,seconds);path=OUT/f'cancion_{song:02d}.vgm';path.write_bytes(blob);print(path,info)

if __name__=='__main__':main()
