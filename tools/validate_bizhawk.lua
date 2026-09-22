local script=debug.getinfo(1,'S').source:sub(2):gsub('\\','/')
local root=assert(script:match('^(.*)/tools/[^/]+$'))..'/'
local out = root..'validation_bizhawk'
local function dump(stem, domain)
  local f=assert(io.open(out..'/'..stem..'-'..domain..'.bin','wb'))
  if domain=='68K RAM' then
    f:write(memory.read_bytes_as_binary_string(0xff0000,65536,'M68K BUS'))
  else
    f:write(memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize(domain),domain))
  end
  f:close()
end
local f=assert(io.open(out..'/domains.txt','w'))
for _,d in ipairs(memory.getmemorydomainlist()) do f:write(d..' '..memory.getmemorydomainsize(d)..'\n') end
f:close()
client.unpause()
client.speedmode(800)
for n=1,4800 do
  joypad.set({},1)
  emu.frameadvance()
  if n%600==0 then
    local stem=string.format('frame-%04d',n)
    client.screenshot(out..'/'..stem..'.png')
    for _,d in ipairs({'VRAM','CRAM','68K RAM'}) do dump(stem,d) end
    savestate.save(out..'/'..stem..'.State')
    local log=assert(io.open(out..'/progress.txt','w'));log:write(stem);log:close()
  end
end
local done=assert(io.open(out..'/done.txt','w'));done:write('4800 frames captured');done:close()
client.exit()
