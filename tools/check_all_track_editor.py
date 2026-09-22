from pathlib import Path
import json
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
out=root/'todos_los_circuitos/verificacion';out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1500,'height':1000},accept_downloads=True)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((root/'todos_los_circuitos/EDITOR.html').as_uri())
    page.wait_for_function('current!==null && current.track===1')
    assert page.locator('#track option').count()==72
    for track in [1,5,10,16,23,30,37,72]:
        page.select_option('#track',str(track))
        page.wait_for_function(f'current!==null && current.track==={track}')
        assert page.evaluate('cache.size')>0
    page.locator('#map').click(position={'x':90,'y':90})
    assert 'Tile' in page.locator('#info').inner_text()
    # A deliberate single-cell change, save, undo, and restore from the saved file.
    page.select_option('#target','0');page.locator('#tile').fill('10');page.locator('#tile').dispatch_event('change')
    page.locator('#paint').click()
    before=page.evaluate('Array.from(current.map)')
    page.locator('#map').click(position={'x':110,'y':90})
    after=page.evaluate('Array.from(current.map)')
    assert sum(a!=b for a,b in zip(before,after))==1
    with page.expect_download() as d:page.locator('#save').click()
    file=out/'edicion_prueba.json';d.value.save_as(file)
    assert json.loads(file.read_text())['words']==after
    page.locator('#undo').click();assert page.evaluate('Array.from(current.map)')==before
    page.locator('#file').set_input_files(file)
    page.wait_for_function("document.querySelector('#status').textContent.includes('Edición restaurada')")
    assert page.evaluate('Array.from(current.map)')==after
    page.select_option('#layer','1');page.select_option('#layer','both');page.check('#grid');page.uncheck('#grid')
    page.screenshot(path=str(out/'editor_probado.png'))
    assert not errors,errors
    report=dict(catalog_tracks=72,worlds_opened=6,one_cell_paint=True,undo=True,json_save_restore_exact=True,layer_switches=True,js_errors=errors)
    (out/'editor_check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close()
