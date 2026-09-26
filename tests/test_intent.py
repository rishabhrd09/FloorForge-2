import pytest,math,json
from floorforge.model import *
from floorforge.intent import fuse,parse_text

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
    r=fuse(p);assert r['values']['bedrooms']==3;assert len(r['sources'])==4;assert r['provenance']['bedrooms']['selected']==['plan']

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
