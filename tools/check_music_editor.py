from pathlib import Path
import json
from playwright.sync_api import sync_playwright
import export_music as m

with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((m.OUT/'EDITOR.html').as_uri())
    assert page.locator('#song option').count()==6
    for song in range(6):
        page.select_option('#song',str(song))
        assert page.locator('#events tr').count()>0
        assert f'cancion_{song+1:02d}' in page.locator('#midi').get_attribute('href')
    page.select_option('#song','0')
    first=page.locator('#events input').first;old=int(first.input_value());first.fill(str(old+1));first.dispatch_event('change')
    page.locator('#tempo').fill('151');page.locator('#tempo').dispatch_event('change')
    with page.expect_download() as download:page.click('#save')
    target=m.OUT/'validacion/editor_descarga.json';download.value.save_as(target)
    obj=json.loads(target.read_text());assert obj['tempo']==151
    event=next(e for e in obj['events'] if e['kind']=='note');assert event['op']==old+1
    m.from_json(obj)
    page.locator('#order').fill('6,5,4,3,2,1')
    with page.expect_download() as download:page.click('#saveOrder')
    target=m.OUT/'validacion/editor_orden.json';download.value.save_as(target)
    assert json.loads(target.read_text())==[6,5,4,3,2,1]
    assert not errors,errors
    browser.close()
print('Editor: six songs, note/tempo edit and JSON/order downloads verified in Edge.')
