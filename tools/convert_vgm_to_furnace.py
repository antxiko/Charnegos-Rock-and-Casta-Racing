"""Convert the six YM2612 captures to editable Furnace modules."""
from pathlib import Path
import subprocess,shutil

ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'musicas_tracker'
tool=shutil.which('vgm2fur')
if not tool:raise RuntimeError('vgm2fur is not installed')
for i in range(1,7):
    src=folder/f'cancion_{i:02d}.vgm';dst=folder/f'cancion_{i:02d}.fur'
    subprocess.run([tool,str(src),'-o',str(dst),
                    '--playback-rate=60','--pattern-length=64'],check=True)
    if not dst.exists() or dst.stat().st_size<100:raise RuntimeError(f'Invalid output: {dst}')
    print(dst.name,dst.stat().st_size,'bytes')
