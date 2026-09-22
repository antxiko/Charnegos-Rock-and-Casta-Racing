"""Smoke-check local-file navigation and tile selection in the circuit viewer."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json

root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1500,'height':900})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((root/'circuitos_png/EXPLORAR.html').as_uri())
    page.wait_for_function("document.querySelector('#map').style.width==='3072px'")
    page.locator('#map').click(position={'x':120,'y':180})
    page.locator('#tilelink').wait_for(state='visible')
    assert 'Tile ' in page.locator('#details').inner_text()
    file=page.locator('#tilelink').get_attribute('href')
    assert (root/'circuitos_png'/file).is_file()
    assert page.locator('#preview').evaluate('(im)=>im.complete && im.naturalWidth===8')
    for layer in ('0','1','both'):page.select_option('#layer',layer)
    page.select_option('#zoom','0.5');page.check('#grid')
    page.screenshot(path=str(root/'circuitos_png/captura/visor_comprobado.png'))
    page.uncheck('#grid');page.locator('#clear').click()
    assert not errors,errors
    result={'local_file_load':True,'tile_selection':True,'png_link_exists':True,'palette_preview_8x8':True,'layer_switches':True,'zoom_and_grid':True,'js_errors':errors}
    (root/'circuitos_png/captura/viewer_check.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result));browser.close()
