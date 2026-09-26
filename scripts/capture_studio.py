"""Optional browser evidence harness for this restricted host.
Uses a loopback HTTP transport binding because managed Chromium blocks navigation.
This is not a replacement for native-machine browser/GPU acceptance.
Requires separately installed Playwright, Chromium, and Xvfb (Linux).
"""
from pathlib import Path
import sys,os,time,subprocess,threading,json,base64,urllib.request,urllib.error,re
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from floorforge.server import make_server
from playwright.sync_api import sync_playwright

def main():
 out=ROOT/'evidence';out.mkdir(exist_ok=True)
 server=make_server(Path(os.environ.get('FF_CAPTURE_WORK','/mnt/data/ff_ui_test')))
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 url=f'http://127.0.0.1:{server.server_port}'
 calls=[];errors=[];checks=[]
 def bridge(source,request):
  path=request['url']
  if not isinstance(path,str) or not path.startswith('/') or path.startswith('//'):raise ValueError('Only this studio HTTP transport is permitted')
  req=urllib.request.Request(url+path,data=request.get('body','').encode() if request.get('method')=='POST' else None,headers=request.get('headers',{}),method=request.get('method','GET'))
  try:
   with urllib.request.urlopen(req,timeout=30) as response:status=response.status;data=response.read();ctype=response.headers.get('Content-Type','')
  except urllib.error.HTTPError as e:status=e.code;data=e.read();ctype=e.headers.get('Content-Type','')
  calls.append({'path':path,'method':request.get('method','GET'),'status':status})
  print(request.get('method','GET'),path,status,flush=True)
  return {'status':status,'body':base64.b64encode(data).decode(),'contentType':ctype}
 shim='''<script>window.fetch=async (url,options={})=>{const x=await window.localHTTP({url:String(url),method:options.method||'GET',body:options.body||'',headers:options.headers||{}});const bytes=Uint8Array.from(atob(x.body),c=>c.charCodeAt(0));return new Response(bytes,{status:x.status,headers:{'Content-Type':x.contentType}});};</script>'''
 html=(ROOT/'web/index.html').read_text().replace('<link rel="stylesheet" href="/style.css">','<style>'+(ROOT/'web/style.css').read_text()+'</style>')
 html=html.replace('<script src="/viewer.js"></script><script src="/app.js"></script>',shim+'<script>'+(ROOT/'web/viewer.js').read_text()+'</script><script>'+(ROOT/'web/app.js').read_text()+'</script>')
 x=subprocess.Popen(['Xvfb',':97','-screen','0','1600x1100x24'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);os.environ['DISPLAY']=':97';time.sleep(.7)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
   page=browser.new_page(viewport={'width':1440,'height':1024},device_scale_factor=1)
   page.expose_binding('localHTTP',bridge);page.on('pageerror',lambda e:(errors.append(str(e)),print('JSERROR',str(e),flush=True)))
   page.set_content(html);page.wait_for_function('window.__ffApp && window.__ffApp.viewer',timeout=30000)
   page.wait_for_timeout(900)
   checks.append({'check':'bundled project + actual renderer initialised','passed':True})
   print('capture desktop',flush=True);page.screenshot(path=str(out/'studio-desktop.png'))
   page.click('[data-tab="drawings"]');page.wait_for_timeout(300);page.screenshot(path=str(out/'studio-drawings.png'))
   assert page.locator('#sheet-select option').count()==9;checks.append({'check':'nine generated drawing sheets selectable','passed':True})
   page.click('[data-tab="documents"]');page.screenshot(path=str(out/'studio-review.png'))
   assert 'NOT EVALUATED' in page.locator('#review-content').inner_text();checks.append({'check':'regulatory unknown remains visible','passed':True})
   page.click('#understand');page.wait_for_selector('#intent-dialog[open]');assert 'quick-survey' in page.locator('#intent-content').inner_text();page.click('[data-close="intent-dialog"]');checks.append({'check':'fused-source preflight opens','passed':True})
   print('generate compact',flush=True);page.select_option('#preset','compact');page.click('#generate');page.wait_for_function("document.getElementById('build-id').textContent!=='BUNDLED EXAMPLE' && !document.getElementById('generate').disabled",timeout=45000)
   print('generation completed',flush=True);assert 'Garden Pavilion' in page.locator('#project-title').inner_text();checks.append({'check':'UI POST generation to output/render completes for 30x40','passed':True})
   page.click('[data-tab="home"]');page.click('[data-mode="dollhouse"]');page.wait_for_timeout(500);page.screenshot(path=str(out/'studio-generated-compact.png'))
   print('grid checks',flush=True);page.evaluate("document.getElementById('grid-open').click()");assert page.evaluate("document.getElementById('grid-dialog').open");page.evaluate("document.querySelector('#grid-board button').click()");grid=page.evaluate('window.__ffApp.collect()');page.evaluate("document.getElementById('grid-dialog').close()");checks.append({'check':'grid painter interaction','passed':True})
   print('AI choices',flush=True);page.evaluate("document.getElementById('ai-open').click()");assert page.evaluate("document.getElementById('ai-dialog').open");assert page.locator('[name="ai-tier"]').count()==3;page.evaluate("document.getElementById('ai-dialog').close()");checks.append({'check':'three AI consent choices visible','passed':True})
   project=page.evaluate('window.__ffApp.collect()');assert project['brief']['bedrooms']==2 and project['brief']['storeys']==1;checks.append({'check':'reopenable project collects actual inputs','passed':True})
   print('mobile capture',flush=True);page.evaluate("window.__ffApp.viewer.destroy()");page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300);page.screenshot(path=str(out/'studio-mobile.png'),full_page=True)
   dims=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');checks.append({'check':'mobile no horizontal document overflow','passed':dims['scroll']<=dims['width'],'details':dims})
   gl=page.evaluate("(()=>{let g=window.__ffApp.viewer.gl,e=g.getExtension('WEBGL_debug_renderer_info');return {vendor:g.getParameter(7936),renderer:e?g.getParameter(e.UNMASKED_RENDERER_WEBGL):g.getParameter(7937)}})()")
   browser.close()
  record={'method':'Chromium software SwiftShader under Xvfb. HTML set_content; fetch transport bound to actual loopback HTTP server because managed navigation is blocked. Not a real-GPU or native-platform sign-off.','checks':checks,'page_errors':errors,'requests':calls,'gpu':gl}
  (out/'studio-browser.json').write_text(json.dumps(record,indent=2));print(json.dumps({'checks':checks,'errors':errors,'gpu':gl},indent=2))
  if errors or any(not c['passed'] for c in checks):raise SystemExit(1)
 finally:
  x.terminate();server.shutdown();server.server_close();server.state.pool.shutdown(wait=True)
if __name__=='__main__':main()
