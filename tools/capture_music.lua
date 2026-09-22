local script=debug.getinfo(1,'S').source:sub(2):gsub('\\','/')
local root=assert(script:match('^(.*)/tools/[^/]+$'))..'/'
local out=root..(MUSIC_CAPTURE_OUT or 'musicas/validacion/')
local log=assert(io.open(out..'z80.csv','w'))
log:write('song,frame,channel,pc,note,instrument,duration,counter,transpose,playing\n')
for song=1,6 do
 savestate.load(root..'partidas/CarreraVoyGanando5.State',true)
 client.unpause();client.speedmode(800)
 memory.write_u8(0x80,0x80+song,'Z80 RAM');memory.write_u8(0x81,0,'Z80 RAM')
 memory.write_u8(0x96,0,'Z80 RAM');memory.write_u8(0x97,0,'Z80 RAM')
 memory.write_u8(0xafd,0,'Z80 RAM')
 for frame=1,360 do
  memory.write_u8(0x84,0,'Z80 RAM')
  joypad.set({},1);emu.frameadvance()
  for ch=1,5 do
   local p=ch*256
   log:write(string.format('%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n',song,frame,ch,
    memory.read_u16_le(p,'Z80 RAM'),memory.read_u8(p+7,'Z80 RAM'),memory.read_u8(p+10,'Z80 RAM'),
    memory.read_u8(p+6,'Z80 RAM'),memory.read_u8(p+5,'Z80 RAM'),memory.read_u8(p+16,'Z80 RAM'),memory.read_u8(0x81,'Z80 RAM')))
  end
  if frame==30 then
   local f=assert(io.open(out..string.format('song_%d_ram.bin',song),'wb'))
   f:write(memory.read_bytes_as_binary_string(0,8192,'Z80 RAM'));f:close()
  end
 end
end
log:close()
local f=assert(io.open(out..'done.txt','w'));f:write('6 songs, 360 frames each');f:close()
client.exit()
