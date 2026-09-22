MUSIC_CAPTURE_OUT='musicas/validacion/editada/'
local script=debug.getinfo(1,'S').source:sub(2):gsub('\\','/')
local root=assert(script:match('^(.*)/tools/[^/]+$'))..'/'
dofile(root..'tools/capture_music.lua')
