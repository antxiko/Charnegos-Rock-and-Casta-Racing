from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import export_texts

with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((ROOT/'textos/EDITOR.html').as_uri())
    page.locator('#file').set_input_files(ROOT/'textos/textos.json')
    page.wait_for_function("document.querySelectorAll('textarea').length > 200")
    assert page.locator('textarea').count()==214
    page.locator('#search').fill('PLAYER');assert page.locator('textarea').count()>=2
    first=page.locator('textarea').first;first.fill('PILOTO');first.dispatch_event('input')
    with page.expect_download() as download:page.click('#save')
    target=ROOT/'textos/validacion_editor.json';download.value.save_as(target)
    doc=json.loads(target.read_text(encoding='utf8'));row=next(x for x in doc['strings'] if x['offset']==0x398c)
    assert row['text']=='PILOTO';assert export_texts.encode(row)==b'PILOTO';assert not errors,errors
    browser.close()
print('Editor: 214 strings loaded; filtering, editing, validation and download verified in Edge.')
