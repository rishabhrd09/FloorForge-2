"""Source-preserving fusion. Uninterpreted material stays visible, not silently applied."""
from __future__ import annotations
from .model import *
import re, datetime


def parse_text(text: str) -> dict:
    if not isinstance(text,str) or len(text)>20000:
        raise DesignError('TEXT_LIMIT','Description must be text, at most 20,000 characters.')
    s=text.lower(); values={}; spans=[]
    def take(pattern, transform):
        for m in re.finditer(pattern,s):
            values.update(transform(m)); spans.append((m.start(),m.end()))
    take(r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(ft|feet|m|metres|meters)\b',
         lambda m: {'width_mm':round(float(m[1])*(304.8 if m[3] in ('ft','feet') else 1000)),
                    'depth_mm':round(float(m[2])*(304.8 if m[3] in ('ft','feet') else 1000))})
    take(r'\b([1-8])\s*(?:bhk|bedrooms?|beds?)\b',lambda m:{'bedrooms':int(m[1])})
    take(r'\bg\s*\+\s*([1-3])\b',lambda m:{'storeys':int(m[1])+1})
    take(r'\bground[ -](?:floor[ -])?only\b|\bsingle[ -]storey\b',lambda m:{'storeys':1})
    dirs={'north':0.,'east':90.,'south':180.,'west':270.,'north-east':45.,'south-east':135.,'south-west':225.,'north-west':315.}
    take(r'\b(north-east|south-east|south-west|north-west|north|east|south|west)[ -]facing\b',lambda m:{'road_bearing_deg':dirs[m[1]]})
    take(r'\b(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac)\b',lambda m:{'budget_lakh':float(m[1])})
    take(r'\b(no parking|without parking)\b',lambda m:{'parking':False})
    if not re.search(r'no parking|without parking',s):
        take(r'\b(car parking|one car|parking)\b',lambda m:{'parking':True})
    take(r'\b(open kitchen|open-plan kitchen)\b',lambda m:{'open_kitchen':True})
    take(r'\bclosed kitchen\b',lambda m:{'open_kitchen':False})
    for style in STYLES:
        take(r'\b'+style+r'\b',lambda m,key=style:{'style':key})
    return {'values':values,'raw_text':text,'unparsed_notice':
        'Only the listed structured fields were extracted. Other prose remains a reference; it is not a satisfied constraint.',
        'matched_spans':spans}


def validate_values(values: dict) -> dict:
    unknown=set(values)-set(DEFAULTS)
    if unknown: raise DesignError('UNKNOWN_FIELD','Unsupported structured fields: '+', '.join(sorted(unknown)))
    d={**DEFAULTS,**values}
    ints={'width_mm':(5000,50000),'depth_mm':(6500,60000),'bedrooms':(1,8),'storeys':(1,2),
          'front_mm':(0,15000),'rear_mm':(0,10000),'left_mm':(0,10000),'right_mm':(0,10000),
          'plinth_mm':(0,900),'floor_height_mm':(2950,3600),'variant':(0,2),'seed':(0,2147483647)}
    for k,(lo,hi) in ints.items():
        if type(d[k]) is not int or not lo<=d[k]<=hi:
            raise DesignError('FIELD_RANGE',f'{k} must be an integer between {lo} and {hi}.')
    nums={'road_bearing_deg':(0,359.999999),'budget_lakh':(.1,100000),'latitude':(-89,89),
          'longitude':(-180,180),'timezone_hours':(-12,14),'solar_hour':(0,24),
          'rate_low_inr_ft2':(0,100000),'rate_high_inr_ft2':(0,100000),'cost_contingency_pct':(0,100)}
    for k,(lo,hi) in nums.items():
        v=d[k]
        if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or not lo<=v<=hi:
            raise DesignError('FIELD_RANGE',f'{k} must be a finite number between {lo} and {hi}.')
    if d['rate_low_inr_ft2']>d['rate_high_inr_ft2']:
        raise DesignError('RATE_ORDER','Low scenario rate must not exceed high scenario rate.')
    for k in ('parking','pooja','eldercare','open_kitchen'):
        if type(d[k]) is not bool: raise DesignError('FIELD_TYPE',f'{k} must be a boolean.')
    for key, choices in [('style',list(STYLES)),('exterior_theme',['current','warm_modern_minimal','tropical_verandah','earth_terracotta']),
                         ('interior_theme',['current','warm_contemporary','quiet_minimal','earthy_modern_indian']),
                         ('change_policy',['finish_only','exterior_refinement','spatial_redesign']),
                         ('finish',['economy','standard','premium']),('vastu',['off','flexible','moderate','strict']),
                         ('soil',['unknown','black-cotton','rocky','sandy','alluvial','red-laterite','murrum'])]:
        if d[key] not in choices: raise DesignError('FIELD_CHOICE',f'Invalid {key}.')
    if type(d['interior_layout_locked']) is not bool:
        raise DesignError('FIELD_TYPE','interior_layout_locked must be a boolean.')
    if not isinstance(d['theme_version'],str) or not 1<=len(d['theme_version'])<=32:
        raise DesignError('FIELD_TYPE','theme_version must be a non-empty string of at most 32 characters.')
    if not isinstance(d['title'],str) or not 1<=len(d['title'])<=120: raise DesignError('TITLE','Use a title of 1-120 characters.')
    try: datetime.date.fromisoformat(d['solar_date'])
    except (TypeError,ValueError): raise DesignError('SOLAR_DATE','Use a valid ISO calendar date.')
    if d['eldercare']:
        # Preserve request, but do not call a standard room an ICU or accessible space.
        pass
    return d


def fuse(payload: dict) -> dict:
    if not isinstance(payload,dict): raise DesignError('INPUT_OBJECT','Expected a project object.')
    if set(payload)-{'schema','sources','brief','text','grid','attachments','notes'}:
        raise DesignError('PROJECT_FIELDS','Unknown project top-level fields.')
    brief_input=payload.get('brief') if isinstance(payload.get('brief'),dict) else {}
    defaults=dict(DEFAULTS)
    # Projects written before the exterior upgrade must retain their current
    # appearance until the owner explicitly selects an upgrade.
    if 'exterior_theme' not in brief_input and payload.get('schema')!='floorforge.project/0.3':
        defaults['exterior_theme']='current'
    sources=[{'id':'defaults','kind':'defaults','enabled':True,'values':defaults}]
    if payload.get('brief') is not None:
        sources.append({'id':'quick-survey','kind':'survey','enabled':True,'values':payload['brief']})
    if payload.get('text'):
        p=parse_text(payload['text']); sources.append({'id':'description','kind':'text','enabled':True,**p})
    extra=payload.get('sources',[])
    if not isinstance(extra,list):raise DesignError('SOURCE_SCHEMA','Sources must be a list.')
    sources += extra
    if not isinstance(sources,list) or len(sources)>64: raise DesignError('SOURCE_LIMIT','Maximum 64 input sources.')
    seen=set(); notices=[]
    for src in sources:
        if not isinstance(src,dict) or set(src)-{'id','kind','enabled','values','raw_text','unparsed_notice','matched_spans','reference'}:
            raise DesignError('SOURCE_SCHEMA','Invalid source record.')
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',str(src.get('id',''))) or src['id'] in seen:
            raise DesignError('SOURCE_ID','Source IDs must be unique, safe identifiers.')
        seen.add(src['id'])
        if src.get('kind') not in SOURCE_PRIORITY or type(src.get('enabled',True)) is not bool:
            raise DesignError('SOURCE_SCHEMA','Unknown source kind or invalid Used/Off value.')
        if not isinstance(src.get('values',{}),dict): raise DesignError('SOURCE_VALUES','Source values must be an object.')
        if set(src.get('values',{}))-set(DEFAULTS): raise DesignError('UNKNOWN_FIELD','A source contains unsupported fields.')
        try: canonical(src)
        except (ValueError,TypeError) as exc:
            raise DesignError('SOURCE_JSON','Sources must contain finite JSON data; NaN and infinity are not permitted.') from exc
        if src.get('unparsed_notice'): notices.append(src['unparsed_notice'])
    out={};provenance={};conflicts=[]
    for key in DEFAULTS:
        candidates=[s for s in sources if s.get('enabled',True) and key in s.get('values',{})]
        rank=max(SOURCE_PRIORITY[s['kind']] for s in candidates)
        chosen=[s for s in candidates if SOURCE_PRIORITY[s['kind']]==rank]
        if len({canonical(s['values'][key]) for s in chosen})>1:
            conflicts.append({'field':key,'sources':[s['id'] for s in chosen]})
            continue
        out[key]=chosen[0]['values'][key]
        provenance[key]={'value':out[key],'selected':[s['id'] for s in chosen],
                         'superseded':[s['id'] for s in candidates if s not in chosen]}
    if conflicts: raise DesignError('INPUT_CONFLICT','Equal-priority inputs disagree. Resolve them before generating.',conflicts)
    out=validate_values(out)
    attachments=payload.get('attachments',[])
    if not isinstance(attachments,list) or len(attachments)>12: raise DesignError('ATTACHMENT_LIMIT','Maximum 12 reference records.')
    for a in attachments:
        if not isinstance(a,dict) or set(a)-{'name','kind','sha256','note'}:
            raise DesignError('ATTACHMENT_SCHEMA','References contain name, kind, hash and note only; images stay on your device.')
    if attachments: notices.append('Uploaded images are references only until manually traced; automatic OCR/CV recognition is not implemented.')
    if out['eldercare']: notices.append('Eldercare request preserved. Specialist care-room and step-free access design require professional review; this generator does not certify them.')
    notices += ['Setbacks are user-editable design assumptions, not verified municipal byelaws.',
                'Cost rates are editable illustrative scenarios, not researched local quotations.']
    return {'values':out,'provenance':provenance,'sources':sources,'grid':payload.get('grid'),
            'attachments':attachments,'notes':payload.get('notes',''),'notices':notices,
            'schema':'floorforge.intent/0.2','orientation':'Road at local -Y; bearing is the outward road-facing true azimuth.'}
