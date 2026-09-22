local script=debug.getinfo(1,'S').source:sub(2):gsub('\\','/')
local root=assert(script:match('^(.*)/tools/[^/]+$'))..'/'
local out=root..'samples_wav/captura/'
savestate.load(root..'partidas/CarreraVoyGanando5.State',true)
client.unpause()
client.speedmode(800)
local log=assert(io.open(out..'z80_commands.csv','w'))
log:write('frame,commands_80_af\n')
for n=0,900 do
 if n%30==0 then
  local f=assert(io.open(out..string.format('z80_%04d.bin',n),'wb'))
  f:write(memory.read_bytes_as_binary_string(0,8192,'Z80 RAM'));f:close()
 end
 local b=memory.read_bytes_as_binary_string(0x80,48,'Z80 RAM')
 local s='';for i=1,#b do s=s..string.format('%02x',b:byte(i)) end
 log:write(n..','..s..'\n')
 if n==1 then client.screenshot(out..'partida_original.png') end
 if n==60 then client.screenshot(out..'carrera.png') end
 if n==2 then joypad.set({Start=true},1) else joypad.set({},1) end
 emu.frameadvance()
end
log:close()
local f=assert(io.open(out..'done.txt','w'));f:write('901 frames observed');f:close()
client.exit()
