import pytest,math,json
from floorforge.model import *
from floorforge.intent import fuse,parse_text,derive_setbacks

@pytest.mark.parametrize('bearing',range(0,360,45))
def test_orientation_basis(bearing):
    for e,n in [(1,0),(0,1),(.3,-.8)]:
        x,y=enu_to_local(e,n,bearing);ee,nn=local_to_enu(x,y,bearing)
        assert abs(ee-e)<1e-9 and abs(nn-n)<1e-9
    e,n=local_to_enu(0,-1,bearing)
    assert abs(e-math.sin(math.radians(bearing)))<1e-9
    assert abs(n-math.cos(math.radians(bearing)))<1e-9

@pytest.mark.parametrize('key,value',[('width_mm',True),('width_mm',4999),('depth_mm',float('nan')),('storeys',3),('bedrooms',0),('budget_lakh',-1),('road_bearing_deg',360),('latitude',91),('longitude',200),('floor_height_mm',1000),('front_mm',-1),('style','unknown'),('solar_date','2026-02-30'),('parking','yes')])
def test_invalid_field_rejected(key,value):
    with pytest.raises(DesignError):fuse({'brief':{key:value}})

def test_source_precedence_and_archive():
    p={'brief':{'bedrooms':2},'sources':[{'id':'plan','kind':'plan','values':{'bedrooms':3}},{'id':'unused','kind':'edit','enabled':False,'values':{'bedrooms':4}}]}
    r=fuse(p);assert r['values']['bedrooms']==3;assert len(r['sources'])==5;assert r['provenance']['bedrooms']['selected']==['plan']
    assert [x['kind'] for x in r['sources']][:2]==['defaults','derived']

def test_equal_precedence_conflict_is_not_guessed():
    with pytest.raises(DesignError) as e:fuse({'sources':[{'id':'a','kind':'grid','values':{'storeys':1}},{'id':'b','kind':'plan','values':{'storeys':2}}]})
    assert e.value.code=='INPUT_CONFLICT'

def test_disabled_text_survives():
    r=fuse({'sources':[{'id':'ignored','kind':'text','values':{'bedrooms':7},'raw_text':'seven rooms','enabled':False}]})
    assert r['sources'][-1]['raw_text']=='seven rooms' and r['values']['bedrooms']==3

@pytest.mark.parametrize('bad',[{'bogus':1},{'sources':'bad'},{'brief':{'execute':'shell'}},{'attachments':[{'image':'pretend'}]}])
def test_unknown_fields_rejected(bad):
    with pytest.raises((DesignError,TypeError)):fuse(bad)

def test_text_supported_fields_and_unparsed_notice():
    r=parse_text('40x60 ft east-facing, 3 bedrooms, G+1, 65 lakh. A peaceful home for my family.')
    assert r['values']['width_mm']==12192 and r['values']['depth_mm']==18288
    assert r['values']['bedrooms']==3 and r['values']['storeys']==2
    assert 'peaceful' in r['raw_text'];assert r['unparsed_notice']

def test_floor_request_not_silently_promoted():
    assert fuse({'brief':{'storeys':1,'bedrooms':8}})['values']['storeys']==1

def test_cost_is_user_input_not_inferred():
    r=fuse({'brief':{'rate_low_inr_ft2':1800,'rate_high_inr_ft2':3000}})
    assert r['values']['rate_low_inr_ft2']==1800
    with pytest.raises(DesignError):fuse({'brief':{'rate_low_inr_ft2':4000,'rate_high_inr_ft2':2000}})


@pytest.mark.parametrize('text,expect',[
    ('We have a 30 by 40 site, north facing. Need 3BHK duplex with all bedrooms attached bathrooms, pooja room, car parking and open kitchen. Budget 80 lakhs. Vastu compliant please.',
     {'width_mm':9144,'depth_mm':12192,'road_bearing_deg':0.,'bedrooms':3,'storeys':2,'attached_baths':'all','pooja':True,'parking':True,'open_kitchen':True,'budget_lakh':80.,'vastu':'strict'}),
    ('1200 sq ft plot facing east, 2 bhk ground floor only, 2 bathrooms, budget Rs 45 lakh, no vastu',
     {'width_mm':9144,'depth_mm':12192,'road_bearing_deg':90.,'bedrooms':2,'storeys':1,'attached_baths':1,'budget_lakh':45.,'vastu':'off'}),
    ('200 gaj plot, G+1, 4 bedrooms with 3 attached toilets, 1.2 crore, road on the west, modern style elevation',
     {'width_mm':9144,'depth_mm':18288,'storeys':2,'bedrooms':4,'attached_baths':3,'budget_lakh':120.,'road_bearing_deg':270.,'style':'minimal'}),
    ('Plot 9m x 12m NE-facing. Master bedroom with attached bath. Separate kitchen. Front setback 3 m, side margin 1 m. Floor height 3.2 m.',
     {'width_mm':9000,'depth_mm':12000,'road_bearing_deg':45.,'attached_baths':1,'open_kitchen':False,'front_mm':3000,'left_mm':1000,'right_mm':1000,'floor_height_mm':3200}),
    ('bedroom 12x14 and living 15x18 on a 40x60 plot, south road, 4bhk, 5 baths, no pooja, no parking',
     {'width_mm':12192,'depth_mm':18288,'road_bearing_deg':180.,'bedrooms':4,'attached_baths':'all','pooja':False,'parking':False}),
    ('Budget 75,00,000. 30*50. west facing. strict vastu. kerala style house.',
     {'width_mm':9144,'depth_mm':15240,'road_bearing_deg':270.,'budget_lakh':75.,'vastu':'strict','style':'tropical'}),
])
def test_text_reads_how_people_write_a_brief(text,expect):
    r=parse_text(text)
    assert {k:r['values'].get(k) for k in expect}==expect


def test_text_reports_what_it_did_not_understand():
    r=parse_text('40x60 ft east-facing, 3 bedrooms. A home theatre and a courtyard with a swing.')
    assert r['reading']['not_understood']==['A home theatre and a courtyard with a swing']
    assert {k for u in r['reading']['understood'] for k in u['values']}>={'width_mm','depth_mm','road_bearing_deg','bedrooms'}
    g=parse_text('G+3 house, 20 x 30')
    assert g['values']['storeys']==2 and any('G+1' in a for a in g['reading']['assumptions'])
    assert any('feet' in a for a in g['reading']['assumptions'])


def test_setbacks_follow_the_plot_unless_stated():
    small,large=derive_setbacks(7620,10668),derive_setbacks(18288,27432)
    assert small['front_mm']<large['front_mm'] and small['left_mm']<large['left_mm']
    assert derive_setbacks(12192,18288,parking=True)['front_mm']==5500
    r=fuse({'brief':{'width_mm':9144,'depth_mm':12192}})
    assert r['provenance']['front_mm']['selected']==['derived-setbacks'] and r['values']['front_mm']==1800
    assert any('Open spaces set from the plot size' in n for n in r['notices'])
    stated=fuse({'brief':{'width_mm':9144,'depth_mm':12192,'front_mm':2500}})
    assert stated['values']['front_mm']==2500 and stated['provenance']['front_mm']['selected']==['quick-survey']
    assert fuse({'text':'30x40 plot, front setback 2 m'})['values']['front_mm']==2000
