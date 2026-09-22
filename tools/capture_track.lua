local script=debug.getinfo(1,'S').source:sub(2):gsub('\\','/')
local root=assert(script:match('^(.*)/tools/[^/]+$'))..'/'
local out=root..'circuitos_png/captura/'
savestate.load(root..'partidas/SegundoCircuitoHeGanada8de8.State',true)
client.unpause()
joypad.set({},1)
emu.frameadvance()
client.screenshot(out..'pantalla.png')
for _,domain in ipairs({'VRAM','CRAM','VSRAM'}) do
 local f=assert(io.open(out..domain..'.bin','wb'))
 f:write(memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize(domain),domain));f:close()
end
local f=assert(io.open(out..'RAM.bin','wb'))
f:write(memory.read_bytes_as_binary_string(0xff0000,65536,'M68K BUS'));f:close()
local done=assert(io.open(out..'done.txt','w'));done:write('Captured one frame after supplied state');done:close()
client.exit()
