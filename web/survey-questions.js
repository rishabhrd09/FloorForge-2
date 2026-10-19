/* Each enabled answer has a model target and a stated consumer. */
'use strict';
const CompassSurvey = {
 foundation:[
  {id:'road',title:'Which side of your plot has the main road?',field:'road_bearing_deg',type:'choice',choices:[['North',0],['North-east',45],['East',90],['South-east',135],['South',180],['South-west',225],['West',270],['North-west',315]],consumer:'orientation, solar and Vastu',effect:'applied'},
  {id:'frontage',title:'How wide is the plot along the road?',field:'width_mm',type:'length',presets:[20,25,30,35,40,50,60],consumer:'buildable envelope',effect:'applied'},
  {id:'depth',title:'How deep is it from road to back?',field:'depth_mm',type:'length',presets:[30,40,50,60,70,80,100],consumer:'buildable envelope',effect:'applied'},
  {id:'context',title:'What surrounds your plot?',field:'context',type:'choice',site:true,choices:[['Choose later','unknown'],['Middle plot','middle'],['Corner plot','corner'],['Three sides open','three-open'],['Independent','independent']],consumer:'site notes; no exposure or second road is inferred',effect:'note only'},
  {id:'floors',title:'How many occupied floors?',field:'storeys',type:'choice',choices:[['Ground only',1],['Ground + First',2],['Ground + First + Second',3]],consumer:'floor scope and linked stairs',effect:'applied'},
  {id:'bedrooms',title:'How many bedrooms do you need?',field:'bedrooms',type:'count',consumer:'required room identities; zero bedrooms is supported',effect:'applied'},
  {id:'gate',title:'Where should the main gate be?',field:'gate',site:true,type:'choice',choices:[['Let the planner choose','planner'],['Left','left',true],['Center','center',true],['Right','right',true]],consumer:'existing site path chooses the gate; custom positions await the site compiler extension',effect:'applied'},
  {id:'density',title:'Choose your room grid',field:'grid',type:'choice',density:true,choices:[],consumer:'Across × deep; more cells give finer placement within the same plot',effect:'applied'}
 ],
 followups:[
  {id:'room-programme',title:'Which rooms belong on each floor?',target:'rooms',consumer:'required room instances',effect:'applied'},
  {id:'relationships',title:'Which rooms should connect?',target:'connections',consumer:'doors, cased or glazed openings, direct bathroom attachment',effect:'applied'},
  {id:'entry',title:'Where should the main door lead?',target:'site.entryRoomId',consumer:'public ground-floor entry opening',effect:'applied'},
  {id:'sizes',title:'Any preferred clear room sizes?',target:'rooms.target',consumer:'target comparison or blocking size lock',effect:'preference checked'},
  {id:'passage',title:'How wide should this route stay?',target:'requirements.access-width',consumer:'polygon neck and clear width checks',effect:'applied'},
  {id:'stairs',title:'Which staircase links these floors?',target:'stairLinks',consumer:'existing coordinated stair compiler',effect:'applied'},
  {id:'notes',title:'Any other requests?',target:'requirements.note',consumer:'saved notes and input coverage; no automatic modelling',effect:'note only'}
 ]
};
if(typeof module!=='undefined')module.exports=CompassSurvey;
