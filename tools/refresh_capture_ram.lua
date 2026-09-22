local script=debug.getinfo(1,'S').source:sub(2):gsub('\\','/')
local root=assert(script:match('^(.*)/tools/[^/]+$'))..'/'
local out=root..'validation_bizhawk'
for n=600,4800,600 do
  local stem=string.format('frame-%04d',n)
  savestate.load(out..'/'..stem..'.State',true)
  local f=assert(io.open(out..'/'..stem..'-68K RAM.bin','wb'))
  f:write(memory.read_bytes_as_binary_string(0xff0000,65536,'M68K BUS'));f:close()
end
local f=assert(io.open(out..'/ram-refreshed.txt','w'));f:write('RAM read explicitly from M68K BUS FF0000-FFFFFF');f:close()
client.exit()
