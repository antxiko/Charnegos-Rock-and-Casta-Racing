local script=debug.getinfo(1,'S').source:sub(2):gsub('\\','/')
local root=assert(script:match('^(.*)/tools/[^/]+$'))..'/'
local f=assert(io.open(root..'musicas/validacion/ym_callbacks.txt','w'))
f:write('memory params '..tostring(event.can_use_callback_params('memory'))..'\n')
local count=0
local function cb(...)
 count=count+1
 if count<1000 then
  local a={...};for i,v in ipairs(a) do a[i]=tostring(v) end
  f:write(table.concat(a,',')..'\n')
 end
end
for _,a in ipairs({0x4000,0x4001,0x4002,0x4003,0xa04000,0xa04001,0xa04002,0xa04003}) do
 local ok,id=pcall(event.on_bus_write,cb,a,'ym_'..string.format('%x',a))
 f:write(string.format('hook %x %s %s\n',a,tostring(ok),tostring(id)))
end
savestate.load(root..'partidas/CarreraVoyGanando5.State',true)
client.unpause();client.speedmode(800)
memory.write_u8(0x80,0x81,'Z80 RAM');memory.write_u8(0x81,0,'Z80 RAM');memory.write_u8(0x84,0,'Z80 RAM')
for n=1,120 do memory.write_u8(0x84,0,'Z80 RAM');emu.frameadvance() end
f:write('count '..count..'\n');f:close();client.exit()
