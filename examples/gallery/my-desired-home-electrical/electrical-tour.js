(()=>{var ta=1;var ea=3,Cr=0,hi=1,ue=2;var na=1;var ia=100;var sa=204,ra=205;var rr=0,or=1,ar=2,Xi=3,lr=4,cr=5,ur=6,hr=7,Ir=0,oa=1,aa=2;var Pr=1,Lr=2,Dr=3,Nr=4,Ur=5,Fr=6,Br=7;var Or=300,la=301,kr=302;var ca=306,_e=1e3,Gn=1001,dr=1002,fr=1003;var ua=1006;var ha=1008;var zr=1009;var Hr=1015;var da=1023;var fa=1028;var Zn=2300,$i=2301,Vi=2302,pr=2303,mr=2400,gr=2401,xr=2402;var pa=0;var Vr="",Bt="srgb",_r="srgb-linear",yr="linear",Gi="srgb";var Wi=7680;var ma=519;var ga=35044;var Re=2e3,Jn=2001;function ul(o){for(let t=o.length-1;t>=0;--t)if(o[t]>=65535)return!0;return!1}function hl(o){return ArrayBuffer.isView(o)&&!(o instanceof DataView)}function vr(o){return document.createElementNS("http://www.w3.org/1999/xhtml",o)}var Mo={},qi=null;function xa(o){let t=o[0];if(typeof t=="string"&&t.startsWith("TSL:")){let e=o[1];e&&e.isStackTrace?o[0]+=" "+e.getLocation():o[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return o}function St(...o){o=xa(o);let t="THREE."+o.shift();if(qi)qi("warn",t,...o);else{let e=o[0];e&&e.isStackTrace?console.warn(e.getError(t)):console.warn(t,...o)}}function gt(...o){o=xa(o);let t="THREE."+o.shift();if(qi)qi("error",t,...o);else{let e=o[0];e&&e.isStackTrace?console.error(e.getError(t)):console.error(t,...o)}}function bn(...o){let t=o.join(" ");t in Mo||(Mo[t]=!0,St(...o))}var dl={[rr]:or,[ar]:ur,[lr]:hr,[Xi]:cr,[or]:rr,[ur]:ar,[hr]:lr,[cr]:Xi},Ce=class{addEventListener(t,e){this._listeners===void 0&&(this._listeners={});let n=this._listeners;n[t]===void 0&&(n[t]=[]),n[t].indexOf(e)===-1&&n[t].push(e)}hasEventListener(t,e){let n=this._listeners;return n===void 0?!1:n[t]!==void 0&&n[t].indexOf(e)!==-1}removeEventListener(t,e){let n=this._listeners;if(n===void 0)return;let i=n[t];if(i!==void 0){let s=i.indexOf(e);s!==-1&&i.splice(s,1)}}dispatchEvent(t){let e=this._listeners;if(e===void 0)return;let n=e[t.type];if(n!==void 0){t.target=this;let i=n.slice(0);for(let s=0,r=i.length;s<r;s++)i[s].call(this,t);t.target=null}}},Dt=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],So=1234567,Xn=Math.PI/180,wn=180/Math.PI;function je(){let o=Math.random()*4294967295|0,t=Math.random()*4294967295|0,e=Math.random()*4294967295|0,n=Math.random()*4294967295|0;return(Dt[o&255]+Dt[o>>8&255]+Dt[o>>16&255]+Dt[o>>24&255]+"-"+Dt[t&255]+Dt[t>>8&255]+"-"+Dt[t>>16&15|64]+Dt[t>>24&255]+"-"+Dt[e&63|128]+Dt[e>>8&255]+"-"+Dt[e>>16&255]+Dt[e>>24&255]+Dt[n&255]+Dt[n>>8&255]+Dt[n>>16&255]+Dt[n>>24&255]).toLowerCase()}function Q(o,t,e){return Math.max(t,Math.min(e,o))}function Gr(o,t){return(o%t+t)%t}function fl(o,t,e,n,i){return n+(o-t)*(i-n)/(e-t)}function pl(o,t,e){return o!==t?(e-o)/(t-o):0}function $n(o,t,e){return(1-e)*o+e*t}function ml(o,t,e,n){return $n(o,t,1-Math.exp(-e*n))}function gl(o,t=1){return t-Math.abs(Gr(o,t*2)-t)}function xl(o,t,e){return o<=t?0:o>=e?1:(o=(o-t)/(e-t),o*o*(3-2*o))}function _l(o,t,e){return o<=t?0:o>=e?1:(o=(o-t)/(e-t),o*o*o*(o*(o*6-15)+10))}function yl(o,t){return o+Math.floor(Math.random()*(t-o+1))}function vl(o,t){return o+Math.random()*(t-o)}function Ml(o){return o*(.5-Math.random())}function Sl(o){o!==void 0&&(So=o);let t=So+=1831565813;return t=Math.imul(t^t>>>15,t|1),t^=t+Math.imul(t^t>>>7,t|61),((t^t>>>14)>>>0)/4294967296}function bl(o){return o*Xn}function El(o){return o*wn}function wl(o){return o>0&&Number.isInteger(o)&&2**Math.round(Math.log2(o))===o}function Tl(o){return Math.pow(2,Math.ceil(Math.log(o)/Math.LN2))}function Al(o){return Math.pow(2,Math.floor(Math.log(o)/Math.LN2))}function Rl(o,t,e,n,i){let s=Math.cos,r=Math.sin,a=s(e/2),l=r(e/2),c=s((t+n)/2),u=r((t+n)/2),d=s((t-n)/2),h=r((t-n)/2),f=s((n-t)/2),p=r((n-t)/2);switch(i){case"XYX":o.set(a*u,l*d,l*h,a*c);break;case"YZY":o.set(l*h,a*u,l*d,a*c);break;case"ZXZ":o.set(l*d,l*h,a*u,a*c);break;case"XZX":o.set(a*u,l*p,l*f,a*c);break;case"YXY":o.set(l*f,a*u,l*p,a*c);break;case"ZYZ":o.set(l*p,l*f,a*u,a*c);break;default:St("MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+i)}}function Sn(o,t){switch(t.constructor){case Float32Array:return o;case Uint32Array:return o/4294967295;case Uint16Array:return o/65535;case Uint8Array:case Uint8ClampedArray:return o/255;case Int32Array:return Math.max(o/2147483647,-1);case Int16Array:return Math.max(o/32767,-1);case Int8Array:return Math.max(o/127,-1);default:throw new Error("THREE.MathUtils: Invalid component type.")}}function Ft(o,t){switch(t.constructor){case Float32Array:return o;case Uint32Array:return Math.round(o*4294967295);case Uint16Array:return Math.round(o*65535);case Uint8Array:case Uint8ClampedArray:return Math.round(o*255);case Int32Array:return Math.round(o*2147483647);case Int16Array:return Math.round(o*32767);case Int8Array:return Math.round(o*127);default:throw new Error("THREE.MathUtils: Invalid component type.")}}var Wr={DEG2RAD:Xn,RAD2DEG:wn,generateUUID:je,clamp:Q,euclideanModulo:Gr,mapLinear:fl,inverseLerp:pl,lerp:$n,damp:ml,pingpong:gl,smoothstep:xl,smootherstep:_l,randInt:yl,randFloat:vl,randFloatSpread:Ml,seededRandom:Sl,degToRad:bl,radToDeg:El,isPowerOfTwo:wl,ceilPowerOfTwo:Tl,floorPowerOfTwo:Al,setQuaternionFromProperEuler:Rl,normalize:Ft,denormalize:Sn},Yr=class Yr{constructor(t=0,e=0){this.x=t,this.y=e}get width(){return this.x}set width(t){this.x=t}get height(){return this.y}set height(t){this.y=t}set(t,e){return this.x=t,this.y=e,this}setScalar(t){return this.x=t,this.y=t,this}setX(t){return this.x=t,this}setY(t){return this.y=t,this}setComponent(t,e){switch(t){case 0:this.x=e;break;case 1:this.y=e;break;default:throw new Error("THREE.Vector2: index is out of range: "+t)}return this}getComponent(t){switch(t){case 0:return this.x;case 1:return this.y;default:throw new Error("THREE.Vector2: index is out of range: "+t)}}clone(){return new this.constructor(this.x,this.y)}copy(t){return this.x=t.x,this.y=t.y,this}add(t){return this.x+=t.x,this.y+=t.y,this}addScalar(t){return this.x+=t,this.y+=t,this}addVectors(t,e){return this.x=t.x+e.x,this.y=t.y+e.y,this}addScaledVector(t,e){return this.x+=t.x*e,this.y+=t.y*e,this}sub(t){return this.x-=t.x,this.y-=t.y,this}subScalar(t){return this.x-=t,this.y-=t,this}subVectors(t,e){return this.x=t.x-e.x,this.y=t.y-e.y,this}multiply(t){return this.x*=t.x,this.y*=t.y,this}multiplyScalar(t){return this.x*=t,this.y*=t,this}divide(t){return this.x/=t.x,this.y/=t.y,this}divideScalar(t){return this.multiplyScalar(1/t)}applyMatrix3(t){let e=this.x,n=this.y,i=t.elements;return this.x=i[0]*e+i[3]*n+i[6],this.y=i[1]*e+i[4]*n+i[7],this}min(t){return this.x=Math.min(this.x,t.x),this.y=Math.min(this.y,t.y),this}max(t){return this.x=Math.max(this.x,t.x),this.y=Math.max(this.y,t.y),this}clamp(t,e){return this.x=Q(this.x,t.x,e.x),this.y=Q(this.y,t.y,e.y),this}clampScalar(t,e){return this.x=Q(this.x,t,e),this.y=Q(this.y,t,e),this}clampLength(t,e){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Q(n,t,e))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(t){return this.x*t.x+this.y*t.y}cross(t){return this.x*t.y-this.y*t.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(t){let e=Math.sqrt(this.lengthSq()*t.lengthSq());if(e===0)return Math.PI/2;let n=this.dot(t)/e;return Math.acos(Q(n,-1,1))}distanceTo(t){return Math.sqrt(this.distanceToSquared(t))}distanceToSquared(t){let e=this.x-t.x,n=this.y-t.y;return e*e+n*n}manhattanDistanceTo(t){return Math.abs(this.x-t.x)+Math.abs(this.y-t.y)}setLength(t){return this.normalize().multiplyScalar(t)}lerp(t,e){return this.x+=(t.x-this.x)*e,this.y+=(t.y-this.y)*e,this}lerpVectors(t,e,n){return this.x=t.x+(e.x-t.x)*n,this.y=t.y+(e.y-t.y)*n,this}equals(t){return t.x===this.x&&t.y===this.y}fromArray(t,e=0){return this.x=t[e],this.y=t[e+1],this}toArray(t=[],e=0){return t[e]=this.x,t[e+1]=this.y,t}fromBufferAttribute(t,e){return this.x=t.getX(e),this.y=t.getY(e),this}rotateAround(t,e){let n=Math.cos(e),i=Math.sin(e),s=this.x-t.x,r=this.y-t.y;return this.x=s*n-r*i+t.x,this.y=s*i+r*n+t.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}};Yr.prototype.isVector2=!0;var O=Yr,kt=class{constructor(t=0,e=0,n=0,i=1){this.isQuaternion=!0,this._x=t,this._y=e,this._z=n,this._w=i}static slerpFlat(t,e,n,i,s,r,a){let l=n[i+0],c=n[i+1],u=n[i+2],d=n[i+3],h=s[r+0],f=s[r+1],p=s[r+2],m=s[r+3];if(d!==m||l!==h||c!==f||u!==p){let x=l*h+c*f+u*p+d*m;x<0&&(h=-h,f=-f,p=-p,m=-m,x=-x);let v=1-a;if(x<.9995){let S=Math.acos(x),y=Math.sin(S);v=Math.sin(v*S)/y,a=Math.sin(a*S)/y,l=l*v+h*a,c=c*v+f*a,u=u*v+p*a,d=d*v+m*a}else{l=l*v+h*a,c=c*v+f*a,u=u*v+p*a,d=d*v+m*a;let S=1/Math.sqrt(l*l+c*c+u*u+d*d);l*=S,c*=S,u*=S,d*=S}}t[e]=l,t[e+1]=c,t[e+2]=u,t[e+3]=d}static multiplyQuaternionsFlat(t,e,n,i,s,r){let a=n[i],l=n[i+1],c=n[i+2],u=n[i+3],d=s[r],h=s[r+1],f=s[r+2],p=s[r+3];return t[e]=a*p+u*d+l*f-c*h,t[e+1]=l*p+u*h+c*d-a*f,t[e+2]=c*p+u*f+a*h-l*d,t[e+3]=u*p-a*d-l*h-c*f,t}get x(){return this._x}set x(t){this._x=t,this._onChangeCallback()}get y(){return this._y}set y(t){this._y=t,this._onChangeCallback()}get z(){return this._z}set z(t){this._z=t,this._onChangeCallback()}get w(){return this._w}set w(t){this._w=t,this._onChangeCallback()}set(t,e,n,i){return this._x=t,this._y=e,this._z=n,this._w=i,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(t){return this._x=t.x,this._y=t.y,this._z=t.z,this._w=t.w,this._onChangeCallback(),this}setFromEuler(t,e=!0){let n=t._x,i=t._y,s=t._z,r=t._order,a=Math.cos,l=Math.sin,c=a(n/2),u=a(i/2),d=a(s/2),h=l(n/2),f=l(i/2),p=l(s/2);switch(r){case"XYZ":this._x=h*u*d+c*f*p,this._y=c*f*d-h*u*p,this._z=c*u*p+h*f*d,this._w=c*u*d-h*f*p;break;case"YXZ":this._x=h*u*d+c*f*p,this._y=c*f*d-h*u*p,this._z=c*u*p-h*f*d,this._w=c*u*d+h*f*p;break;case"ZXY":this._x=h*u*d-c*f*p,this._y=c*f*d+h*u*p,this._z=c*u*p+h*f*d,this._w=c*u*d-h*f*p;break;case"ZYX":this._x=h*u*d-c*f*p,this._y=c*f*d+h*u*p,this._z=c*u*p-h*f*d,this._w=c*u*d+h*f*p;break;case"YZX":this._x=h*u*d+c*f*p,this._y=c*f*d+h*u*p,this._z=c*u*p-h*f*d,this._w=c*u*d-h*f*p;break;case"XZY":this._x=h*u*d-c*f*p,this._y=c*f*d-h*u*p,this._z=c*u*p+h*f*d,this._w=c*u*d+h*f*p;break;default:St("Quaternion: .setFromEuler() encountered an unknown order: "+r)}return e===!0&&this._onChangeCallback(),this}setFromAxisAngle(t,e){let n=e/2,i=Math.sin(n);return this._x=t.x*i,this._y=t.y*i,this._z=t.z*i,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(t){let e=t.elements,n=e[0],i=e[4],s=e[8],r=e[1],a=e[5],l=e[9],c=e[2],u=e[6],d=e[10],h=n+a+d;if(h>0){let f=.5/Math.sqrt(h+1);this._w=.25/f,this._x=(u-l)*f,this._y=(s-c)*f,this._z=(r-i)*f}else if(n>a&&n>d){let f=2*Math.sqrt(1+n-a-d);this._w=(u-l)/f,this._x=.25*f,this._y=(i+r)/f,this._z=(s+c)/f}else if(a>d){let f=2*Math.sqrt(1+a-n-d);this._w=(s-c)/f,this._x=(i+r)/f,this._y=.25*f,this._z=(l+u)/f}else{let f=2*Math.sqrt(1+d-n-a);this._w=(r-i)/f,this._x=(s+c)/f,this._y=(l+u)/f,this._z=.25*f}return this._onChangeCallback(),this}setFromUnitVectors(t,e){let n=t.dot(e)+1;return n<1e-8?(n=0,Math.abs(t.x)>Math.abs(t.z)?(this._x=-t.y,this._y=t.x,this._z=0,this._w=n):(this._x=0,this._y=-t.z,this._z=t.y,this._w=n)):(this._x=t.y*e.z-t.z*e.y,this._y=t.z*e.x-t.x*e.z,this._z=t.x*e.y-t.y*e.x,this._w=n),this.normalize()}angleTo(t){return 2*Math.acos(Math.abs(Q(this.dot(t),-1,1)))}rotateTowards(t,e){let n=this.angleTo(t);if(n===0)return this;let i=Math.min(1,e/n);return this.slerp(t,i),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(t){return this._x*t._x+this._y*t._y+this._z*t._z+this._w*t._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let t=this.length();return t===0?(this._x=0,this._y=0,this._z=0,this._w=1):(t=1/t,this._x=this._x*t,this._y=this._y*t,this._z=this._z*t,this._w=this._w*t),this._onChangeCallback(),this}multiply(t){return this.multiplyQuaternions(this,t)}premultiply(t){return this.multiplyQuaternions(t,this)}multiplyQuaternions(t,e){let n=t._x,i=t._y,s=t._z,r=t._w,a=e._x,l=e._y,c=e._z,u=e._w;return this._x=n*u+r*a+i*c-s*l,this._y=i*u+r*l+s*a-n*c,this._z=s*u+r*c+n*l-i*a,this._w=r*u-n*a-i*l-s*c,this._onChangeCallback(),this}slerp(t,e){let n=t._x,i=t._y,s=t._z,r=t._w,a=this.dot(t);a<0&&(n=-n,i=-i,s=-s,r=-r,a=-a);let l=1-e;if(a<.9995){let c=Math.acos(a),u=Math.sin(c);l=Math.sin(l*c)/u,e=Math.sin(e*c)/u,this._x=this._x*l+n*e,this._y=this._y*l+i*e,this._z=this._z*l+s*e,this._w=this._w*l+r*e,this._onChangeCallback()}else this._x=this._x*l+n*e,this._y=this._y*l+i*e,this._z=this._z*l+s*e,this._w=this._w*l+r*e,this.normalize();return this}slerpQuaternions(t,e,n){return this.copy(t).slerp(e,n)}random(){let t=2*Math.PI*Math.random(),e=2*Math.PI*Math.random(),n=Math.random(),i=Math.sqrt(1-n),s=Math.sqrt(n);return this.set(i*Math.sin(t),i*Math.cos(t),s*Math.sin(e),s*Math.cos(e))}equals(t){return t._x===this._x&&t._y===this._y&&t._z===this._z&&t._w===this._w}fromArray(t,e=0){return this._x=t[e],this._y=t[e+1],this._z=t[e+2],this._w=t[e+3],this._onChangeCallback(),this}toArray(t=[],e=0){return t[e]=this._x,t[e+1]=this._y,t[e+2]=this._z,t[e+3]=this._w,t}fromBufferAttribute(t,e){return this._x=t.getX(e),this._y=t.getY(e),this._z=t.getZ(e),this._w=t.getW(e),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(t){return this._onChangeCallback=t,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}},Zr=class Zr{constructor(t=0,e=0,n=0){this.x=t,this.y=e,this.z=n}set(t,e,n){return n===void 0&&(n=this.z),this.x=t,this.y=e,this.z=n,this}setScalar(t){return this.x=t,this.y=t,this.z=t,this}setX(t){return this.x=t,this}setY(t){return this.y=t,this}setZ(t){return this.z=t,this}setComponent(t,e){switch(t){case 0:this.x=e;break;case 1:this.y=e;break;case 2:this.z=e;break;default:throw new Error("THREE.Vector3: index is out of range: "+t)}return this}getComponent(t){switch(t){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("THREE.Vector3: index is out of range: "+t)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(t){return this.x=t.x,this.y=t.y,this.z=t.z,this}add(t){return this.x+=t.x,this.y+=t.y,this.z+=t.z,this}addScalar(t){return this.x+=t,this.y+=t,this.z+=t,this}addVectors(t,e){return this.x=t.x+e.x,this.y=t.y+e.y,this.z=t.z+e.z,this}addScaledVector(t,e){return this.x+=t.x*e,this.y+=t.y*e,this.z+=t.z*e,this}sub(t){return this.x-=t.x,this.y-=t.y,this.z-=t.z,this}subScalar(t){return this.x-=t,this.y-=t,this.z-=t,this}subVectors(t,e){return this.x=t.x-e.x,this.y=t.y-e.y,this.z=t.z-e.z,this}multiply(t){return this.x*=t.x,this.y*=t.y,this.z*=t.z,this}multiplyScalar(t){return this.x*=t,this.y*=t,this.z*=t,this}multiplyVectors(t,e){return this.x=t.x*e.x,this.y=t.y*e.y,this.z=t.z*e.z,this}applyEuler(t){return this.applyQuaternion(bo.setFromEuler(t))}applyAxisAngle(t,e){return this.applyQuaternion(bo.setFromAxisAngle(t,e))}applyMatrix3(t){let e=this.x,n=this.y,i=this.z,s=t.elements;return this.x=s[0]*e+s[3]*n+s[6]*i,this.y=s[1]*e+s[4]*n+s[7]*i,this.z=s[2]*e+s[5]*n+s[8]*i,this}applyNormalMatrix(t){return this.applyMatrix3(t).normalize()}applyMatrix4(t){let e=this.x,n=this.y,i=this.z,s=t.elements,r=1/(s[3]*e+s[7]*n+s[11]*i+s[15]);return this.x=(s[0]*e+s[4]*n+s[8]*i+s[12])*r,this.y=(s[1]*e+s[5]*n+s[9]*i+s[13])*r,this.z=(s[2]*e+s[6]*n+s[10]*i+s[14])*r,this}applyQuaternion(t){let e=this.x,n=this.y,i=this.z,s=t.x,r=t.y,a=t.z,l=t.w,c=2*(r*i-a*n),u=2*(a*e-s*i),d=2*(s*n-r*e);return this.x=e+l*c+r*d-a*u,this.y=n+l*u+a*c-s*d,this.z=i+l*d+s*u-r*c,this}project(t){return this.applyMatrix4(t.matrixWorldInverse).applyMatrix4(t.projectionMatrix)}unproject(t){return this.applyMatrix4(t.projectionMatrixInverse).applyMatrix4(t.matrixWorld)}transformDirection(t){let e=this.x,n=this.y,i=this.z,s=t.elements;return this.x=s[0]*e+s[4]*n+s[8]*i,this.y=s[1]*e+s[5]*n+s[9]*i,this.z=s[2]*e+s[6]*n+s[10]*i,this.normalize()}divide(t){return this.x/=t.x,this.y/=t.y,this.z/=t.z,this}divideScalar(t){return this.multiplyScalar(1/t)}min(t){return this.x=Math.min(this.x,t.x),this.y=Math.min(this.y,t.y),this.z=Math.min(this.z,t.z),this}max(t){return this.x=Math.max(this.x,t.x),this.y=Math.max(this.y,t.y),this.z=Math.max(this.z,t.z),this}clamp(t,e){return this.x=Q(this.x,t.x,e.x),this.y=Q(this.y,t.y,e.y),this.z=Q(this.z,t.z,e.z),this}clampScalar(t,e){return this.x=Q(this.x,t,e),this.y=Q(this.y,t,e),this.z=Q(this.z,t,e),this}clampLength(t,e){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Q(n,t,e))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(t){return this.x*t.x+this.y*t.y+this.z*t.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(t){return this.normalize().multiplyScalar(t)}lerp(t,e){return this.x+=(t.x-this.x)*e,this.y+=(t.y-this.y)*e,this.z+=(t.z-this.z)*e,this}lerpVectors(t,e,n){return this.x=t.x+(e.x-t.x)*n,this.y=t.y+(e.y-t.y)*n,this.z=t.z+(e.z-t.z)*n,this}cross(t){return this.crossVectors(this,t)}crossVectors(t,e){let n=t.x,i=t.y,s=t.z,r=e.x,a=e.y,l=e.z;return this.x=i*l-s*a,this.y=s*r-n*l,this.z=n*a-i*r,this}projectOnVector(t){let e=t.lengthSq();if(e===0)return this.set(0,0,0);let n=t.dot(this)/e;return this.copy(t).multiplyScalar(n)}projectOnPlane(t){return Ns.copy(this).projectOnVector(t),this.sub(Ns)}reflect(t){return this.sub(Ns.copy(t).multiplyScalar(2*this.dot(t)))}angleTo(t){let e=Math.sqrt(this.lengthSq()*t.lengthSq());if(e===0)return Math.PI/2;let n=this.dot(t)/e;return Math.acos(Q(n,-1,1))}distanceTo(t){return Math.sqrt(this.distanceToSquared(t))}distanceToSquared(t){let e=this.x-t.x,n=this.y-t.y,i=this.z-t.z;return e*e+n*n+i*i}manhattanDistanceTo(t){return Math.abs(this.x-t.x)+Math.abs(this.y-t.y)+Math.abs(this.z-t.z)}setFromSpherical(t){return this.setFromSphericalCoords(t.radius,t.phi,t.theta)}setFromSphericalCoords(t,e,n){let i=Math.sin(e)*t;return this.x=i*Math.sin(n),this.y=Math.cos(e)*t,this.z=i*Math.cos(n),this}setFromCylindrical(t){return this.setFromCylindricalCoords(t.radius,t.theta,t.y)}setFromCylindricalCoords(t,e,n){return this.x=t*Math.sin(e),this.y=n,this.z=t*Math.cos(e),this}setFromMatrixPosition(t){let e=t.elements;return this.x=e[12],this.y=e[13],this.z=e[14],this}setFromMatrixScale(t){let e=this.setFromMatrixColumn(t,0).length(),n=this.setFromMatrixColumn(t,1).length(),i=this.setFromMatrixColumn(t,2).length();return this.x=e,this.y=n,this.z=i,this}setFromMatrixColumn(t,e){return this.fromArray(t.elements,e*4)}setFromMatrix3Column(t,e){return this.fromArray(t.elements,e*3)}setFromEuler(t){return this.x=t._x,this.y=t._y,this.z=t._z,this}setFromColor(t){return this.x=t.r,this.y=t.g,this.z=t.b,this}equals(t){return t.x===this.x&&t.y===this.y&&t.z===this.z}fromArray(t,e=0){return this.x=t[e],this.y=t[e+1],this.z=t[e+2],this}toArray(t=[],e=0){return t[e]=this.x,t[e+1]=this.y,t[e+2]=this.z,t}fromBufferAttribute(t,e){return this.x=t.getX(e),this.y=t.getY(e),this.z=t.getZ(e),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){let t=Math.random()*Math.PI*2,e=Math.random()*2-1,n=Math.sqrt(1-e*e);return this.x=n*Math.cos(t),this.y=e,this.z=n*Math.sin(t),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}};Zr.prototype.isVector3=!0;var _=Zr,Ns=new _,bo=new kt,Jr=class Jr{constructor(t,e,n,i,s,r,a,l,c){this.elements=[1,0,0,0,1,0,0,0,1],t!==void 0&&this.set(t,e,n,i,s,r,a,l,c)}set(t,e,n,i,s,r,a,l,c){let u=this.elements;return u[0]=t,u[1]=i,u[2]=a,u[3]=e,u[4]=s,u[5]=l,u[6]=n,u[7]=r,u[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(t){let e=this.elements,n=t.elements;return e[0]=n[0],e[1]=n[1],e[2]=n[2],e[3]=n[3],e[4]=n[4],e[5]=n[5],e[6]=n[6],e[7]=n[7],e[8]=n[8],this}extractBasis(t,e,n){return t.setFromMatrix3Column(this,0),e.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(t){let e=t.elements;return this.set(e[0],e[4],e[8],e[1],e[5],e[9],e[2],e[6],e[10]),this}multiply(t){return this.multiplyMatrices(this,t)}premultiply(t){return this.multiplyMatrices(t,this)}multiplyMatrices(t,e){let n=t.elements,i=e.elements,s=this.elements,r=n[0],a=n[3],l=n[6],c=n[1],u=n[4],d=n[7],h=n[2],f=n[5],p=n[8],m=i[0],x=i[3],v=i[6],S=i[1],y=i[4],M=i[7],A=i[2],b=i[5],R=i[8];return s[0]=r*m+a*S+l*A,s[3]=r*x+a*y+l*b,s[6]=r*v+a*M+l*R,s[1]=c*m+u*S+d*A,s[4]=c*x+u*y+d*b,s[7]=c*v+u*M+d*R,s[2]=h*m+f*S+p*A,s[5]=h*x+f*y+p*b,s[8]=h*v+f*M+p*R,this}multiplyScalar(t){let e=this.elements;return e[0]*=t,e[3]*=t,e[6]*=t,e[1]*=t,e[4]*=t,e[7]*=t,e[2]*=t,e[5]*=t,e[8]*=t,this}determinant(){let t=this.elements,e=t[0],n=t[1],i=t[2],s=t[3],r=t[4],a=t[5],l=t[6],c=t[7],u=t[8];return e*r*u-e*a*c-n*s*u+n*a*l+i*s*c-i*r*l}invert(){let t=this.elements,e=t[0],n=t[1],i=t[2],s=t[3],r=t[4],a=t[5],l=t[6],c=t[7],u=t[8],d=u*r-a*c,h=a*l-u*s,f=c*s-r*l,p=e*d+n*h+i*f;if(p===0)return this.set(0,0,0,0,0,0,0,0,0);let m=1/p;return t[0]=d*m,t[1]=(i*c-u*n)*m,t[2]=(a*n-i*r)*m,t[3]=h*m,t[4]=(u*e-i*l)*m,t[5]=(i*s-a*e)*m,t[6]=f*m,t[7]=(n*l-c*e)*m,t[8]=(r*e-n*s)*m,this}transpose(){let t,e=this.elements;return t=e[1],e[1]=e[3],e[3]=t,t=e[2],e[2]=e[6],e[6]=t,t=e[5],e[5]=e[7],e[7]=t,this}getNormalMatrix(t){return this.setFromMatrix4(t).invert().transpose()}transposeIntoArray(t){let e=this.elements;return t[0]=e[0],t[1]=e[3],t[2]=e[6],t[3]=e[1],t[4]=e[4],t[5]=e[7],t[6]=e[2],t[7]=e[5],t[8]=e[8],this}setUvTransform(t,e,n,i,s,r,a){let l=Math.cos(s),c=Math.sin(s);return this.set(n*l,n*c,-n*(l*r+c*a)+r+t,-i*c,i*l,-i*(-c*r+l*a)+a+e,0,0,1),this}scale(t,e){return bn("Matrix3: .scale() is deprecated. Use .makeScale() instead."),this.premultiply(Us.makeScale(t,e)),this}rotate(t){return bn("Matrix3: .rotate() is deprecated. Use .makeRotation() instead."),this.premultiply(Us.makeRotation(-t)),this}translate(t,e){return bn("Matrix3: .translate() is deprecated. Use .makeTranslation() instead."),this.premultiply(Us.makeTranslation(t,e)),this}makeTranslation(t,e){return t.isVector2?this.set(1,0,t.x,0,1,t.y,0,0,1):this.set(1,0,t,0,1,e,0,0,1),this}makeRotation(t){let e=Math.cos(t),n=Math.sin(t);return this.set(e,-n,0,n,e,0,0,0,1),this}makeScale(t,e){return this.set(t,0,0,0,e,0,0,0,1),this}equals(t){let e=this.elements,n=t.elements;for(let i=0;i<9;i++)if(e[i]!==n[i])return!1;return!0}fromArray(t,e=0){for(let n=0;n<9;n++)this.elements[n]=t[n+e];return this}toArray(t=[],e=0){let n=this.elements;return t[e]=n[0],t[e+1]=n[1],t[e+2]=n[2],t[e+3]=n[3],t[e+4]=n[4],t[e+5]=n[5],t[e+6]=n[6],t[e+7]=n[7],t[e+8]=n[8],t}clone(){return new this.constructor().fromArray(this.elements)}};Jr.prototype.isMatrix3=!0;var nt=Jr,Us=new nt,Eo=new nt().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),wo=new nt().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function Cl(){let o={enabled:!0,workingColorSpace:_r,spaces:{},convert:function(i,s,r){return this.enabled===!1||s===r||!s||!r||(this.spaces[s].transfer===Gi&&(i.r=xe(i.r),i.g=xe(i.g),i.b=xe(i.b)),this.spaces[s].primaries!==this.spaces[r].primaries&&(i.applyMatrix3(this.spaces[s].toXYZ),i.applyMatrix3(this.spaces[r].fromXYZ)),this.spaces[r].transfer===Gi&&(i.r=En(i.r),i.g=En(i.g),i.b=En(i.b))),i},workingToColorSpace:function(i,s){return this.convert(i,this.workingColorSpace,s)},colorSpaceToWorking:function(i,s){return this.convert(i,s,this.workingColorSpace)},getPrimaries:function(i){return this.spaces[i].primaries},getTransfer:function(i){return i===Vr?yr:this.spaces[i].transfer},getToneMappingMode:function(i){return this.spaces[i].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(i,s=this.workingColorSpace){return i.fromArray(this.spaces[s].luminanceCoefficients)},define:function(i){Object.assign(this.spaces,i)},_getMatrix:function(i,s,r){return i.copy(this.spaces[s].toXYZ).multiply(this.spaces[r].fromXYZ)},_getDrawingBufferColorSpace:function(i){return this.spaces[i].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(i=this.workingColorSpace){return this.spaces[i].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(i,s){return bn("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),o.workingToColorSpace(i,s)},toWorkingColorSpace:function(i,s){return bn("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),o.colorSpaceToWorking(i,s)}},t=[.64,.33,.3,.6,.15,.06],e=[.2126,.7152,.0722],n=[.3127,.329];return o.define({[_r]:{primaries:t,whitePoint:n,transfer:yr,toXYZ:Eo,fromXYZ:wo,luminanceCoefficients:e,workingColorSpaceConfig:{unpackColorSpace:Bt},outputColorSpaceConfig:{drawingBufferColorSpace:Bt}},[Bt]:{primaries:t,whitePoint:n,transfer:Gi,toXYZ:Eo,fromXYZ:wo,luminanceCoefficients:e,outputColorSpaceConfig:{drawingBufferColorSpace:Bt}}}),o}var jt=Cl();function xe(o){return o<.04045?o*.0773993808:Math.pow(o*.9478672986+.0521327014,2.4)}function En(o){return o<.0031308?o*12.92:1.055*Math.pow(o,.41666)-.055}var ln,Yi=class{static getDataURL(t,e="image/png"){if(/^data:/i.test(t.src)||typeof HTMLCanvasElement>"u")return t.src;let n;if(t instanceof HTMLCanvasElement)n=t;else{ln===void 0&&(ln=vr("canvas")),ln.width=t.width,ln.height=t.height;let i=ln.getContext("2d");t instanceof ImageData?i.putImageData(t,0,0):i.drawImage(t,0,0,t.width,t.height),n=ln}return n.toDataURL(e)}static sRGBToLinear(t){if(typeof HTMLImageElement<"u"&&t instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&t instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&t instanceof ImageBitmap){let e=vr("canvas");e.width=t.width,e.height=t.height;let n=e.getContext("2d");n.drawImage(t,0,0,t.width,t.height);let i=n.getImageData(0,0,t.width,t.height),s=i.data;for(let r=0;r<s.length;r++)s[r]=xe(s[r]/255)*255;return n.putImageData(i,0,0),e}else if(t.data){let e=t.data.slice(0);for(let n=0;n<e.length;n++)e instanceof Uint8Array||e instanceof Uint8ClampedArray?e[n]=Math.floor(xe(e[n]/255)*255):e[n]=xe(e[n]);return{data:e,width:t.width,height:t.height}}else return St("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),t}},Il=0,Zi=class{constructor(t=null){this.isTextureSource=!0,Object.defineProperty(this,"id",{value:Il++}),this.uuid=je(),this.data=t,this.dataReady=!0,this.version=0}getSize(t){let e=this.data;return typeof HTMLVideoElement<"u"&&e instanceof HTMLVideoElement?t.set(e.videoWidth,e.videoHeight,0):typeof VideoFrame<"u"&&e instanceof VideoFrame?t.set(e.displayWidth,e.displayHeight,0):e!==null?t.set(e.width,e.height,e.depth||0):t.set(0,0,0),t}set needsUpdate(t){t===!0&&this.version++}toJSON(t){let e=t===void 0||typeof t=="string";if(!e&&t.images[this.uuid]!==void 0)return t.images[this.uuid];let n={uuid:this.uuid,url:""},i=this.data;if(i!==null){let s;if(Array.isArray(i)){s=[];for(let r=0,a=i.length;r<a;r++)i[r].isDataTexture?s.push(Fs(i[r].image)):s.push(Fs(i[r]))}else s=Fs(i);n.url=s}return e||(t.images[this.uuid]=n),n}};function Fs(o){return typeof HTMLImageElement<"u"&&o instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&o instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&o instanceof ImageBitmap?Yi.getDataURL(o):o.data?{data:Array.from(o.data),width:o.width,height:o.height,type:o.data.constructor.name}:(St("Texture: Unable to serialize Texture."),{})}var Pl=0,Bs=new _,Ie=class o extends Ce{constructor(t=o.DEFAULT_IMAGE,e=o.DEFAULT_MAPPING,n=Gn,i=Gn,s=ua,r=ha,a=da,l=zr,c=o.DEFAULT_ANISOTROPY,u=Vr){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Pl++}),this.uuid=je(),this.name="",this.source=new Zi(t),this.mipmaps=[],this.mapping=e,this.channel=0,this.wrapS=n,this.wrapT=i,this.magFilter=s,this.minFilter=r,this.anisotropy=c,this.format=a,this.internalFormat=null,this.type=l,this.offset=new O(0,0),this.repeat=new O(1,1),this.center=new O(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new nt,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=u,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(t&&t.depth&&t.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(Bs).x}get height(){return this.source.getSize(Bs).y}get depth(){return this.source.getSize(Bs).z}get image(){return this.source.data}set image(t){this.source.data=t}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(t,e){this.updateRanges.push({start:t,count:e})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(t){return this.name=t.name,this.source=t.source,this.mipmaps=t.mipmaps.slice(0),this.mapping=t.mapping,this.channel=t.channel,this.wrapS=t.wrapS,this.wrapT=t.wrapT,this.magFilter=t.magFilter,this.minFilter=t.minFilter,this.anisotropy=t.anisotropy,this.format=t.format,this.internalFormat=t.internalFormat,this.type=t.type,this.normalized=t.normalized,this.offset.copy(t.offset),this.repeat.copy(t.repeat),this.center.copy(t.center),this.rotation=t.rotation,this.matrixAutoUpdate=t.matrixAutoUpdate,this.matrix.copy(t.matrix),this.generateMipmaps=t.generateMipmaps,this.premultiplyAlpha=t.premultiplyAlpha,this.flipY=t.flipY,this.unpackAlignment=t.unpackAlignment,this.colorSpace=t.colorSpace,this.renderTarget=t.renderTarget,this.isRenderTargetTexture=t.isRenderTargetTexture,this.isArrayTexture=t.isArrayTexture,this.userData=JSON.parse(JSON.stringify(t.userData)),this.needsUpdate=!0,this}setValues(t){for(let e in t){let n=t[e];if(n===void 0){St(`Texture.setValues(): parameter '${e}' has value of undefined.`);continue}let i=this[e];if(i===void 0){St(`Texture.setValues(): property '${e}' does not exist.`);continue}i&&n&&i.isVector2&&n.isVector2||i&&n&&i.isVector3&&n.isVector3||i&&n&&i.isMatrix3&&n.isMatrix3?i.copy(n):this[e]=n}}toJSON(t){let e=t===void 0||typeof t=="string";if(!e&&t.textures[this.uuid]!==void 0)return t.textures[this.uuid];let n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(t).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(n.userData=this.userData),e||(t.textures[this.uuid]=n),n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(t){if(this.mapping!==Or)return t;if(t.applyMatrix3(this.matrix),t.x<0||t.x>1)switch(this.wrapS){case _e:t.x=t.x-Math.floor(t.x);break;case Gn:t.x=t.x<0?0:1;break;case dr:Math.abs(Math.floor(t.x)%2)===1?t.x=Math.ceil(t.x)-t.x:t.x=t.x-Math.floor(t.x);break}if(t.y<0||t.y>1)switch(this.wrapT){case _e:t.y=t.y-Math.floor(t.y);break;case Gn:t.y=t.y<0?0:1;break;case dr:Math.abs(Math.floor(t.y)%2)===1?t.y=Math.ceil(t.y)-t.y:t.y=t.y-Math.floor(t.y);break}return this.flipY&&(t.y=1-t.y),t}set needsUpdate(t){t===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(t){t===!0&&this.pmremVersion++}};Ie.DEFAULT_IMAGE=null;Ie.DEFAULT_MAPPING=Or;Ie.DEFAULT_ANISOTROPY=1;var Kr=class Kr{constructor(t=0,e=0,n=0,i=1){this.x=t,this.y=e,this.z=n,this.w=i}get width(){return this.z}set width(t){this.z=t}get height(){return this.w}set height(t){this.w=t}set(t,e,n,i){return this.x=t,this.y=e,this.z=n,this.w=i,this}setScalar(t){return this.x=t,this.y=t,this.z=t,this.w=t,this}setX(t){return this.x=t,this}setY(t){return this.y=t,this}setZ(t){return this.z=t,this}setW(t){return this.w=t,this}setComponent(t,e){switch(t){case 0:this.x=e;break;case 1:this.y=e;break;case 2:this.z=e;break;case 3:this.w=e;break;default:throw new Error("THREE.Vector4: index is out of range: "+t)}return this}getComponent(t){switch(t){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("THREE.Vector4: index is out of range: "+t)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(t){return this.x=t.x,this.y=t.y,this.z=t.z,this.w=t.w!==void 0?t.w:1,this}add(t){return this.x+=t.x,this.y+=t.y,this.z+=t.z,this.w+=t.w,this}addScalar(t){return this.x+=t,this.y+=t,this.z+=t,this.w+=t,this}addVectors(t,e){return this.x=t.x+e.x,this.y=t.y+e.y,this.z=t.z+e.z,this.w=t.w+e.w,this}addScaledVector(t,e){return this.x+=t.x*e,this.y+=t.y*e,this.z+=t.z*e,this.w+=t.w*e,this}sub(t){return this.x-=t.x,this.y-=t.y,this.z-=t.z,this.w-=t.w,this}subScalar(t){return this.x-=t,this.y-=t,this.z-=t,this.w-=t,this}subVectors(t,e){return this.x=t.x-e.x,this.y=t.y-e.y,this.z=t.z-e.z,this.w=t.w-e.w,this}multiply(t){return this.x*=t.x,this.y*=t.y,this.z*=t.z,this.w*=t.w,this}multiplyScalar(t){return this.x*=t,this.y*=t,this.z*=t,this.w*=t,this}applyMatrix4(t){let e=this.x,n=this.y,i=this.z,s=this.w,r=t.elements;return this.x=r[0]*e+r[4]*n+r[8]*i+r[12]*s,this.y=r[1]*e+r[5]*n+r[9]*i+r[13]*s,this.z=r[2]*e+r[6]*n+r[10]*i+r[14]*s,this.w=r[3]*e+r[7]*n+r[11]*i+r[15]*s,this}divide(t){return this.x/=t.x,this.y/=t.y,this.z/=t.z,this.w/=t.w,this}divideScalar(t){return this.multiplyScalar(1/t)}setAxisAngleFromQuaternion(t){this.w=2*Math.acos(t.w);let e=Math.sqrt(1-t.w*t.w);return e<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=t.x/e,this.y=t.y/e,this.z=t.z/e),this}setAxisAngleFromRotationMatrix(t){let e,n,i,s,l=t.elements,c=l[0],u=l[4],d=l[8],h=l[1],f=l[5],p=l[9],m=l[2],x=l[6],v=l[10];if(Math.abs(u-h)<.01&&Math.abs(d-m)<.01&&Math.abs(p-x)<.01){if(Math.abs(u+h)<.1&&Math.abs(d+m)<.1&&Math.abs(p+x)<.1&&Math.abs(c+f+v-3)<.1)return this.set(1,0,0,0),this;e=Math.PI;let y=(c+1)/2,M=(f+1)/2,A=(v+1)/2,b=(u+h)/4,R=(d+m)/4,T=(p+x)/4;return y>M&&y>A?y<.01?(n=0,i=.707106781,s=.707106781):(n=Math.sqrt(y),i=b/n,s=R/n):M>A?M<.01?(n=.707106781,i=0,s=.707106781):(i=Math.sqrt(M),n=b/i,s=T/i):A<.01?(n=.707106781,i=.707106781,s=0):(s=Math.sqrt(A),n=R/s,i=T/s),this.set(n,i,s,e),this}let S=Math.sqrt((x-p)*(x-p)+(d-m)*(d-m)+(h-u)*(h-u));return Math.abs(S)<.001&&(S=1),this.x=(x-p)/S,this.y=(d-m)/S,this.z=(h-u)/S,this.w=Math.acos((c+f+v-1)/2),this}setFromMatrixPosition(t){let e=t.elements;return this.x=e[12],this.y=e[13],this.z=e[14],this.w=e[15],this}min(t){return this.x=Math.min(this.x,t.x),this.y=Math.min(this.y,t.y),this.z=Math.min(this.z,t.z),this.w=Math.min(this.w,t.w),this}max(t){return this.x=Math.max(this.x,t.x),this.y=Math.max(this.y,t.y),this.z=Math.max(this.z,t.z),this.w=Math.max(this.w,t.w),this}clamp(t,e){return this.x=Q(this.x,t.x,e.x),this.y=Q(this.y,t.y,e.y),this.z=Q(this.z,t.z,e.z),this.w=Q(this.w,t.w,e.w),this}clampScalar(t,e){return this.x=Q(this.x,t,e),this.y=Q(this.y,t,e),this.z=Q(this.z,t,e),this.w=Q(this.w,t,e),this}clampLength(t,e){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Q(n,t,e))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(t){return this.x*t.x+this.y*t.y+this.z*t.z+this.w*t.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(t){return this.normalize().multiplyScalar(t)}lerp(t,e){return this.x+=(t.x-this.x)*e,this.y+=(t.y-this.y)*e,this.z+=(t.z-this.z)*e,this.w+=(t.w-this.w)*e,this}lerpVectors(t,e,n){return this.x=t.x+(e.x-t.x)*n,this.y=t.y+(e.y-t.y)*n,this.z=t.z+(e.z-t.z)*n,this.w=t.w+(e.w-t.w)*n,this}equals(t){return t.x===this.x&&t.y===this.y&&t.z===this.z&&t.w===this.w}fromArray(t,e=0){return this.x=t[e],this.y=t[e+1],this.z=t[e+2],this.w=t[e+3],this}toArray(t=[],e=0){return t[e]=this.x,t[e+1]=this.y,t[e+2]=this.z,t[e+3]=this.w,t}fromBufferAttribute(t,e){return this.x=t.getX(e),this.y=t.getY(e),this.z=t.getZ(e),this.w=t.getW(e),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}};Kr.prototype.isVector4=!0;var Ye=Kr;var _s=class _s{constructor(t,e,n,i,s,r,a,l,c,u,d,h,f,p,m,x){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],t!==void 0&&this.set(t,e,n,i,s,r,a,l,c,u,d,h,f,p,m,x)}set(t,e,n,i,s,r,a,l,c,u,d,h,f,p,m,x){let v=this.elements;return v[0]=t,v[4]=e,v[8]=n,v[12]=i,v[1]=s,v[5]=r,v[9]=a,v[13]=l,v[2]=c,v[6]=u,v[10]=d,v[14]=h,v[3]=f,v[7]=p,v[11]=m,v[15]=x,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new _s().fromArray(this.elements)}copy(t){let e=this.elements,n=t.elements;return e[0]=n[0],e[1]=n[1],e[2]=n[2],e[3]=n[3],e[4]=n[4],e[5]=n[5],e[6]=n[6],e[7]=n[7],e[8]=n[8],e[9]=n[9],e[10]=n[10],e[11]=n[11],e[12]=n[12],e[13]=n[13],e[14]=n[14],e[15]=n[15],this}copyPosition(t){let e=this.elements,n=t.elements;return e[12]=n[12],e[13]=n[13],e[14]=n[14],this}setFromMatrix3(t){let e=t.elements;return this.set(e[0],e[3],e[6],0,e[1],e[4],e[7],0,e[2],e[5],e[8],0,0,0,0,1),this}extractBasis(t,e,n){return this.determinantAffine()===0?(t.set(1,0,0),e.set(0,1,0),n.set(0,0,1),this):(t.setFromMatrixColumn(this,0),e.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this)}makeBasis(t,e,n){return this.set(t.x,e.x,n.x,0,t.y,e.y,n.y,0,t.z,e.z,n.z,0,0,0,0,1),this}extractRotation(t){if(t.determinantAffine()===0)return this.identity();let e=this.elements,n=t.elements,i=1/cn.setFromMatrixColumn(t,0).length(),s=1/cn.setFromMatrixColumn(t,1).length(),r=1/cn.setFromMatrixColumn(t,2).length();return e[0]=n[0]*i,e[1]=n[1]*i,e[2]=n[2]*i,e[3]=0,e[4]=n[4]*s,e[5]=n[5]*s,e[6]=n[6]*s,e[7]=0,e[8]=n[8]*r,e[9]=n[9]*r,e[10]=n[10]*r,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,this}makeRotationFromEuler(t){let e=this.elements,n=t.x,i=t.y,s=t.z,r=Math.cos(n),a=Math.sin(n),l=Math.cos(i),c=Math.sin(i),u=Math.cos(s),d=Math.sin(s);if(t.order==="XYZ"){let h=r*u,f=r*d,p=a*u,m=a*d;e[0]=l*u,e[4]=-l*d,e[8]=c,e[1]=f+p*c,e[5]=h-m*c,e[9]=-a*l,e[2]=m-h*c,e[6]=p+f*c,e[10]=r*l}else if(t.order==="YXZ"){let h=l*u,f=l*d,p=c*u,m=c*d;e[0]=h+m*a,e[4]=p*a-f,e[8]=r*c,e[1]=r*d,e[5]=r*u,e[9]=-a,e[2]=f*a-p,e[6]=m+h*a,e[10]=r*l}else if(t.order==="ZXY"){let h=l*u,f=l*d,p=c*u,m=c*d;e[0]=h-m*a,e[4]=-r*d,e[8]=p+f*a,e[1]=f+p*a,e[5]=r*u,e[9]=m-h*a,e[2]=-r*c,e[6]=a,e[10]=r*l}else if(t.order==="ZYX"){let h=r*u,f=r*d,p=a*u,m=a*d;e[0]=l*u,e[4]=p*c-f,e[8]=h*c+m,e[1]=l*d,e[5]=m*c+h,e[9]=f*c-p,e[2]=-c,e[6]=a*l,e[10]=r*l}else if(t.order==="YZX"){let h=r*l,f=r*c,p=a*l,m=a*c;e[0]=l*u,e[4]=m-h*d,e[8]=p*d+f,e[1]=d,e[5]=r*u,e[9]=-a*u,e[2]=-c*u,e[6]=f*d+p,e[10]=h-m*d}else if(t.order==="XZY"){let h=r*l,f=r*c,p=a*l,m=a*c;e[0]=l*u,e[4]=-d,e[8]=c*u,e[1]=h*d+m,e[5]=r*u,e[9]=f*d-p,e[2]=p*d-f,e[6]=a*u,e[10]=m*d+h}return e[3]=0,e[7]=0,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,this}makeRotationFromQuaternion(t){return this.compose(Ll,t,Dl)}lookAt(t,e,n){let i=this.elements;return Xt.subVectors(t,e),Xt.lengthSq()===0&&(Xt.z=1),Xt.normalize(),Se.crossVectors(n,Xt),Se.lengthSq()===0&&(Math.abs(n.z)===1?Xt.x+=1e-4:Xt.z+=1e-4,Xt.normalize(),Se.crossVectors(n,Xt)),Se.normalize(),yi.crossVectors(Xt,Se),i[0]=Se.x,i[4]=yi.x,i[8]=Xt.x,i[1]=Se.y,i[5]=yi.y,i[9]=Xt.y,i[2]=Se.z,i[6]=yi.z,i[10]=Xt.z,this}multiply(t){return this.multiplyMatrices(this,t)}premultiply(t){return this.multiplyMatrices(t,this)}multiplyMatrices(t,e){let n=t.elements,i=e.elements,s=this.elements,r=n[0],a=n[4],l=n[8],c=n[12],u=n[1],d=n[5],h=n[9],f=n[13],p=n[2],m=n[6],x=n[10],v=n[14],S=n[3],y=n[7],M=n[11],A=n[15],b=i[0],R=i[4],T=i[8],I=i[12],C=i[1],P=i[5],k=i[9],w=i[13],U=i[2],L=i[6],V=i[10],X=i[14],J=i[3],K=i[7],E=i[11],N=i[15];return s[0]=r*b+a*C+l*U+c*J,s[4]=r*R+a*P+l*L+c*K,s[8]=r*T+a*k+l*V+c*E,s[12]=r*I+a*w+l*X+c*N,s[1]=u*b+d*C+h*U+f*J,s[5]=u*R+d*P+h*L+f*K,s[9]=u*T+d*k+h*V+f*E,s[13]=u*I+d*w+h*X+f*N,s[2]=p*b+m*C+x*U+v*J,s[6]=p*R+m*P+x*L+v*K,s[10]=p*T+m*k+x*V+v*E,s[14]=p*I+m*w+x*X+v*N,s[3]=S*b+y*C+M*U+A*J,s[7]=S*R+y*P+M*L+A*K,s[11]=S*T+y*k+M*V+A*E,s[15]=S*I+y*w+M*X+A*N,this}multiplyScalar(t){let e=this.elements;return e[0]*=t,e[4]*=t,e[8]*=t,e[12]*=t,e[1]*=t,e[5]*=t,e[9]*=t,e[13]*=t,e[2]*=t,e[6]*=t,e[10]*=t,e[14]*=t,e[3]*=t,e[7]*=t,e[11]*=t,e[15]*=t,this}determinant(){let t=this.elements,e=t[0],n=t[4],i=t[8],s=t[12],r=t[1],a=t[5],l=t[9],c=t[13],u=t[2],d=t[6],h=t[10],f=t[14],p=t[3],m=t[7],x=t[11],v=t[15],S=l*f-c*h,y=a*f-c*d,M=a*h-l*d,A=r*f-c*u,b=r*h-l*u,R=r*d-a*u;return e*(m*S-x*y+v*M)-n*(p*S-x*A+v*b)+i*(p*y-m*A+v*R)-s*(p*M-m*b+x*R)}determinantAffine(){let t=this.elements,e=t[0],n=t[4],i=t[8],s=t[1],r=t[5],a=t[9],l=t[2],c=t[6],u=t[10];return e*(r*u-a*c)-n*(s*u-a*l)+i*(s*c-r*l)}transpose(){let t=this.elements,e;return e=t[1],t[1]=t[4],t[4]=e,e=t[2],t[2]=t[8],t[8]=e,e=t[6],t[6]=t[9],t[9]=e,e=t[3],t[3]=t[12],t[12]=e,e=t[7],t[7]=t[13],t[13]=e,e=t[11],t[11]=t[14],t[14]=e,this}setPosition(t,e,n){let i=this.elements;return t.isVector3?(i[12]=t.x,i[13]=t.y,i[14]=t.z):(i[12]=t,i[13]=e,i[14]=n),this}invert(){let t=this.elements,e=t[0],n=t[1],i=t[2],s=t[3],r=t[4],a=t[5],l=t[6],c=t[7],u=t[8],d=t[9],h=t[10],f=t[11],p=t[12],m=t[13],x=t[14],v=t[15],S=e*a-n*r,y=e*l-i*r,M=e*c-s*r,A=n*l-i*a,b=n*c-s*a,R=i*c-s*l,T=u*m-d*p,I=u*x-h*p,C=u*v-f*p,P=d*x-h*m,k=d*v-f*m,w=h*v-f*x,U=S*w-y*k+M*P+A*C-b*I+R*T;if(U===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let L=1/U;return t[0]=(a*w-l*k+c*P)*L,t[1]=(i*k-n*w-s*P)*L,t[2]=(m*R-x*b+v*A)*L,t[3]=(h*b-d*R-f*A)*L,t[4]=(l*C-r*w-c*I)*L,t[5]=(e*w-i*C+s*I)*L,t[6]=(x*M-p*R-v*y)*L,t[7]=(u*R-h*M+f*y)*L,t[8]=(r*k-a*C+c*T)*L,t[9]=(n*C-e*k-s*T)*L,t[10]=(p*b-m*M+v*S)*L,t[11]=(d*M-u*b-f*S)*L,t[12]=(a*I-r*P-l*T)*L,t[13]=(e*P-n*I+i*T)*L,t[14]=(m*y-p*A-x*S)*L,t[15]=(u*A-d*y+h*S)*L,this}scale(t){let e=this.elements,n=t.x,i=t.y,s=t.z;return e[0]*=n,e[4]*=i,e[8]*=s,e[1]*=n,e[5]*=i,e[9]*=s,e[2]*=n,e[6]*=i,e[10]*=s,e[3]*=n,e[7]*=i,e[11]*=s,this}getMaxScaleOnAxis(){let t=this.elements,e=t[0]*t[0]+t[1]*t[1]+t[2]*t[2],n=t[4]*t[4]+t[5]*t[5]+t[6]*t[6],i=t[8]*t[8]+t[9]*t[9]+t[10]*t[10];return Math.sqrt(Math.max(e,n,i))}makeTranslation(t,e,n){return t.isVector3?this.set(1,0,0,t.x,0,1,0,t.y,0,0,1,t.z,0,0,0,1):this.set(1,0,0,t,0,1,0,e,0,0,1,n,0,0,0,1),this}makeRotationX(t){let e=Math.cos(t),n=Math.sin(t);return this.set(1,0,0,0,0,e,-n,0,0,n,e,0,0,0,0,1),this}makeRotationY(t){let e=Math.cos(t),n=Math.sin(t);return this.set(e,0,n,0,0,1,0,0,-n,0,e,0,0,0,0,1),this}makeRotationZ(t){let e=Math.cos(t),n=Math.sin(t);return this.set(e,-n,0,0,n,e,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(t,e){let n=Math.cos(e),i=Math.sin(e),s=1-n,r=t.x,a=t.y,l=t.z,c=s*r,u=s*a;return this.set(c*r+n,c*a-i*l,c*l+i*a,0,c*a+i*l,u*a+n,u*l-i*r,0,c*l-i*a,u*l+i*r,s*l*l+n,0,0,0,0,1),this}makeScale(t,e,n){return this.set(t,0,0,0,0,e,0,0,0,0,n,0,0,0,0,1),this}makeShear(t,e,n,i,s,r){return this.set(1,n,s,0,t,1,r,0,e,i,1,0,0,0,0,1),this}compose(t,e,n){let i=this.elements,s=e._x,r=e._y,a=e._z,l=e._w,c=s+s,u=r+r,d=a+a,h=s*c,f=s*u,p=s*d,m=r*u,x=r*d,v=a*d,S=l*c,y=l*u,M=l*d,A=n.x,b=n.y,R=n.z;return i[0]=(1-(m+v))*A,i[1]=(f+M)*A,i[2]=(p-y)*A,i[3]=0,i[4]=(f-M)*b,i[5]=(1-(h+v))*b,i[6]=(x+S)*b,i[7]=0,i[8]=(p+y)*R,i[9]=(x-S)*R,i[10]=(1-(h+m))*R,i[11]=0,i[12]=t.x,i[13]=t.y,i[14]=t.z,i[15]=1,this}decompose(t,e,n){let i=this.elements;t.x=i[12],t.y=i[13],t.z=i[14];let s=this.determinantAffine();if(s===0)return n.set(1,1,1),e.identity(),this;let r=cn.set(i[0],i[1],i[2]).length(),a=cn.set(i[4],i[5],i[6]).length(),l=cn.set(i[8],i[9],i[10]).length();s<0&&(r=-r),se.copy(this);let c=1/r,u=1/a,d=1/l;return se.elements[0]*=c,se.elements[1]*=c,se.elements[2]*=c,se.elements[4]*=u,se.elements[5]*=u,se.elements[6]*=u,se.elements[8]*=d,se.elements[9]*=d,se.elements[10]*=d,e.setFromRotationMatrix(se),n.x=r,n.y=a,n.z=l,this}makePerspective(t,e,n,i,s,r,a=Re,l=!1){let c=this.elements,u=2*s/(e-t),d=2*s/(n-i),h=(e+t)/(e-t),f=(n+i)/(n-i),p,m;if(l)p=s/(r-s),m=r*s/(r-s);else if(a===Re)p=-(r+s)/(r-s),m=-2*r*s/(r-s);else if(a===Jn)p=-r/(r-s),m=-r*s/(r-s);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+a);return c[0]=u,c[4]=0,c[8]=h,c[12]=0,c[1]=0,c[5]=d,c[9]=f,c[13]=0,c[2]=0,c[6]=0,c[10]=p,c[14]=m,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(t,e,n,i,s,r,a=Re,l=!1){let c=this.elements,u=2/(e-t),d=2/(n-i),h=-(e+t)/(e-t),f=-(n+i)/(n-i),p,m;if(l)p=1/(r-s),m=r/(r-s);else if(a===Re)p=-2/(r-s),m=-(r+s)/(r-s);else if(a===Jn)p=-1/(r-s),m=-s/(r-s);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+a);return c[0]=u,c[4]=0,c[8]=0,c[12]=h,c[1]=0,c[5]=d,c[9]=0,c[13]=f,c[2]=0,c[6]=0,c[10]=p,c[14]=m,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(t){let e=this.elements,n=t.elements;for(let i=0;i<16;i++)if(e[i]!==n[i])return!1;return!0}fromArray(t,e=0){for(let n=0;n<16;n++)this.elements[n]=t[n+e];return this}toArray(t=[],e=0){let n=this.elements;return t[e]=n[0],t[e+1]=n[1],t[e+2]=n[2],t[e+3]=n[3],t[e+4]=n[4],t[e+5]=n[5],t[e+6]=n[6],t[e+7]=n[7],t[e+8]=n[8],t[e+9]=n[9],t[e+10]=n[10],t[e+11]=n[11],t[e+12]=n[12],t[e+13]=n[13],t[e+14]=n[14],t[e+15]=n[15],t}};_s.prototype.isMatrix4=!0;var lt=_s,cn=new _,se=new lt,Ll=new _(0,0,0),Dl=new _(1,1,1),Se=new _,yi=new _,Xt=new _,To=new lt,Ao=new kt,Ze=class o{constructor(t=0,e=0,n=0,i=o.DEFAULT_ORDER){this.isEuler=!0,this._x=t,this._y=e,this._z=n,this._order=i}get x(){return this._x}set x(t){this._x=t,this._onChangeCallback()}get y(){return this._y}set y(t){this._y=t,this._onChangeCallback()}get z(){return this._z}set z(t){this._z=t,this._onChangeCallback()}get order(){return this._order}set order(t){this._order=t,this._onChangeCallback()}set(t,e,n,i=this._order){return this._x=t,this._y=e,this._z=n,this._order=i,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(t){return this._x=t._x,this._y=t._y,this._z=t._z,this._order=t._order,this._onChangeCallback(),this}setFromRotationMatrix(t,e=this._order,n=!0){let i=t.elements,s=i[0],r=i[4],a=i[8],l=i[1],c=i[5],u=i[9],d=i[2],h=i[6],f=i[10];switch(e){case"XYZ":this._y=Math.asin(Q(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(-u,f),this._z=Math.atan2(-r,s)):(this._x=Math.atan2(h,c),this._z=0);break;case"YXZ":this._x=Math.asin(-Q(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(a,f),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-d,s),this._z=0);break;case"ZXY":this._x=Math.asin(Q(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(-d,f),this._z=Math.atan2(-r,c)):(this._y=0,this._z=Math.atan2(l,s));break;case"ZYX":this._y=Math.asin(-Q(d,-1,1)),Math.abs(d)<.9999999?(this._x=Math.atan2(h,f),this._z=Math.atan2(l,s)):(this._x=0,this._z=Math.atan2(-r,c));break;case"YZX":this._z=Math.asin(Q(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-u,c),this._y=Math.atan2(-d,s)):(this._x=0,this._y=Math.atan2(a,f));break;case"XZY":this._z=Math.asin(-Q(r,-1,1)),Math.abs(r)<.9999999?(this._x=Math.atan2(h,c),this._y=Math.atan2(a,s)):(this._x=Math.atan2(-u,f),this._y=0);break;default:St("Euler: .setFromRotationMatrix() encountered an unknown order: "+e)}return this._order=e,n===!0&&this._onChangeCallback(),this}setFromQuaternion(t,e,n){return To.makeRotationFromQuaternion(t),this.setFromRotationMatrix(To,e,n)}setFromVector3(t,e=this._order){return this.set(t.x,t.y,t.z,e)}reorder(t){return Ao.setFromEuler(this),this.setFromQuaternion(Ao,t)}equals(t){return t._x===this._x&&t._y===this._y&&t._z===this._z&&t._order===this._order}fromArray(t){return this._x=t[0],this._y=t[1],this._z=t[2],t[3]!==void 0&&(this._order=t[3]),this._onChangeCallback(),this}toArray(t=[],e=0){return t[e]=this._x,t[e+1]=this._y,t[e+2]=this._z,t[e+3]=this._order,t}_onChange(t){return this._onChangeCallback=t,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}};Ze.DEFAULT_ORDER="XYZ";var Kn=class{constructor(){this.mask=1}set(t){this.mask=(1<<t|0)>>>0}enable(t){this.mask|=1<<t|0}enableAll(){this.mask=-1}toggle(t){this.mask^=1<<t|0}disable(t){this.mask&=~(1<<t|0)}disableAll(){this.mask=0}test(t){return(this.mask&t.mask)!==0}isEnabled(t){return(this.mask&(1<<t|0))!==0}},Nl=0,Ro=new _,un=new kt,de=new lt,vi=new _,Bn=new _,Ul=new _,Fl=new kt,Co=new _(1,0,0),Io=new _(0,1,0),Po=new _(0,0,1),Lo={type:"added"},Bl={type:"removed"},hn={type:"childadded",child:null},Os={type:"childremoved",child:null},Yt=class o extends Ce{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Nl++}),this.uuid=je(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=o.DEFAULT_UP.clone();let t=new _,e=new Ze,n=new kt,i=new _(1,1,1);function s(){n.setFromEuler(e,!1)}function r(){e.setFromQuaternion(n,void 0,!1)}e._onChange(s),n._onChange(r),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:t},rotation:{configurable:!0,enumerable:!0,value:e},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:i},modelViewMatrix:{value:new lt},normalMatrix:{value:new nt}}),this.matrix=new lt,this.matrixWorld=new lt,this.matrixAutoUpdate=o.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=o.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Kn,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(t){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(t),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(t){return this.quaternion.premultiply(t),this}setRotationFromAxisAngle(t,e){this.quaternion.setFromAxisAngle(t,e)}setRotationFromEuler(t){this.quaternion.setFromEuler(t,!0)}setRotationFromMatrix(t){this.quaternion.setFromRotationMatrix(t)}setRotationFromQuaternion(t){this.quaternion.copy(t)}rotateOnAxis(t,e){return un.setFromAxisAngle(t,e),this.quaternion.multiply(un),this}rotateOnWorldAxis(t,e){return un.setFromAxisAngle(t,e),this.quaternion.premultiply(un),this}rotateX(t){return this.rotateOnAxis(Co,t)}rotateY(t){return this.rotateOnAxis(Io,t)}rotateZ(t){return this.rotateOnAxis(Po,t)}translateOnAxis(t,e){return Ro.copy(t).applyQuaternion(this.quaternion),this.position.add(Ro.multiplyScalar(e)),this}translateX(t){return this.translateOnAxis(Co,t)}translateY(t){return this.translateOnAxis(Io,t)}translateZ(t){return this.translateOnAxis(Po,t)}localToWorld(t){return this.updateWorldMatrix(!0,!1),t.applyMatrix4(this.matrixWorld)}worldToLocal(t){return this.updateWorldMatrix(!0,!1),t.applyMatrix4(de.copy(this.matrixWorld).invert())}lookAt(t,e,n){t.isVector3?vi.copy(t):vi.set(t,e,n);let i=this.parent;this.updateWorldMatrix(!0,!1),Bn.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?de.lookAt(Bn,vi,this.up):de.lookAt(vi,Bn,this.up),this.quaternion.setFromRotationMatrix(de),i&&(de.extractRotation(i.matrixWorld),un.setFromRotationMatrix(de),this.quaternion.premultiply(un.invert()))}add(t){if(arguments.length>1){for(let e=0;e<arguments.length;e++)this.add(arguments[e]);return this}return t===this?(gt("Object3D.add: object can't be added as a child of itself.",t),this):(t&&t.isObject3D?(t.removeFromParent(),t.parent=this,this.children.push(t),t.dispatchEvent(Lo),hn.child=t,this.dispatchEvent(hn),hn.child=null):gt("Object3D.add: object not an instance of THREE.Object3D.",t),this)}remove(t){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}let e=this.children.indexOf(t);return e!==-1&&(t.parent=null,this.children.splice(e,1),t.dispatchEvent(Bl),Os.child=t,this.dispatchEvent(Os),Os.child=null),this}removeFromParent(){let t=this.parent;return t!==null&&t.remove(this),this}clear(){return this.remove(...this.children)}attach(t){return this.updateWorldMatrix(!0,!1),de.copy(this.matrixWorld).invert(),t.parent!==null&&(t.parent.updateWorldMatrix(!0,!1),de.multiply(t.parent.matrixWorld)),t.applyMatrix4(de),t.removeFromParent(),t.parent=this,this.children.push(t),t.updateWorldMatrix(!1,!0),t.dispatchEvent(Lo),hn.child=t,this.dispatchEvent(hn),hn.child=null,this}getObjectById(t){return this.getObjectByProperty("id",t)}getObjectByName(t){return this.getObjectByProperty("name",t)}getObjectByProperty(t,e){if(this[t]===e)return this;for(let n=0,i=this.children.length;n<i;n++){let r=this.children[n].getObjectByProperty(t,e);if(r!==void 0)return r}}getObjectsByProperty(t,e,n=[]){this[t]===e&&n.push(this);let i=this.children;for(let s=0,r=i.length;s<r;s++)i[s].getObjectsByProperty(t,e,n);return n}getWorldPosition(t){return this.updateWorldMatrix(!0,!1),t.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(t){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Bn,t,Ul),t}getWorldScale(t){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Bn,Fl,t),t}getWorldDirection(t){this.updateWorldMatrix(!0,!1);let e=this.matrixWorld.elements;return t.set(e[8],e[9],e[10]).normalize()}raycast(){}intersectsFrustum(){}traverse(t){t(this);let e=this.children;for(let n=0,i=e.length;n<i;n++)e[n].traverse(t)}traverseVisible(t){if(this.visible===!1)return;t(this);let e=this.children;for(let n=0,i=e.length;n<i;n++)e[n].traverseVisible(t)}traverseAncestors(t){let e=this.parent;e!==null&&(t(e),e.traverseAncestors(t))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);let t=this.pivot;if(t!==null){let e=t.x,n=t.y,i=t.z,s=this.matrix.elements;s[12]+=e-s[0]*e-s[4]*n-s[8]*i,s[13]+=n-s[1]*e-s[5]*n-s[9]*i,s[14]+=i-s[2]*e-s[6]*n-s[10]*i}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(t){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||t)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,t=!0);let e=this.children;for(let n=0,i=e.length;n<i;n++)e[n].updateMatrixWorld(t)}updateWorldMatrix(t,e,n=!1){let i=this.parent;if(t===!0&&i!==null&&i.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||n)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,n=!0),e===!0){let s=this.children;for(let r=0,a=s.length;r<a;r++)s[r].updateWorldMatrix(!1,!0,n)}}toJSON(t){let e=t===void 0||typeof t=="string",n={};e&&(t={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});let i={};i.uuid=this.uuid,i.type=this.type,i.name=this.name,i.castShadow=this.castShadow,i.receiveShadow=this.receiveShadow,i.visible=this.visible,i.frustumCulled=this.frustumCulled,i.renderOrder=this.renderOrder,i.static=this.static,i.matrixAutoUpdate=this.matrixAutoUpdate,Object.keys(this.userData).length>0&&(i.userData=this.userData),i.layers=this.layers.mask,i.matrix=this.matrix.toArray(),i.up=this.up.toArray(),this.pivot!==null&&(i.pivot=this.pivot.toArray()),this.morphTargetDictionary!==void 0&&(i.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(i.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(i.type="InstancedMesh",i.count=this.count,i.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(i.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(i.type="BatchedMesh",i.perObjectFrustumCulled=this.perObjectFrustumCulled,i.sortObjects=this.sortObjects,i.drawRanges=this._drawRanges,i.reservedRanges=this._reservedRanges,i.geometryInfo=this._geometryInfo.map(a=>({...a,boundingBox:a.boundingBox?a.boundingBox.toJSON():void 0,boundingSphere:a.boundingSphere?a.boundingSphere.toJSON():void 0})),i.instanceInfo=this._instanceInfo.map(a=>({...a})),i.availableInstanceIds=this._availableInstanceIds.slice(),i.availableGeometryIds=this._availableGeometryIds.slice(),i.nextIndexStart=this._nextIndexStart,i.nextVertexStart=this._nextVertexStart,i.geometryCount=this._geometryCount,i.maxInstanceCount=this._maxInstanceCount,i.maxVertexCount=this._maxVertexCount,i.maxIndexCount=this._maxIndexCount,i.geometryInitialized=this._geometryInitialized,i.matricesTexture=this._matricesTexture.toJSON(t),i.indirectTexture=this._indirectTexture.toJSON(t),this._colorsTexture!==null&&(i.colorsTexture=this._colorsTexture.toJSON(t)),this.boundingSphere!==null&&(i.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(i.boundingBox=this.boundingBox.toJSON()));function s(a,l){return a[l.uuid]===void 0&&(a[l.uuid]=l.toJSON(t)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?i.background=this.background.toJSON():this.background.isTexture&&(i.background=this.background.toJSON(t).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(i.environment=this.environment.toJSON(t).uuid);else if(this.isMesh||this.isLine||this.isPoints){i.geometry=s(t.geometries,this.geometry);let a=this.geometry.parameters;if(a!==void 0&&a.shapes!==void 0){let l=a.shapes;if(Array.isArray(l))for(let c=0,u=l.length;c<u;c++){let d=l[c];s(t.shapes,d)}else s(t.shapes,l)}}if(this.isSkinnedMesh&&(i.bindMode=this.bindMode,i.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(s(t.skeletons,this.skeleton),i.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){let a=[];for(let l=0,c=this.material.length;l<c;l++)a.push(s(t.materials,this.material[l]));i.material=a}else i.material=s(t.materials,this.material);if(this.children.length>0){i.children=[];for(let a=0;a<this.children.length;a++)i.children.push(this.children[a].toJSON(t).object)}if(this.animations.length>0){i.animations=[];for(let a=0;a<this.animations.length;a++){let l=this.animations[a];i.animations.push(s(t.animations,l))}}if(e){let a=r(t.geometries),l=r(t.materials),c=r(t.textures),u=r(t.images),d=r(t.shapes),h=r(t.skeletons),f=r(t.animations),p=r(t.nodes);a.length>0&&(n.geometries=a),l.length>0&&(n.materials=l),c.length>0&&(n.textures=c),u.length>0&&(n.images=u),d.length>0&&(n.shapes=d),h.length>0&&(n.skeletons=h),f.length>0&&(n.animations=f),p.length>0&&(n.nodes=p)}return n.object=i,n;function r(a){let l=[];for(let c in a){let u=a[c];delete u.metadata,l.push(u)}return l}}clone(t){return new this.constructor().copy(this,t)}copy(t,e=!0){if(this.name=t.name,this.up.copy(t.up),this.position.copy(t.position),this.rotation.order=t.rotation.order,this.quaternion.copy(t.quaternion),this.scale.copy(t.scale),this.pivot=t.pivot!==null?t.pivot.clone():null,this.matrix.copy(t.matrix),this.matrixWorld.copy(t.matrixWorld),this.matrixAutoUpdate=t.matrixAutoUpdate,this.matrixWorldAutoUpdate=t.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=t.matrixWorldNeedsUpdate,this.layers.mask=t.layers.mask,this.visible=t.visible,this.castShadow=t.castShadow,this.receiveShadow=t.receiveShadow,this.frustumCulled=t.frustumCulled,this.renderOrder=t.renderOrder,this.static=t.static,this.animations=t.animations.slice(),this.userData=JSON.parse(JSON.stringify(t.userData)),e===!0)for(let n=0;n<t.children.length;n++){let i=t.children[n];this.add(i.clone())}return this}dispose(){this.dispatchEvent({type:"dispose"})}};Yt.DEFAULT_UP=new _(0,1,0);Yt.DEFAULT_MATRIX_AUTO_UPDATE=!0;Yt.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var rt=class extends Yt{constructor(){super(),this.isGroup=!0,this.type="Group"}};var _a={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},be={h:0,s:0,l:0},Mi={h:0,s:0,l:0};function ks(o,t,e){return e<0&&(e+=1),e>1&&(e-=1),e<1/6?o+(t-o)*6*e:e<1/2?t:e<2/3?o+(t-o)*6*(2/3-e):o}var ft=class{constructor(t,e,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(t,e,n)}set(t,e,n){if(e===void 0&&n===void 0){let i=t;i&&i.isColor?this.copy(i):typeof i=="number"?this.setHex(i):typeof i=="string"&&this.setStyle(i)}else this.setRGB(t,e,n);return this}setScalar(t){return this.r=t,this.g=t,this.b=t,this}setHex(t,e=Bt){return t=Math.floor(t),this.r=(t>>16&255)/255,this.g=(t>>8&255)/255,this.b=(t&255)/255,jt.colorSpaceToWorking(this,e),this}setRGB(t,e,n,i=jt.workingColorSpace){return this.r=t,this.g=e,this.b=n,jt.colorSpaceToWorking(this,i),this}setHSL(t,e,n,i=jt.workingColorSpace){if(t=Gr(t,1),e=Q(e,0,1),n=Q(n,0,1),e===0)this.r=this.g=this.b=n;else{let s=n<=.5?n*(1+e):n+e-n*e,r=2*n-s;this.r=ks(r,s,t+1/3),this.g=ks(r,s,t),this.b=ks(r,s,t-1/3)}return jt.colorSpaceToWorking(this,i),this}setStyle(t,e=Bt){function n(s){s!==void 0&&parseFloat(s)<1&&St("Color: Alpha component of "+t+" will be ignored.")}let i;if(i=/^(\w+)\(([^\)]*)\)/.exec(t)){let s,r=i[1],a=i[2];switch(r){case"rgb":case"rgba":if(s=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(a))return n(s[4]),this.setRGB(Math.min(255,parseInt(s[1],10))/255,Math.min(255,parseInt(s[2],10))/255,Math.min(255,parseInt(s[3],10))/255,e);if(s=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(a))return n(s[4]),this.setRGB(Math.min(100,parseInt(s[1],10))/100,Math.min(100,parseInt(s[2],10))/100,Math.min(100,parseInt(s[3],10))/100,e);break;case"hsl":case"hsla":if(s=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(a))return n(s[4]),this.setHSL(parseFloat(s[1])/360,parseFloat(s[2])/100,parseFloat(s[3])/100,e);break;default:St("Color: Unknown color model "+t)}}else if(i=/^\#([A-Fa-f\d]+)$/.exec(t)){let s=i[1],r=s.length;if(r===3)return this.setRGB(parseInt(s.charAt(0),16)/15,parseInt(s.charAt(1),16)/15,parseInt(s.charAt(2),16)/15,e);if(r===6)return this.setHex(parseInt(s,16),e);St("Color: Invalid hex color "+t)}else if(t&&t.length>0)return this.setColorName(t,e);return this}setColorName(t,e=Bt){let n=_a[t.toLowerCase()];return n!==void 0?this.setHex(n,e):St("Color: Unknown color "+t),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(t){return this.r=t.r,this.g=t.g,this.b=t.b,this}copySRGBToLinear(t){return this.r=xe(t.r),this.g=xe(t.g),this.b=xe(t.b),this}copyLinearToSRGB(t){return this.r=En(t.r),this.g=En(t.g),this.b=En(t.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(t=Bt){return jt.workingToColorSpace(Nt.copy(this),t),Math.round(Q(Nt.r*255,0,255))*65536+Math.round(Q(Nt.g*255,0,255))*256+Math.round(Q(Nt.b*255,0,255))}getHexString(t=Bt){return("000000"+this.getHex(t).toString(16)).slice(-6)}getHSL(t,e=jt.workingColorSpace){jt.workingToColorSpace(Nt.copy(this),e);let n=Nt.r,i=Nt.g,s=Nt.b,r=Math.max(n,i,s),a=Math.min(n,i,s),l,c,u=(a+r)/2;if(a===r)l=0,c=0;else{let d=r-a;switch(c=u<=.5?d/(r+a):d/(2-r-a),r){case n:l=(i-s)/d+(i<s?6:0);break;case i:l=(s-n)/d+2;break;case s:l=(n-i)/d+4;break}l/=6}return t.h=l,t.s=c,t.l=u,t}getRGB(t,e=jt.workingColorSpace){return jt.workingToColorSpace(Nt.copy(this),e),t.r=Nt.r,t.g=Nt.g,t.b=Nt.b,t}getStyle(t=Bt){jt.workingToColorSpace(Nt.copy(this),t);let e=Nt.r,n=Nt.g,i=Nt.b;return t!==Bt?`color(${t} ${e.toFixed(3)} ${n.toFixed(3)} ${i.toFixed(3)})`:`rgb(${Math.round(e*255)},${Math.round(n*255)},${Math.round(i*255)})`}offsetHSL(t,e,n){return this.getHSL(be),this.setHSL(be.h+t,be.s+e,be.l+n)}add(t){return this.r+=t.r,this.g+=t.g,this.b+=t.b,this}addColors(t,e){return this.r=t.r+e.r,this.g=t.g+e.g,this.b=t.b+e.b,this}addScalar(t){return this.r+=t,this.g+=t,this.b+=t,this}sub(t){return this.r=Math.max(0,this.r-t.r),this.g=Math.max(0,this.g-t.g),this.b=Math.max(0,this.b-t.b),this}multiply(t){return this.r*=t.r,this.g*=t.g,this.b*=t.b,this}multiplyScalar(t){return this.r*=t,this.g*=t,this.b*=t,this}lerp(t,e){return this.r+=(t.r-this.r)*e,this.g+=(t.g-this.g)*e,this.b+=(t.b-this.b)*e,this}lerpColors(t,e,n){return this.r=t.r+(e.r-t.r)*n,this.g=t.g+(e.g-t.g)*n,this.b=t.b+(e.b-t.b)*n,this}lerpHSL(t,e){this.getHSL(be),t.getHSL(Mi);let n=$n(be.h,Mi.h,e),i=$n(be.s,Mi.s,e),s=$n(be.l,Mi.l,e);return this.setHSL(n,i,s),this}setFromVector3(t){return this.r=t.x,this.g=t.y,this.b=t.z,this}applyMatrix3(t){let e=this.r,n=this.g,i=this.b,s=t.elements;return this.r=s[0]*e+s[3]*n+s[6]*i,this.g=s[1]*e+s[4]*n+s[7]*i,this.b=s[2]*e+s[5]*n+s[8]*i,this}equals(t){return t.r===this.r&&t.g===this.g&&t.b===this.b}fromArray(t,e=0){return this.r=t[e],this.g=t[e+1],this.b=t[e+2],this}toArray(t=[],e=0){return t[e]=this.r,t[e+1]=this.g,t[e+2]=this.b,t}fromBufferAttribute(t,e){return this.r=t.getX(e),this.g=t.getY(e),this.b=t.getZ(e),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}},Nt=new ft;ft.NAMES=_a;var re=new _,fe=new _,zs=new _,pe=new _,dn=new _,fn=new _,Do=new _,Hs=new _,Vs=new _,Gs=new _,Ws=new Ye,Xs=new Ye,$s=new Ye,Ae=class o{constructor(t=new _,e=new _,n=new _){this.a=t,this.b=e,this.c=n}static getNormal(t,e,n,i){i.subVectors(n,e),re.subVectors(t,e),i.cross(re);let s=i.lengthSq();return s>0?i.multiplyScalar(1/Math.sqrt(s)):i.set(0,0,0)}static getBarycoord(t,e,n,i,s){re.subVectors(i,e),fe.subVectors(n,e),zs.subVectors(t,e);let r=re.dot(re),a=re.dot(fe),l=re.dot(zs),c=fe.dot(fe),u=fe.dot(zs),d=r*c-a*a;if(d===0)return s.set(0,0,0),null;let h=1/d,f=(c*l-a*u)*h,p=(r*u-a*l)*h;return s.set(1-f-p,p,f)}static containsPoint(t,e,n,i){return this.getBarycoord(t,e,n,i,pe)===null?!1:pe.x>=0&&pe.y>=0&&pe.x+pe.y<=1}static getInterpolation(t,e,n,i,s,r,a,l){return this.getBarycoord(t,e,n,i,pe)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(s,pe.x),l.addScaledVector(r,pe.y),l.addScaledVector(a,pe.z),l)}static getInterpolatedAttribute(t,e,n,i,s,r){return Ws.setScalar(0),Xs.setScalar(0),$s.setScalar(0),Ws.fromBufferAttribute(t,e),Xs.fromBufferAttribute(t,n),$s.fromBufferAttribute(t,i),r.setScalar(0),r.addScaledVector(Ws,s.x),r.addScaledVector(Xs,s.y),r.addScaledVector($s,s.z),r}static isFrontFacing(t,e,n,i){return re.subVectors(n,e),fe.subVectors(t,e),re.cross(fe).dot(i)<0}set(t,e,n){return this.a.copy(t),this.b.copy(e),this.c.copy(n),this}setFromPointsAndIndices(t,e,n,i){return this.a.copy(t[e]),this.b.copy(t[n]),this.c.copy(t[i]),this}setFromAttributeAndIndices(t,e,n,i){return this.a.fromBufferAttribute(t,e),this.b.fromBufferAttribute(t,n),this.c.fromBufferAttribute(t,i),this}clone(){return new this.constructor().copy(this)}copy(t){return this.a.copy(t.a),this.b.copy(t.b),this.c.copy(t.c),this}getArea(){return re.subVectors(this.c,this.b),fe.subVectors(this.a,this.b),re.cross(fe).length()*.5}getMidpoint(t){return t.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(t){return o.getNormal(this.a,this.b,this.c,t)}getPlane(t){return t.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(t,e){return o.getBarycoord(t,this.a,this.b,this.c,e)}getInterpolation(t,e,n,i,s){return o.getInterpolation(t,this.a,this.b,this.c,e,n,i,s)}containsPoint(t){return o.containsPoint(t,this.a,this.b,this.c)}isFrontFacing(t){return o.isFrontFacing(this.a,this.b,this.c,t)}intersectsBox(t){return t.intersectsTriangle(this)}closestPointToPoint(t,e){let n=this.a,i=this.b,s=this.c,r,a;dn.subVectors(i,n),fn.subVectors(s,n),Hs.subVectors(t,n);let l=dn.dot(Hs),c=fn.dot(Hs);if(l<=0&&c<=0)return e.copy(n);Vs.subVectors(t,i);let u=dn.dot(Vs),d=fn.dot(Vs);if(u>=0&&d<=u)return e.copy(i);let h=l*d-u*c;if(h<=0&&l>=0&&u<=0)return r=l/(l-u),e.copy(n).addScaledVector(dn,r);Gs.subVectors(t,s);let f=dn.dot(Gs),p=fn.dot(Gs);if(p>=0&&f<=p)return e.copy(s);let m=f*c-l*p;if(m<=0&&c>=0&&p<=0)return a=c/(c-p),e.copy(n).addScaledVector(fn,a);let x=u*p-f*d;if(x<=0&&d-u>=0&&f-p>=0)return Do.subVectors(s,i),a=(d-u)/(d-u+(f-p)),e.copy(i).addScaledVector(Do,a);let v=1/(x+m+h);return r=m*v,a=h*v,e.copy(n).addScaledVector(dn,r).addScaledVector(fn,a)}equals(t){return t.a.equals(this.a)&&t.b.equals(this.b)&&t.c.equals(this.c)}},ee=class{constructor(t=new _(1/0,1/0,1/0),e=new _(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=t,this.max=e}set(t,e){return this.min.copy(t),this.max.copy(e),this}setFromArray(t){this.makeEmpty();for(let e=0,n=t.length;e<n;e+=3)this.expandByPoint(oe.fromArray(t,e));return this}setFromBufferAttribute(t){this.makeEmpty();for(let e=0,n=t.count;e<n;e++)this.expandByPoint(oe.fromBufferAttribute(t,e));return this}setFromPoints(t){this.makeEmpty();for(let e=0,n=t.length;e<n;e++)this.expandByPoint(t[e]);return this}setFromCenterAndSize(t,e){let n=oe.copy(e).multiplyScalar(.5);return this.min.copy(t).sub(n),this.max.copy(t).add(n),this}setFromObject(t,e=!1){return this.makeEmpty(),this.expandByObject(t,e)}clone(){return new this.constructor().copy(this)}copy(t){return this.min.copy(t.min),this.max.copy(t.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(t){return this.isEmpty()?t.set(0,0,0):t.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(t){return this.isEmpty()?t.set(0,0,0):t.subVectors(this.max,this.min)}expandByPoint(t){return this.min.min(t),this.max.max(t),this}expandByVector(t){return this.min.sub(t),this.max.add(t),this}expandByScalar(t){return this.min.addScalar(-t),this.max.addScalar(t),this}expandByObject(t,e=!1){t.updateWorldMatrix(!1,!1);let n=t.geometry;if(n!==void 0){let s=n.getAttribute("position");if(e===!0&&s!==void 0&&t.isInstancedMesh!==!0)for(let r=0,a=s.count;r<a;r++)t.isMesh===!0?t.getVertexPosition(r,oe):oe.fromBufferAttribute(s,r),oe.applyMatrix4(t.matrixWorld),this.expandByPoint(oe);else t.boundingBox!==void 0?(t.boundingBox===null&&t.computeBoundingBox(),Si.copy(t.boundingBox)):(n.boundingBox===null&&n.computeBoundingBox(),Si.copy(n.boundingBox)),Si.applyMatrix4(t.matrixWorld),this.union(Si)}let i=t.children;for(let s=0,r=i.length;s<r;s++)this.expandByObject(i[s],e);return this}containsPoint(t){return t.x>=this.min.x&&t.x<=this.max.x&&t.y>=this.min.y&&t.y<=this.max.y&&t.z>=this.min.z&&t.z<=this.max.z}containsBox(t){return this.min.x<=t.min.x&&t.max.x<=this.max.x&&this.min.y<=t.min.y&&t.max.y<=this.max.y&&this.min.z<=t.min.z&&t.max.z<=this.max.z}getParameter(t,e){return e.set((t.x-this.min.x)/(this.max.x-this.min.x),(t.y-this.min.y)/(this.max.y-this.min.y),(t.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(t){return t.max.x>=this.min.x&&t.min.x<=this.max.x&&t.max.y>=this.min.y&&t.min.y<=this.max.y&&t.max.z>=this.min.z&&t.min.z<=this.max.z}intersectsSphere(t){return this.clampPoint(t.center,oe),oe.distanceToSquared(t.center)<=t.radius*t.radius}intersectsPlane(t){let e,n;return t.normal.x>0?(e=t.normal.x*this.min.x,n=t.normal.x*this.max.x):(e=t.normal.x*this.max.x,n=t.normal.x*this.min.x),t.normal.y>0?(e+=t.normal.y*this.min.y,n+=t.normal.y*this.max.y):(e+=t.normal.y*this.max.y,n+=t.normal.y*this.min.y),t.normal.z>0?(e+=t.normal.z*this.min.z,n+=t.normal.z*this.max.z):(e+=t.normal.z*this.max.z,n+=t.normal.z*this.min.z),e<=-t.constant&&n>=-t.constant}intersectsTriangle(t){if(this.isEmpty())return!1;this.getCenter(On),bi.subVectors(this.max,On),pn.subVectors(t.a,On),mn.subVectors(t.b,On),gn.subVectors(t.c,On),Ee.subVectors(mn,pn),we.subVectors(gn,mn),Ge.subVectors(pn,gn);let e=[0,-Ee.z,Ee.y,0,-we.z,we.y,0,-Ge.z,Ge.y,Ee.z,0,-Ee.x,we.z,0,-we.x,Ge.z,0,-Ge.x,-Ee.y,Ee.x,0,-we.y,we.x,0,-Ge.y,Ge.x,0];return!qs(e,pn,mn,gn,bi)||(e=[1,0,0,0,1,0,0,0,1],!qs(e,pn,mn,gn,bi))?!1:(Ei.crossVectors(Ee,we),e=[Ei.x,Ei.y,Ei.z],qs(e,pn,mn,gn,bi))}clampPoint(t,e){return e.copy(t).clamp(this.min,this.max)}distanceToPoint(t){return this.clampPoint(t,oe).distanceTo(t)}getBoundingSphere(t){return this.isEmpty()?t.makeEmpty():(this.getCenter(t.center),t.radius=this.getSize(oe).length()*.5),t}intersect(t){return this.min.max(t.min),this.max.min(t.max),this.isEmpty()&&this.makeEmpty(),this}union(t){return this.min.min(t.min),this.max.max(t.max),this}applyMatrix4(t){return this.isEmpty()?this:(me[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(t),me[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(t),me[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(t),me[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(t),me[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(t),me[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(t),me[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(t),me[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(t),this.setFromPoints(me),this)}translate(t){return this.min.add(t),this.max.add(t),this}equals(t){return t.min.equals(this.min)&&t.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(t){return this.min.fromArray(t.min),this.max.fromArray(t.max),this}},me=[new _,new _,new _,new _,new _,new _,new _,new _],oe=new _,Si=new ee,pn=new _,mn=new _,gn=new _,Ee=new _,we=new _,Ge=new _,On=new _,bi=new _,Ei=new _,We=new _;function qs(o,t,e,n,i){for(let s=0,r=o.length-3;s<=r;s+=3){We.fromArray(o,s);let a=i.x*Math.abs(We.x)+i.y*Math.abs(We.y)+i.z*Math.abs(We.z),l=t.dot(We),c=e.dot(We),u=n.dot(We);if(Math.max(-Math.max(l,c,u),Math.min(l,c,u))>a)return!1}return!0}var wt=new _,wi=new O,Ol=0,te=class extends Ce{constructor(t,e,n=!1){if(super(),Array.isArray(t))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Ol++}),this.name="",this.array=t,this.itemSize=e,this.count=t!==void 0?t.length/e:0,this.normalized=n,this.usage=ga,this.updateRanges=[],this.gpuType=Hr,this.version=0}onUploadCallback(){}set needsUpdate(t){t===!0&&this.version++}setUsage(t){return this.usage=t,this}addUpdateRange(t,e){this.updateRanges.push({start:t,count:e})}clearUpdateRanges(){this.updateRanges.length=0}copy(t){return this.name=t.name,this.array=new t.array.constructor(t.array),this.itemSize=t.itemSize,this.count=t.count,this.normalized=t.normalized,this.usage=t.usage,this.gpuType=t.gpuType,this}copyAt(t,e,n){t*=this.itemSize,n*=e.itemSize;for(let i=0,s=this.itemSize;i<s;i++)this.array[t+i]=e.array[n+i];return this}copyArray(t){return this.array.set(t),this}applyMatrix3(t){if(this.itemSize===2)for(let e=0,n=this.count;e<n;e++)wi.fromBufferAttribute(this,e),wi.applyMatrix3(t),this.setXY(e,wi.x,wi.y);else if(this.itemSize===3)for(let e=0,n=this.count;e<n;e++)wt.fromBufferAttribute(this,e),wt.applyMatrix3(t),this.setXYZ(e,wt.x,wt.y,wt.z);return this}applyMatrix4(t){for(let e=0,n=this.count;e<n;e++)wt.fromBufferAttribute(this,e),wt.applyMatrix4(t),this.setXYZ(e,wt.x,wt.y,wt.z);return this}applyNormalMatrix(t){for(let e=0,n=this.count;e<n;e++)wt.fromBufferAttribute(this,e),wt.applyNormalMatrix(t),this.setXYZ(e,wt.x,wt.y,wt.z);return this}transformDirection(t){for(let e=0,n=this.count;e<n;e++)wt.fromBufferAttribute(this,e),wt.transformDirection(t),this.setXYZ(e,wt.x,wt.y,wt.z);return this}set(t,e=0){return this.array.set(t,e),this}getComponent(t,e){let n=this.array[t*this.itemSize+e];return this.normalized&&(n=Sn(n,this.array)),n}setComponent(t,e,n){return this.normalized&&(n=Ft(n,this.array)),this.array[t*this.itemSize+e]=n,this}getX(t){let e=this.array[t*this.itemSize];return this.normalized&&(e=Sn(e,this.array)),e}setX(t,e){return this.normalized&&(e=Ft(e,this.array)),this.array[t*this.itemSize]=e,this}getY(t){let e=this.array[t*this.itemSize+1];return this.normalized&&(e=Sn(e,this.array)),e}setY(t,e){return this.normalized&&(e=Ft(e,this.array)),this.array[t*this.itemSize+1]=e,this}getZ(t){let e=this.array[t*this.itemSize+2];return this.normalized&&(e=Sn(e,this.array)),e}setZ(t,e){return this.normalized&&(e=Ft(e,this.array)),this.array[t*this.itemSize+2]=e,this}getW(t){let e=this.array[t*this.itemSize+3];return this.normalized&&(e=Sn(e,this.array)),e}setW(t,e){return this.normalized&&(e=Ft(e,this.array)),this.array[t*this.itemSize+3]=e,this}setXY(t,e,n){return t*=this.itemSize,this.normalized&&(e=Ft(e,this.array),n=Ft(n,this.array)),this.array[t+0]=e,this.array[t+1]=n,this}setXYZ(t,e,n,i){return t*=this.itemSize,this.normalized&&(e=Ft(e,this.array),n=Ft(n,this.array),i=Ft(i,this.array)),this.array[t+0]=e,this.array[t+1]=n,this.array[t+2]=i,this}setXYZW(t,e,n,i,s){return t*=this.itemSize,this.normalized&&(e=Ft(e,this.array),n=Ft(n,this.array),i=Ft(i,this.array),s=Ft(s,this.array)),this.array[t+0]=e,this.array[t+1]=n,this.array[t+2]=i,this.array[t+3]=s,this}onUpload(t){return this.onUploadCallback=t,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let t={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return t.name=this.name,t.usage=this.usage,t.gpuType=this.gpuType,t}dispose(){this.dispatchEvent({type:"dispose"})}};var Ji=class extends te{constructor(t,e,n){super(new Uint16Array(t),e,n)}};var Ki=class extends te{constructor(t,e,n){super(new Uint32Array(t),e,n)}};var ct=class extends te{constructor(t,e,n){super(new Float32Array(t),e,n)}},kl=new ee,kn=new _,Ys=new _,Pe=class{constructor(t=new _,e=-1){this.isSphere=!0,this.center=t,this.radius=e}set(t,e){return this.center.copy(t),this.radius=e,this}setFromPoints(t,e){let n=this.center;e!==void 0?n.copy(e):kl.setFromPoints(t).getCenter(n);let i=0;for(let s=0,r=t.length;s<r;s++)i=Math.max(i,n.distanceToSquared(t[s]));return this.radius=Math.sqrt(i),this}copy(t){return this.center.copy(t.center),this.radius=t.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(t){return t.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(t){return t.distanceTo(this.center)-this.radius}intersectsSphere(t){let e=this.radius+t.radius;return t.center.distanceToSquared(this.center)<=e*e}intersectsBox(t){return t.intersectsSphere(this)}intersectsPlane(t){return Math.abs(t.distanceToPoint(this.center))<=this.radius}clampPoint(t,e){let n=this.center.distanceToSquared(t);return e.copy(t),n>this.radius*this.radius&&(e.sub(this.center).normalize(),e.multiplyScalar(this.radius).add(this.center)),e}getBoundingBox(t){return this.isEmpty()?(t.makeEmpty(),t):(t.set(this.center,this.center),t.expandByScalar(this.radius),t)}applyMatrix4(t){return this.center.applyMatrix4(t),this.radius=this.radius*t.getMaxScaleOnAxis(),this}translate(t){return this.center.add(t),this}expandByPoint(t){if(this.isEmpty())return this.center.copy(t),this.radius=0,this;kn.subVectors(t,this.center);let e=kn.lengthSq();if(e>this.radius*this.radius){let n=Math.sqrt(e),i=(n-this.radius)*.5;this.center.addScaledVector(kn,i/n),this.radius+=i}return this}union(t){return t.isEmpty()?this:this.isEmpty()?(this.copy(t),this):(this.center.equals(t.center)===!0?this.radius=Math.max(this.radius,t.radius):(Ys.subVectors(t.center,this.center).setLength(t.radius),this.expandByPoint(kn.copy(t.center).add(Ys)),this.expandByPoint(kn.copy(t.center).sub(Ys))),this)}equals(t){return t.center.equals(this.center)&&t.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(t){return this.radius=t.radius,this.center.fromArray(t.center),this}},zl=0,Qt=new lt,Zs=new Yt,xn=new _,$t=new ee,zn=new ee,It=new _,Pt=class o extends Ce{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:zl++}),this.uuid=je(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={},this._transformed=!1}getIndex(){return this.index}setIndex(t){return Array.isArray(t)?this.index=new(ul(t)?Ki:Ji)(t,1):this.index=t,this}setIndirect(t,e=0){return this.indirect=t,this.indirectOffset=e,this}getIndirect(){return this.indirect}getAttribute(t){return this.attributes[t]}setAttribute(t,e){return this.attributes[t]=e,this}deleteAttribute(t){return delete this.attributes[t],this}hasAttribute(t){return this.attributes[t]!==void 0}addGroup(t,e,n=0){this.groups.push({start:t,count:e,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(t,e){this.drawRange.start=t,this.drawRange.count=e}applyMatrix4(t){let e=this.attributes.position;e!==void 0&&(e.applyMatrix4(t),e.needsUpdate=!0);let n=this.attributes.normal;if(n!==void 0){let s=new nt().getNormalMatrix(t);n.applyNormalMatrix(s),n.needsUpdate=!0}let i=this.attributes.tangent;return i!==void 0&&(i.transformDirection(t),i.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this._transformed=!0,this}applyQuaternion(t){return Qt.makeRotationFromQuaternion(t),this.applyMatrix4(Qt),this}rotateX(t){return Qt.makeRotationX(t),this.applyMatrix4(Qt),this}rotateY(t){return Qt.makeRotationY(t),this.applyMatrix4(Qt),this}rotateZ(t){return Qt.makeRotationZ(t),this.applyMatrix4(Qt),this}translate(t,e,n){return Qt.makeTranslation(t,e,n),this.applyMatrix4(Qt),this}scale(t,e,n){return Qt.makeScale(t,e,n),this.applyMatrix4(Qt),this}lookAt(t){return Zs.lookAt(t),Zs.updateMatrix(),this.applyMatrix4(Zs.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(xn).negate(),this.translate(xn.x,xn.y,xn.z),this}setFromPoints(t){let e=this.getAttribute("position");if(e===void 0){let n=[];for(let i=0,s=t.length;i<s;i++){let r=t[i];n.push(r.x,r.y,r.z||0)}this.setAttribute("position",new ct(n,3))}else{let n=Math.min(t.length,e.count);for(let i=0;i<n;i++){let s=t[i];e.setXYZ(i,s.x,s.y,s.z||0)}t.length>e.count&&St("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),e.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new ee);let t=this.attributes.position,e=this.morphAttributes.position;if(t&&t.isGLBufferAttribute){gt("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new _(-1/0,-1/0,-1/0),new _(1/0,1/0,1/0));return}if(t!==void 0){if(this.boundingBox.setFromBufferAttribute(t),e)for(let n=0,i=e.length;n<i;n++){let s=e[n];$t.setFromBufferAttribute(s),this.morphTargetsRelative?(It.addVectors(this.boundingBox.min,$t.min),this.boundingBox.expandByPoint(It),It.addVectors(this.boundingBox.max,$t.max),this.boundingBox.expandByPoint(It)):(this.boundingBox.expandByPoint($t.min),this.boundingBox.expandByPoint($t.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&gt('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Pe);let t=this.attributes.position,e=this.morphAttributes.position;if(t&&t.isGLBufferAttribute){gt("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new _,1/0);return}if(t){let n=this.boundingSphere.center;if($t.setFromBufferAttribute(t),e)for(let s=0,r=e.length;s<r;s++){let a=e[s];zn.setFromBufferAttribute(a),this.morphTargetsRelative?(It.addVectors($t.min,zn.min),$t.expandByPoint(It),It.addVectors($t.max,zn.max),$t.expandByPoint(It)):($t.expandByPoint(zn.min),$t.expandByPoint(zn.max))}$t.getCenter(n);let i=0;for(let s=0,r=t.count;s<r;s++)It.fromBufferAttribute(t,s),i=Math.max(i,n.distanceToSquared(It));if(e)for(let s=0,r=e.length;s<r;s++){let a=e[s],l=this.morphTargetsRelative;for(let c=0,u=a.count;c<u;c++)It.fromBufferAttribute(a,c),l&&(xn.fromBufferAttribute(t,c),It.add(xn)),i=Math.max(i,n.distanceToSquared(It))}this.boundingSphere.radius=Math.sqrt(i),isNaN(this.boundingSphere.radius)&&gt('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let t=this.index,e=this.attributes;if(t===null||e.position===void 0||e.normal===void 0||e.uv===void 0){gt("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let n=e.position,i=e.normal,s=e.uv,r=this.getAttribute("tangent");(r===void 0||r.count!==n.count)&&(r=new te(new Float32Array(4*n.count),4),this.setAttribute("tangent",r));let a=[],l=[];for(let T=0;T<n.count;T++)a[T]=new _,l[T]=new _;let c=new _,u=new _,d=new _,h=new O,f=new O,p=new O,m=new _,x=new _;function v(T,I,C){c.fromBufferAttribute(n,T),u.fromBufferAttribute(n,I),d.fromBufferAttribute(n,C),h.fromBufferAttribute(s,T),f.fromBufferAttribute(s,I),p.fromBufferAttribute(s,C),u.sub(c),d.sub(c),f.sub(h),p.sub(h);let P=1/(f.x*p.y-p.x*f.y);isFinite(P)&&(m.copy(u).multiplyScalar(p.y).addScaledVector(d,-f.y).multiplyScalar(P),x.copy(d).multiplyScalar(f.x).addScaledVector(u,-p.x).multiplyScalar(P),a[T].add(m),a[I].add(m),a[C].add(m),l[T].add(x),l[I].add(x),l[C].add(x))}let S=this.groups;S.length===0&&(S=[{start:0,count:t.count}]);for(let T=0,I=S.length;T<I;++T){let C=S[T],P=C.start,k=C.count;for(let w=P,U=P+k;w<U;w+=3)v(t.getX(w+0),t.getX(w+1),t.getX(w+2))}let y=new _,M=new _,A=new _,b=new _;function R(T){A.fromBufferAttribute(i,T),b.copy(A);let I=a[T];y.copy(I),y.sub(A.multiplyScalar(A.dot(I))).normalize(),M.crossVectors(b,I);let P=M.dot(l[T])<0?-1:1;r.setXYZW(T,y.x,y.y,y.z,P)}for(let T=0,I=S.length;T<I;++T){let C=S[T],P=C.start,k=C.count;for(let w=P,U=P+k;w<U;w+=3)R(t.getX(w+0)),R(t.getX(w+1)),R(t.getX(w+2))}this._transformed=!0}computeVertexNormals(){let t=this.index,e=this.getAttribute("position");if(e!==void 0){let n=this.getAttribute("normal");if(n===void 0||n.count!==e.count)n=new te(new Float32Array(e.count*3),3),this.setAttribute("normal",n);else for(let h=0,f=n.count;h<f;h++)n.setXYZ(h,0,0,0);let i=new _,s=new _,r=new _,a=new _,l=new _,c=new _,u=new _,d=new _;if(t)for(let h=0,f=t.count;h<f;h+=3){let p=t.getX(h+0),m=t.getX(h+1),x=t.getX(h+2);i.fromBufferAttribute(e,p),s.fromBufferAttribute(e,m),r.fromBufferAttribute(e,x),u.subVectors(r,s),d.subVectors(i,s),u.cross(d),a.fromBufferAttribute(n,p),l.fromBufferAttribute(n,m),c.fromBufferAttribute(n,x),a.add(u),l.add(u),c.add(u),n.setXYZ(p,a.x,a.y,a.z),n.setXYZ(m,l.x,l.y,l.z),n.setXYZ(x,c.x,c.y,c.z)}else for(let h=0,f=e.count;h<f;h+=3)i.fromBufferAttribute(e,h+0),s.fromBufferAttribute(e,h+1),r.fromBufferAttribute(e,h+2),u.subVectors(r,s),d.subVectors(i,s),u.cross(d),n.setXYZ(h+0,u.x,u.y,u.z),n.setXYZ(h+1,u.x,u.y,u.z),n.setXYZ(h+2,u.x,u.y,u.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){let t=this.attributes.normal;for(let e=0,n=t.count;e<n;e++)It.fromBufferAttribute(t,e),It.normalize(),t.setXYZ(e,It.x,It.y,It.z)}toNonIndexed(){function t(a,l){let c=a.array,u=a.itemSize,d=a.normalized,h=new c.constructor(l.length*u),f=0,p=0;for(let m=0,x=l.length;m<x;m++){a.isInterleavedBufferAttribute?f=l[m]*a.data.stride+a.offset:f=l[m]*u;for(let v=0;v<u;v++)h[p++]=c[f++]}return new te(h,u,d)}if(this.index===null)return St("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let e=new o,n=this.index.array,i=this.attributes;for(let a in i){let l=i[a],c=t(l,n);e.setAttribute(a,c)}let s=this.morphAttributes;for(let a in s){let l=[],c=s[a];for(let u=0,d=c.length;u<d;u++){let h=c[u],f=t(h,n);l.push(f)}e.morphAttributes[a]=l}e.morphTargetsRelative=this.morphTargetsRelative;let r=this.groups;for(let a=0,l=r.length;a<l;a++){let c=r[a];e.addGroup(c.start,c.count,c.materialIndex)}return e}toJSON(){let t={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(t.uuid=this.uuid,t.type=this.parameters!==void 0&&this._transformed===!0?"BufferGeometry":this.type,t.name=this.name,Object.keys(this.userData).length>0&&(t.userData=this.userData),this.parameters!==void 0&&this._transformed!==!0){let l=this.parameters;for(let c in l)l[c]!==void 0&&(t[c]=l[c]);return t}t.data={attributes:{}};let e=this.index;e!==null&&(t.data.index={type:e.array.constructor.name,array:Array.prototype.slice.call(e.array)});let n=this.attributes;for(let l in n){let c=n[l];t.data.attributes[l]=c.toJSON(t.data)}let i={},s=!1;for(let l in this.morphAttributes){let c=this.morphAttributes[l],u=[];for(let d=0,h=c.length;d<h;d++){let f=c[d];u.push(f.toJSON(t.data))}u.length>0&&(i[l]=u,s=!0)}s&&(t.data.morphAttributes=i,t.data.morphTargetsRelative=this.morphTargetsRelative);let r=this.groups;r.length>0&&(t.data.groups=JSON.parse(JSON.stringify(r)));let a=this.boundingSphere;return a!==null&&(t.data.boundingSphere=a.toJSON()),t}clone(){return new this.constructor().copy(this)}copy(t){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let e={};this.name=t.name;let n=t.index;n!==null&&this.setIndex(n.clone());let i=t.attributes;for(let c in i){let u=i[c];this.setAttribute(c,u.clone(e))}let s=t.morphAttributes;for(let c in s){let u=[],d=s[c];for(let h=0,f=d.length;h<f;h++)u.push(d[h].clone(e));this.morphAttributes[c]=u}this.morphTargetsRelative=t.morphTargetsRelative;let r=t.groups;for(let c=0,u=r.length;c<u;c++){let d=r[c];this.addGroup(d.start,d.count,d.materialIndex)}let a=t.boundingBox;a!==null&&(this.boundingBox=a.clone());let l=t.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=t.drawRange.start,this.drawRange.count=t.drawRange.count,this.userData=t.userData,this._transformed=t._transformed,this}dispose(){this.dispatchEvent({type:"dispose"})}};var Js=new _,Hl=new _,Vl=new nt,qt=class{constructor(t=new _(1,0,0),e=0){this.isPlane=!0,this.normal=t,this.constant=e}set(t,e){return this.normal.copy(t),this.constant=e,this}setComponents(t,e,n,i){return this.normal.set(t,e,n),this.constant=i,this}setFromNormalAndCoplanarPoint(t,e){return this.normal.copy(t),this.constant=-e.dot(this.normal),this}setFromCoplanarPoints(t,e,n){let i=Js.subVectors(n,e).cross(Hl.subVectors(t,e)).normalize();return this.setFromNormalAndCoplanarPoint(i,t),this}copy(t){return this.normal.copy(t.normal),this.constant=t.constant,this}normalize(){let t=1/this.normal.length();return this.normal.multiplyScalar(t),this.constant*=t,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(t){return this.normal.dot(t)+this.constant}distanceToSphere(t){return this.distanceToPoint(t.center)-t.radius}projectPoint(t,e){return e.copy(t).addScaledVector(this.normal,-this.distanceToPoint(t))}intersectLine(t,e,n=!0){let i=t.delta(Js),s=this.normal.dot(i);if(s===0)return this.distanceToPoint(t.start)===0?e.copy(t.start):null;let r=-(t.start.dot(this.normal)+this.constant)/s;return n===!0&&(r<0||r>1)?null:e.copy(t.start).addScaledVector(i,r)}intersectsLine(t){let e=this.distanceToPoint(t.start),n=this.distanceToPoint(t.end);return e<0&&n>0||n<0&&e>0}intersectsBox(t){return t.intersectsPlane(this)}intersectsSphere(t){return t.intersectsPlane(this)}coplanarPoint(t){return t.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(t,e){let n=e||Vl.getNormalMatrix(t),i=this.coplanarPoint(Js).applyMatrix4(t),s=this.normal.applyMatrix3(n).normalize();return this.constant=-i.dot(s),this}translate(t){return this.constant-=t.dot(this.normal),this}equals(t){return t.normal.equals(this.normal)&&t.constant===this.constant}clone(){return new this.constructor().copy(this)}toJSON(){return{normal:this.normal.toArray(),constant:this.constant}}fromJSON(t){return this.normal.fromArray(t.normal),this.constant=t.constant,this}},Gl=0,Qn=class extends Ce{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:Gl++}),this.uuid=je(),this.name="",this.type="Material",this.blending=na,this.side=Cr,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=sa,this.blendDst=ra,this.blendEquation=ia,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new ft(0,0,0),this.blendAlpha=0,this.depthFunc=Xi,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=ma,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=Wi,this.stencilZFail=Wi,this.stencilZPass=Wi,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(t){this._alphaTest>0!=t>0&&this.version++,this._alphaTest=t}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(t){if(t!==void 0)for(let e in t){let n=t[e];if(n===void 0){St(`Material: parameter '${e}' has value of undefined.`);continue}let i=this[e];if(i===void 0){St(`Material: '${e}' is not a property of THREE.${this.type}.`);continue}i&&i.isColor?i.set(n):i&&i.isVector2&&n&&n.isVector2||i&&i.isEuler&&n&&n.isEuler||i&&i.isVector3&&n&&n.isVector3?i.copy(n):this[e]=n}}toJSON(t){let e=t===void 0||typeof t=="string";e&&(t={textures:{},images:{}});let n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};n.uuid=this.uuid,n.type=this.type,n.blending=this.blending,n.side=this.side,n.shadowSide=this.shadowSide,n.vertexColors=this.vertexColors,n.opacity=this.opacity,n.transparent=this.transparent,n.blendSrc=this.blendSrc,n.blendDst=this.blendDst,n.blendEquation=this.blendEquation,n.blendSrcAlpha=this.blendSrcAlpha,n.blendDstAlpha=this.blendDstAlpha,n.blendEquationAlpha=this.blendEquationAlpha,n.blendColor=this.blendColor.getHex(),n.blendAlpha=this.blendAlpha,n.depthFunc=this.depthFunc,n.depthTest=this.depthTest,n.depthWrite=this.depthWrite,n.colorWrite=this.colorWrite,n.clipIntersection=this.clipIntersection,n.clipShadows=this.clipShadows,n.stencilWriteMask=this.stencilWriteMask,n.stencilFunc=this.stencilFunc,n.stencilRef=this.stencilRef,n.stencilFuncMask=this.stencilFuncMask,n.stencilFail=this.stencilFail,n.stencilZFail=this.stencilZFail,n.stencilZPass=this.stencilZPass,n.stencilWrite=this.stencilWrite,n.polygonOffset=this.polygonOffset,n.polygonOffsetFactor=this.polygonOffsetFactor,n.polygonOffsetUnits=this.polygonOffsetUnits,n.dithering=this.dithering,n.alphaTest=this.alphaTest,n.alphaHash=this.alphaHash,n.alphaToCoverage=this.alphaToCoverage,n.premultipliedAlpha=this.premultipliedAlpha,n.forceSinglePass=this.forceSinglePass,n.allowOverride=this.allowOverride,n.visible=this.visible,n.toneMapped=this.toneMapped,n.name=this.name,this.color&&this.color.isColor&&(n.color=this.color.getHex()),this.roughness!==void 0&&(n.roughness=this.roughness),this.metalness!==void 0&&(n.metalness=this.metalness),this.sheen!==void 0&&(n.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(n.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(n.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(n.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&(n.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(n.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(n.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(n.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(n.shininess=this.shininess),this.clearcoat!==void 0&&(n.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(n.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(n.clearcoatMap=this.clearcoatMap.toJSON(t).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(t).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(t).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(n.sheenColorMap=this.sheenColorMap.toJSON(t).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(t).uuid),this.dispersion!==void 0&&(n.dispersion=this.dispersion),this.retroreflectivity!==void 0&&(n.retroreflectivity=this.retroreflectivity),this.iridescence!==void 0&&(n.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(n.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(n.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(n.iridescenceMap=this.iridescenceMap.toJSON(t).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(t).uuid),this.anisotropy!==void 0&&(n.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(n.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(n.anisotropyMap=this.anisotropyMap.toJSON(t).uuid),this.map&&this.map.isTexture&&(n.map=this.map.toJSON(t).uuid),this.matcap&&this.matcap.isTexture&&(n.matcap=this.matcap.toJSON(t).uuid),this.alphaMap&&this.alphaMap.isTexture&&(n.alphaMap=this.alphaMap.toJSON(t).uuid),this.lightMap&&this.lightMap.isTexture&&(n.lightMap=this.lightMap.toJSON(t).uuid,n.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(n.aoMap=this.aoMap.toJSON(t).uuid,n.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(n.bumpMap=this.bumpMap.toJSON(t).uuid,n.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(n.normalMap=this.normalMap.toJSON(t).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(n.displacementMap=this.displacementMap.toJSON(t).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(n.roughnessMap=this.roughnessMap.toJSON(t).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(n.metalnessMap=this.metalnessMap.toJSON(t).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(n.emissiveMap=this.emissiveMap.toJSON(t).uuid),this.specularMap&&this.specularMap.isTexture&&(n.specularMap=this.specularMap.toJSON(t).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(n.specularIntensityMap=this.specularIntensityMap.toJSON(t).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(n.specularColorMap=this.specularColorMap.toJSON(t).uuid),this.envMap&&this.envMap.isTexture&&(n.envMap=this.envMap.toJSON(t).uuid,this.combine!==void 0&&(n.combine=this.combine)),this.envMapRotation!==void 0&&(n.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(n.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(n.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(n.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(n.gradientMap=this.gradientMap.toJSON(t).uuid),this.transmission!==void 0&&(n.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(n.transmissionMap=this.transmissionMap.toJSON(t).uuid),this.thickness!==void 0&&(n.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(n.thicknessMap=this.thicknessMap.toJSON(t).uuid),this.attenuationDistance!==void 0&&(n.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(n.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(n.size=this.size),this.sizeAttenuation!==void 0&&(n.sizeAttenuation=this.sizeAttenuation),Array.isArray(this.clippingPlanes)&&this.clippingPlanes.length>0&&(n.clippingPlanes=this.clippingPlanes.map(s=>s.toJSON())),this.rotation!==void 0&&(n.rotation=this.rotation),this.depthPacking!==void 0&&(n.depthPacking=this.depthPacking),this.linewidth!==void 0&&(n.linewidth=this.linewidth),this.linecap!==void 0&&(n.linecap=this.linecap),this.linejoin!==void 0&&(n.linejoin=this.linejoin),this.dashSize!==void 0&&(n.dashSize=this.dashSize),this.gapSize!==void 0&&(n.gapSize=this.gapSize),this.scale!==void 0&&(n.scale=this.scale),this.wireframe!==void 0&&(n.wireframe=this.wireframe),this.wireframeLinewidth!==void 0&&(n.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!==void 0&&(n.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!==void 0&&(n.wireframeLinejoin=this.wireframeLinejoin),this.flatShading!==void 0&&(n.flatShading=this.flatShading),this.fog!==void 0&&(n.fog=this.fog),Object.keys(this.userData).length>0&&(n.userData=this.userData);function i(s){let r=[];for(let a in s){let l=s[a];delete l.metadata,r.push(l)}return r}if(e){let s=i(t.textures),r=i(t.images);s.length>0&&(n.textures=s),r.length>0&&(n.images=r)}return n}fromJSON(t,e){if(t.uuid!==void 0&&(this.uuid=t.uuid),t.name!==void 0&&(this.name=t.name),t.color!==void 0&&this.color!==void 0&&this.color.setHex(t.color),t.roughness!==void 0&&(this.roughness=t.roughness),t.metalness!==void 0&&(this.metalness=t.metalness),t.sheen!==void 0&&(this.sheen=t.sheen),t.sheenColor!==void 0&&(this.sheenColor=new ft().setHex(t.sheenColor)),t.sheenRoughness!==void 0&&(this.sheenRoughness=t.sheenRoughness),t.emissive!==void 0&&this.emissive!==void 0&&this.emissive.setHex(t.emissive),t.specular!==void 0&&this.specular!==void 0&&this.specular.setHex(t.specular),t.specularIntensity!==void 0&&(this.specularIntensity=t.specularIntensity),t.specularColor!==void 0&&this.specularColor!==void 0&&this.specularColor.setHex(t.specularColor),t.shininess!==void 0&&(this.shininess=t.shininess),t.clearcoat!==void 0&&(this.clearcoat=t.clearcoat),t.clearcoatRoughness!==void 0&&(this.clearcoatRoughness=t.clearcoatRoughness),t.dispersion!==void 0&&(this.dispersion=t.dispersion),t.retroreflectivity!==void 0&&(this.retroreflectivity=t.retroreflectivity),t.iridescence!==void 0&&(this.iridescence=t.iridescence),t.iridescenceIOR!==void 0&&(this.iridescenceIOR=t.iridescenceIOR),t.iridescenceThicknessRange!==void 0&&(this.iridescenceThicknessRange=t.iridescenceThicknessRange),t.transmission!==void 0&&(this.transmission=t.transmission),t.thickness!==void 0&&(this.thickness=t.thickness),t.attenuationDistance!==void 0&&(this.attenuationDistance=t.attenuationDistance),t.attenuationColor!==void 0&&this.attenuationColor!==void 0&&this.attenuationColor.setHex(t.attenuationColor),t.anisotropy!==void 0&&(this.anisotropy=t.anisotropy),t.anisotropyRotation!==void 0&&(this.anisotropyRotation=t.anisotropyRotation),t.fog!==void 0&&(this.fog=t.fog),t.flatShading!==void 0&&(this.flatShading=t.flatShading),t.blending!==void 0&&(this.blending=t.blending),t.combine!==void 0&&(this.combine=t.combine),t.side!==void 0&&(this.side=t.side),t.shadowSide!==void 0&&(this.shadowSide=t.shadowSide),t.opacity!==void 0&&(this.opacity=t.opacity),t.transparent!==void 0&&(this.transparent=t.transparent),t.alphaTest!==void 0&&(this.alphaTest=t.alphaTest),t.alphaHash!==void 0&&(this.alphaHash=t.alphaHash),t.depthFunc!==void 0&&(this.depthFunc=t.depthFunc),t.depthTest!==void 0&&(this.depthTest=t.depthTest),t.depthWrite!==void 0&&(this.depthWrite=t.depthWrite),t.colorWrite!==void 0&&(this.colorWrite=t.colorWrite),t.clippingPlanes!==void 0&&(this.clippingPlanes=t.clippingPlanes.map(n=>new qt().fromJSON(n))),t.clipIntersection!==void 0&&(this.clipIntersection=t.clipIntersection),t.clipShadows!==void 0&&(this.clipShadows=t.clipShadows),t.depthPacking!==void 0&&(this.depthPacking=t.depthPacking),t.blendSrc!==void 0&&(this.blendSrc=t.blendSrc),t.blendDst!==void 0&&(this.blendDst=t.blendDst),t.blendEquation!==void 0&&(this.blendEquation=t.blendEquation),t.blendSrcAlpha!==void 0&&(this.blendSrcAlpha=t.blendSrcAlpha),t.blendDstAlpha!==void 0&&(this.blendDstAlpha=t.blendDstAlpha),t.blendEquationAlpha!==void 0&&(this.blendEquationAlpha=t.blendEquationAlpha),t.blendColor!==void 0&&this.blendColor!==void 0&&this.blendColor.setHex(t.blendColor),t.blendAlpha!==void 0&&(this.blendAlpha=t.blendAlpha),t.stencilWriteMask!==void 0&&(this.stencilWriteMask=t.stencilWriteMask),t.stencilFunc!==void 0&&(this.stencilFunc=t.stencilFunc),t.stencilRef!==void 0&&(this.stencilRef=t.stencilRef),t.stencilFuncMask!==void 0&&(this.stencilFuncMask=t.stencilFuncMask),t.stencilFail!==void 0&&(this.stencilFail=t.stencilFail),t.stencilZFail!==void 0&&(this.stencilZFail=t.stencilZFail),t.stencilZPass!==void 0&&(this.stencilZPass=t.stencilZPass),t.stencilWrite!==void 0&&(this.stencilWrite=t.stencilWrite),t.wireframe!==void 0&&(this.wireframe=t.wireframe),t.wireframeLinewidth!==void 0&&(this.wireframeLinewidth=t.wireframeLinewidth),t.wireframeLinecap!==void 0&&(this.wireframeLinecap=t.wireframeLinecap),t.wireframeLinejoin!==void 0&&(this.wireframeLinejoin=t.wireframeLinejoin),t.rotation!==void 0&&(this.rotation=t.rotation),t.linewidth!==void 0&&(this.linewidth=t.linewidth),t.linecap!==void 0&&(this.linecap=t.linecap),t.linejoin!==void 0&&(this.linejoin=t.linejoin),t.dashSize!==void 0&&(this.dashSize=t.dashSize),t.gapSize!==void 0&&(this.gapSize=t.gapSize),t.scale!==void 0&&(this.scale=t.scale),t.polygonOffset!==void 0&&(this.polygonOffset=t.polygonOffset),t.polygonOffsetFactor!==void 0&&(this.polygonOffsetFactor=t.polygonOffsetFactor),t.polygonOffsetUnits!==void 0&&(this.polygonOffsetUnits=t.polygonOffsetUnits),t.dithering!==void 0&&(this.dithering=t.dithering),t.alphaToCoverage!==void 0&&(this.alphaToCoverage=t.alphaToCoverage),t.premultipliedAlpha!==void 0&&(this.premultipliedAlpha=t.premultipliedAlpha),t.forceSinglePass!==void 0&&(this.forceSinglePass=t.forceSinglePass),t.allowOverride!==void 0&&(this.allowOverride=t.allowOverride),t.visible!==void 0&&(this.visible=t.visible),t.toneMapped!==void 0&&(this.toneMapped=t.toneMapped),t.userData!==void 0&&(this.userData=t.userData),t.vertexColors!==void 0&&(typeof t.vertexColors=="number"?this.vertexColors=t.vertexColors>0:this.vertexColors=t.vertexColors),t.size!==void 0&&(this.size=t.size),t.sizeAttenuation!==void 0&&(this.sizeAttenuation=t.sizeAttenuation),t.map!==void 0&&(this.map=e[t.map]||null),t.matcap!==void 0&&(this.matcap=e[t.matcap]||null),t.alphaMap!==void 0&&(this.alphaMap=e[t.alphaMap]||null),t.bumpMap!==void 0&&(this.bumpMap=e[t.bumpMap]||null),t.bumpScale!==void 0&&(this.bumpScale=t.bumpScale),t.normalMap!==void 0&&(this.normalMap=e[t.normalMap]||null),t.normalMapType!==void 0&&(this.normalMapType=t.normalMapType),t.normalScale!==void 0){let n=t.normalScale;Array.isArray(n)===!1&&(n=[n,n]),this.normalScale=new O().fromArray(n)}return t.displacementMap!==void 0&&(this.displacementMap=e[t.displacementMap]||null),t.displacementScale!==void 0&&(this.displacementScale=t.displacementScale),t.displacementBias!==void 0&&(this.displacementBias=t.displacementBias),t.roughnessMap!==void 0&&(this.roughnessMap=e[t.roughnessMap]||null),t.metalnessMap!==void 0&&(this.metalnessMap=e[t.metalnessMap]||null),t.emissiveMap!==void 0&&(this.emissiveMap=e[t.emissiveMap]||null),t.emissiveIntensity!==void 0&&(this.emissiveIntensity=t.emissiveIntensity),t.specularMap!==void 0&&(this.specularMap=e[t.specularMap]||null),t.specularIntensityMap!==void 0&&(this.specularIntensityMap=e[t.specularIntensityMap]||null),t.specularColorMap!==void 0&&(this.specularColorMap=e[t.specularColorMap]||null),t.envMap!==void 0&&(this.envMap=e[t.envMap]||null),t.envMapRotation!==void 0&&this.envMapRotation.fromArray(t.envMapRotation),t.envMapIntensity!==void 0&&(this.envMapIntensity=t.envMapIntensity),t.reflectivity!==void 0&&(this.reflectivity=t.reflectivity),t.refractionRatio!==void 0&&(this.refractionRatio=t.refractionRatio),t.lightMap!==void 0&&(this.lightMap=e[t.lightMap]||null),t.lightMapIntensity!==void 0&&(this.lightMapIntensity=t.lightMapIntensity),t.aoMap!==void 0&&(this.aoMap=e[t.aoMap]||null),t.aoMapIntensity!==void 0&&(this.aoMapIntensity=t.aoMapIntensity),t.gradientMap!==void 0&&(this.gradientMap=e[t.gradientMap]||null),t.clearcoatMap!==void 0&&(this.clearcoatMap=e[t.clearcoatMap]||null),t.clearcoatRoughnessMap!==void 0&&(this.clearcoatRoughnessMap=e[t.clearcoatRoughnessMap]||null),t.clearcoatNormalMap!==void 0&&(this.clearcoatNormalMap=e[t.clearcoatNormalMap]||null),t.clearcoatNormalScale!==void 0&&(this.clearcoatNormalScale=new O().fromArray(t.clearcoatNormalScale)),t.iridescenceMap!==void 0&&(this.iridescenceMap=e[t.iridescenceMap]||null),t.iridescenceThicknessMap!==void 0&&(this.iridescenceThicknessMap=e[t.iridescenceThicknessMap]||null),t.transmissionMap!==void 0&&(this.transmissionMap=e[t.transmissionMap]||null),t.thicknessMap!==void 0&&(this.thicknessMap=e[t.thicknessMap]||null),t.anisotropyMap!==void 0&&(this.anisotropyMap=e[t.anisotropyMap]||null),t.sheenColorMap!==void 0&&(this.sheenColorMap=e[t.sheenColorMap]||null),t.sheenRoughnessMap!==void 0&&(this.sheenRoughnessMap=e[t.sheenRoughnessMap]||null),this}clone(){return new this.constructor().copy(this)}copy(t){this.name=t.name,this.blending=t.blending,this.side=t.side,this.vertexColors=t.vertexColors,this.opacity=t.opacity,this.transparent=t.transparent,this.blendSrc=t.blendSrc,this.blendDst=t.blendDst,this.blendEquation=t.blendEquation,this.blendSrcAlpha=t.blendSrcAlpha,this.blendDstAlpha=t.blendDstAlpha,this.blendEquationAlpha=t.blendEquationAlpha,this.blendColor.copy(t.blendColor),this.blendAlpha=t.blendAlpha,this.depthFunc=t.depthFunc,this.depthTest=t.depthTest,this.depthWrite=t.depthWrite,this.stencilWriteMask=t.stencilWriteMask,this.stencilFunc=t.stencilFunc,this.stencilRef=t.stencilRef,this.stencilFuncMask=t.stencilFuncMask,this.stencilFail=t.stencilFail,this.stencilZFail=t.stencilZFail,this.stencilZPass=t.stencilZPass,this.stencilWrite=t.stencilWrite;let e=t.clippingPlanes,n=null;if(e!==null){let i=e.length;n=new Array(i);for(let s=0;s!==i;++s)n[s]=e[s].clone()}return this.clippingPlanes=n,this.clipIntersection=t.clipIntersection,this.clipShadows=t.clipShadows,this.shadowSide=t.shadowSide,this.colorWrite=t.colorWrite,this.precision=t.precision,this.polygonOffset=t.polygonOffset,this.polygonOffsetFactor=t.polygonOffsetFactor,this.polygonOffsetUnits=t.polygonOffsetUnits,this.dithering=t.dithering,this.alphaTest=t.alphaTest,this.alphaHash=t.alphaHash,this.alphaToCoverage=t.alphaToCoverage,this.premultipliedAlpha=t.premultipliedAlpha,this.forceSinglePass=t.forceSinglePass,this.allowOverride=t.allowOverride,this.visible=t.visible,this.toneMapped=t.toneMapped,this.userData=JSON.parse(JSON.stringify(t.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(t){t===!0&&this.version++}};var ge=new _,Ks=new _,Ti=new _,Ai=new _,jn=class{constructor(t=new _,e=new _(0,0,-1)){this.origin=t,this.direction=e}set(t,e){return this.origin.copy(t),this.direction.copy(e),this}copy(t){return this.origin.copy(t.origin),this.direction.copy(t.direction),this}at(t,e){return e.copy(this.origin).addScaledVector(this.direction,t)}lookAt(t){return this.direction.copy(t).sub(this.origin).normalize(),this}recast(t){return this.origin.copy(this.at(t,ge)),this}closestPointToPoint(t,e){e.subVectors(t,this.origin);let n=e.dot(this.direction);return n<0?e.copy(this.origin):e.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(t){return Math.sqrt(this.distanceSqToPoint(t))}distanceSqToPoint(t){let e=ge.subVectors(t,this.origin).dot(this.direction);return e<0?this.origin.distanceToSquared(t):(ge.copy(this.origin).addScaledVector(this.direction,e),ge.distanceToSquared(t))}distanceSqToSegment(t,e,n,i){Ks.copy(t).add(e).multiplyScalar(.5),Ti.copy(e).sub(t).normalize(),Ai.copy(this.origin).sub(Ks);let s=t.distanceTo(e)*.5,r=-this.direction.dot(Ti),a=Ai.dot(this.direction),l=-Ai.dot(Ti),c=Ai.lengthSq(),u=Math.abs(1-r*r),d,h,f,p;if(u>0)if(d=r*l-a,h=r*a-l,p=s*u,d>=0)if(h>=-p)if(h<=p){let m=1/u;d*=m,h*=m,f=d*(d+r*h+2*a)+h*(r*d+h+2*l)+c}else h=s,d=Math.max(0,-(r*h+a)),f=-d*d+h*(h+2*l)+c;else h=-s,d=Math.max(0,-(r*h+a)),f=-d*d+h*(h+2*l)+c;else h<=-p?(d=Math.max(0,-(-r*s+a)),h=d>0?-s:Math.min(Math.max(-s,-l),s),f=-d*d+h*(h+2*l)+c):h<=p?(d=0,h=Math.min(Math.max(-s,-l),s),f=h*(h+2*l)+c):(d=Math.max(0,-(r*s+a)),h=d>0?s:Math.min(Math.max(-s,-l),s),f=-d*d+h*(h+2*l)+c);else h=r>0?-s:s,d=Math.max(0,-(r*h+a)),f=-d*d+h*(h+2*l)+c;return n&&n.copy(this.origin).addScaledVector(this.direction,d),i&&i.copy(Ks).addScaledVector(Ti,h),f}intersectSphere(t,e){if(t.radius<0)return null;ge.subVectors(t.center,this.origin);let n=ge.dot(this.direction),i=ge.dot(ge)-n*n,s=t.radius*t.radius;if(i>s)return null;let r=Math.sqrt(s-i),a=n-r,l=n+r;return l<0?null:a<0?this.at(l,e):this.at(a,e)}intersectsSphere(t){return t.radius<0?!1:this.distanceSqToPoint(t.center)<=t.radius*t.radius}distanceToPlane(t){let e=t.normal.dot(this.direction);if(e===0)return t.distanceToPoint(this.origin)===0?0:null;let n=-(this.origin.dot(t.normal)+t.constant)/e;return n>=0?n:null}intersectPlane(t,e){let n=this.distanceToPlane(t);return n===null?null:this.at(n,e)}intersectsPlane(t){let e=t.distanceToPoint(this.origin);return e===0||t.normal.dot(this.direction)*e<0}intersectBox(t,e){let n,i,s,r,a,l,c=1/this.direction.x,u=1/this.direction.y,d=1/this.direction.z,h=this.origin;return c>=0?(n=(t.min.x-h.x)*c,i=(t.max.x-h.x)*c):(n=(t.max.x-h.x)*c,i=(t.min.x-h.x)*c),u>=0?(s=(t.min.y-h.y)*u,r=(t.max.y-h.y)*u):(s=(t.max.y-h.y)*u,r=(t.min.y-h.y)*u),n>r||s>i||((s>n||isNaN(n))&&(n=s),(r<i||isNaN(i))&&(i=r),d>=0?(a=(t.min.z-h.z)*d,l=(t.max.z-h.z)*d):(a=(t.max.z-h.z)*d,l=(t.min.z-h.z)*d),n>l||a>i)||((a>n||n!==n)&&(n=a),(l<i||i!==i)&&(i=l),i<0)?null:this.at(n>=0?n:i,e)}intersectsBox(t){return this.intersectBox(t,ge)!==null}intersectTriangle(t,e,n,i,s){let r=this.origin,a=this.direction,l=a.x,c=a.y,u=a.z,d=t.x-r.x,h=t.y-r.y,f=t.z-r.z,p=e.x-r.x,m=e.y-r.y,x=e.z-r.z,v=n.x-r.x,S=n.y-r.y,y=n.z-r.z,M=Math.abs(l),A=Math.abs(c),b=Math.abs(u),R,T,I,C,P,k,w,U,L,V,X,J;if(M>=A&&M>=b?(I=l,k=d,L=p,J=v,l>=0?(R=c,T=u,C=h,P=f,w=m,U=x,V=S,X=y):(R=u,T=c,C=f,P=h,w=x,U=m,V=y,X=S)):A>=b?(I=c,k=h,L=m,J=S,c>=0?(R=u,T=l,C=f,P=d,w=x,U=p,V=y,X=v):(R=l,T=u,C=d,P=f,w=p,U=x,V=v,X=y)):(I=u,k=f,L=x,J=y,u>=0?(R=l,T=c,C=d,P=h,w=p,U=m,V=v,X=S):(R=c,T=l,C=h,P=d,w=m,U=p,V=S,X=v)),I===0)return null;let K=R/I,E=T/I,N=1/I,H=C-K*k,$=P-E*k,ut=w-K*L,_t=U-E*L,Ct=V-K*J,Mt=X-E*J,bt=Ct*_t-Mt*ut,Et=H*Mt-$*Ct,Ut=ut*$-_t*H;if(i){if(bt<0||Et<0||Ut<0)return null}else if((bt<0||Et<0||Ut<0)&&(bt>0||Et>0||Ut>0))return null;let He=bt+Et+Ut;if(He===0)return null;let Vt=N*(bt*k+Et*L+Ut*J);return(He>0?Vt<0:Vt>0)?null:this.at(Vt/He,s)}applyMatrix4(t){return this.origin.applyMatrix4(t),this.direction.transformDirection(t),this}equals(t){return t.origin.equals(this.origin)&&t.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}},ce=class extends Qn{constructor(t){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new ft(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Ze,this.combine=Ir,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(t)}copy(t){return super.copy(t),this.color.copy(t.color),this.map=t.map,this.lightMap=t.lightMap,this.lightMapIntensity=t.lightMapIntensity,this.aoMap=t.aoMap,this.aoMapIntensity=t.aoMapIntensity,this.specularMap=t.specularMap,this.alphaMap=t.alphaMap,this.envMap=t.envMap,this.envMapRotation.copy(t.envMapRotation),this.combine=t.combine,this.reflectivity=t.reflectivity,this.refractionRatio=t.refractionRatio,this.wireframe=t.wireframe,this.wireframeLinewidth=t.wireframeLinewidth,this.wireframeLinecap=t.wireframeLinecap,this.wireframeLinejoin=t.wireframeLinejoin,this.fog=t.fog,this}},No=new lt,Xe=new jn,Ri=new Pe,Uo=new _,Ci=new _,Ii=new _,Pi=new _,Qs=new _,Li=new _,Fo=new _,Di=new _,D=class extends Yt{constructor(t=new Pt,e=new ce){super(),this.isMesh=!0,this.type="Mesh",this.geometry=t,this.material=e,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(t,e){return super.copy(t,e),t.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=t.morphTargetInfluences.slice()),t.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},t.morphTargetDictionary)),this.material=Array.isArray(t.material)?t.material.slice():t.material,this.geometry=t.geometry,this}updateMorphTargets(){let e=this.geometry.morphAttributes,n=Object.keys(e);if(n.length>0){let i=e[n[0]];if(i!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,r=i.length;s<r;s++){let a=i[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[a]=s}}}}getVertexPosition(t,e){let n=this.geometry,i=n.attributes.position,s=n.morphAttributes.position,r=n.morphTargetsRelative;e.fromBufferAttribute(i,t);let a=this.morphTargetInfluences;if(s&&a){Li.set(0,0,0);for(let l=0,c=s.length;l<c;l++){let u=a[l],d=s[l];u!==0&&(Qs.fromBufferAttribute(d,t),r?Li.addScaledVector(Qs,u):Li.addScaledVector(Qs.sub(e),u))}e.add(Li)}return e}intersectsFrustum(t){return t.intersectsObject(this)}raycast(t,e){let n=this.geometry,i=this.material,s=this.matrixWorld;i!==void 0&&(n.boundingSphere===null&&n.computeBoundingSphere(),Ri.copy(n.boundingSphere),Ri.applyMatrix4(s),Xe.copy(t.ray).recast(t.near),!(Ri.containsPoint(Xe.origin)===!1&&(Xe.intersectSphere(Ri,Uo)===null||Xe.origin.distanceToSquared(Uo)>(t.far-t.near)**2))&&(No.copy(s).invert(),Xe.copy(t.ray).applyMatrix4(No),!(n.boundingBox!==null&&Xe.intersectsBox(n.boundingBox)===!1)&&this._computeIntersections(t,e,Xe)))}_computeIntersections(t,e,n){let i,s=this.geometry,r=this.material,a=s.index,l=s.attributes.position,c=s.attributes.uv,u=s.attributes.uv1,d=s.attributes.normal,h=s.groups,f=s.drawRange;if(a!==null)if(Array.isArray(r))for(let p=0,m=h.length;p<m;p++){let x=h[p],v=r[x.materialIndex],S=Math.max(x.start,f.start),y=Math.min(a.count,Math.min(x.start+x.count,f.start+f.count));for(let M=S,A=y;M<A;M+=3){let b=a.getX(M),R=a.getX(M+1),T=a.getX(M+2);i=Ni(this,v,t,n,c,u,d,b,R,T),i&&(i.faceIndex=Math.floor(M/3),i.face.materialIndex=x.materialIndex,e.push(i))}}else{let p=Math.max(0,f.start),m=Math.min(a.count,f.start+f.count);for(let x=p,v=m;x<v;x+=3){let S=a.getX(x),y=a.getX(x+1),M=a.getX(x+2);i=Ni(this,r,t,n,c,u,d,S,y,M),i&&(i.faceIndex=Math.floor(x/3),e.push(i))}}else if(l!==void 0)if(Array.isArray(r))for(let p=0,m=h.length;p<m;p++){let x=h[p],v=r[x.materialIndex],S=Math.max(x.start,f.start),y=Math.min(l.count,Math.min(x.start+x.count,f.start+f.count));for(let M=S,A=y;M<A;M+=3){let b=M,R=M+1,T=M+2;i=Ni(this,v,t,n,c,u,d,b,R,T),i&&(i.faceIndex=Math.floor(M/3),i.face.materialIndex=x.materialIndex,e.push(i))}}else{let p=Math.max(0,f.start),m=Math.min(l.count,f.start+f.count);for(let x=p,v=m;x<v;x+=3){let S=x,y=x+1,M=x+2;i=Ni(this,r,t,n,c,u,d,S,y,M),i&&(i.faceIndex=Math.floor(x/3),e.push(i))}}}};function Wl(o,t,e,n,i,s,r,a){let l;if(t.side===hi?l=n.intersectTriangle(r,s,i,!0,a):l=n.intersectTriangle(i,s,r,t.side===Cr,a),l===null)return null;Di.copy(a),Di.applyMatrix4(o.matrixWorld);let c=e.ray.origin.distanceTo(Di);return c<e.near||c>e.far?null:{distance:c,point:Di.clone(),object:o}}function Ni(o,t,e,n,i,s,r,a,l,c){o.getVertexPosition(a,Ci),o.getVertexPosition(l,Ii),o.getVertexPosition(c,Pi);let u=Wl(o,t,e,n,Ci,Ii,Pi,Fo);if(u){let d=new _;Ae.getBarycoord(Fo,Ci,Ii,Pi,d),i&&(u.uv=Ae.getInterpolatedAttribute(i,a,l,c,d,new O)),s&&(u.uv1=Ae.getInterpolatedAttribute(s,a,l,c,d,new O)),r&&(u.normal=Ae.getInterpolatedAttribute(r,a,l,c,d,new _),u.normal.dot(n.direction)>0&&u.normal.multiplyScalar(-1));let h={a,b:l,c,normal:new _,materialIndex:0};Ae.getNormal(Ci,Ii,Pi,h.normal),u.face=h,u.barycoord=d}return u}var Qi=class extends Ie{constructor(t=null,e=1,n=1,i,s,r,a,l,c=fr,u=fr,d,h){super(null,r,a,l,c,u,i,s,d,h),this.isDataTexture=!0,this.image={data:t,width:e,height:n},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}};var Tn=class extends te{constructor(t,e,n,i=1){super(t,e,n),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=i}copy(t){return super.copy(t),this.meshPerAttribute=t.meshPerAttribute,this}toJSON(){let t=super.toJSON();return t.meshPerAttribute=this.meshPerAttribute,t.isInstancedBufferAttribute=!0,t}},_n=new lt,Bo=new lt,Ui=[],Oo=new ee,Xl=new lt,Hn=new D,Vn=new Pe,An=class extends D{constructor(t,e,n){super(t,e),this.isInstancedMesh=!0,this.instanceMatrix=new Tn(new Float32Array(n*16),16),this.instanceColor=null,this.morphTexture=null,this.count=n,this.boundingBox=null,this.boundingSphere=null;for(let i=0;i<n;i++)this.setMatrixAt(i,Xl)}computeBoundingBox(){let t=this.geometry,e=this.count;this.boundingBox===null&&(this.boundingBox=new ee),t.boundingBox===null&&t.computeBoundingBox(),this.boundingBox.makeEmpty();for(let n=0;n<e;n++)this.getMatrixAt(n,_n),Oo.copy(t.boundingBox).applyMatrix4(_n),this.boundingBox.union(Oo)}computeBoundingSphere(){let t=this.geometry,e=this.count;this.boundingSphere===null&&(this.boundingSphere=new Pe),t.boundingSphere===null&&t.computeBoundingSphere(),this.boundingSphere.makeEmpty();for(let n=0;n<e;n++)this.getMatrixAt(n,_n),Vn.copy(t.boundingSphere).applyMatrix4(_n),this.boundingSphere.union(Vn)}copy(t,e){return super.copy(t,e),this.instanceMatrix.copy(t.instanceMatrix),t.morphTexture!==null&&(this.morphTexture=t.morphTexture.clone()),t.instanceColor!==null&&(this.instanceColor=t.instanceColor.clone()),this.count=t.count,t.boundingBox!==null&&(this.boundingBox=t.boundingBox.clone()),t.boundingSphere!==null&&(this.boundingSphere=t.boundingSphere.clone()),this}getColorAt(t,e){return this.instanceColor===null?e.setRGB(1,1,1):e.fromArray(this.instanceColor.array,t*3)}getMatrixAt(t,e){return e.fromArray(this.instanceMatrix.array,t*16)}getMorphAt(t,e){let n=e.morphTargetInfluences,i=this.morphTexture.source.data.data,s=n.length+1,r=t*s+1;for(let a=0;a<n.length;a++)n[a]=i[r+a]}raycast(t,e){let n=this.matrixWorld,i=this.count;if(Hn.geometry=this.geometry,Hn.material=this.material,Hn.material!==void 0&&(this.boundingSphere===null&&this.computeBoundingSphere(),Vn.copy(this.boundingSphere),Vn.applyMatrix4(n),t.ray.intersectsSphere(Vn)!==!1))for(let s=0;s<i;s++){this.getMatrixAt(s,_n),Bo.multiplyMatrices(n,_n),Hn.matrixWorld=Bo,Hn.raycast(t,Ui);for(let r=0,a=Ui.length;r<a;r++){let l=Ui[r];l.instanceId=s,l.object=this,e.push(l)}Ui.length=0}}setColorAt(t,e){return this.instanceColor===null&&(this.instanceColor=new Tn(new Float32Array(this.instanceMatrix.count*3).fill(1),3)),e.toArray(this.instanceColor.array,t*3),this}setMatrixAt(t,e){return e.toArray(this.instanceMatrix.array,t*16),this}setMorphAt(t,e){let n=e.morphTargetInfluences,i=n.length+1;this.morphTexture===null&&(this.morphTexture=new Qi(new Float32Array(i*this.count),i,this.count,fa,Hr));let s=this.morphTexture.source.data.data,r=0;for(let c=0;c<n.length;c++)r+=n[c];let a=this.geometry.morphTargetsRelative?1:1-r,l=i*t;return s[l]=a,s.set(n,l+1),this}updateMorphTargets(){}dispose(){super.dispose(),this.morphTexture!==null&&(this.morphTexture.dispose(),this.morphTexture=null)}},$e=new Pe,$l=new O(.5,.5),Fi=new _,ji=class{constructor(t=new qt,e=new qt,n=new qt,i=new qt,s=new qt,r=new qt){this.planes=[t,e,n,i,s,r]}set(t,e,n,i,s,r){let a=this.planes;return a[0].copy(t),a[1].copy(e),a[2].copy(n),a[3].copy(i),a[4].copy(s),a[5].copy(r),this}copy(t){let e=this.planes;for(let n=0;n<6;n++)e[n].copy(t.planes[n]);return this}setFromProjectionMatrix(t,e=Re,n=!1){let i=this.planes,s=t.elements,r=s[0],a=s[1],l=s[2],c=s[3],u=s[4],d=s[5],h=s[6],f=s[7],p=s[8],m=s[9],x=s[10],v=s[11],S=s[12],y=s[13],M=s[14],A=s[15];if(i[0].setComponents(c-r,f-u,v-p,A-S).normalize(),i[1].setComponents(c+r,f+u,v+p,A+S).normalize(),i[2].setComponents(c+a,f+d,v+m,A+y).normalize(),i[3].setComponents(c-a,f-d,v-m,A-y).normalize(),n)i[4].setComponents(l,h,x,M).normalize(),i[5].setComponents(c-l,f-h,v-x,A-M).normalize();else if(i[4].setComponents(c-l,f-h,v-x,A-M).normalize(),e===Re)i[5].setComponents(c+l,f+h,v+x,A+M).normalize();else if(e===Jn)i[5].setComponents(l,h,x,M).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+e);return this}intersectsObject(t){if(t.boundingSphere!==void 0)t.boundingSphere===null&&t.computeBoundingSphere(),$e.copy(t.boundingSphere).applyMatrix4(t.matrixWorld);else{let e=t.geometry;e.boundingSphere===null&&e.computeBoundingSphere(),$e.copy(e.boundingSphere).applyMatrix4(t.matrixWorld)}return this.intersectsSphere($e)}intersectsSprite(t){$e.center.set(0,0,0);let e=$l.distanceTo(t.center);return $e.radius=.7071067811865476+e,$e.applyMatrix4(t.matrixWorld),this.intersectsSphere($e)}intersectsSphere(t){let e=this.planes,n=t.center,i=-t.radius;for(let s=0;s<6;s++)if(e[s].distanceToPoint(n)<i)return!1;return!0}intersectsBox(t){let e=this.planes;for(let n=0;n<6;n++){let i=e[n];if(Fi.x=i.normal.x>0?t.max.x:t.min.x,Fi.y=i.normal.y>0?t.max.y:t.min.y,Fi.z=i.normal.z>0?t.max.z:t.min.z,i.distanceToPoint(Fi)<0)return!1}return!0}containsPoint(t){let e=this.planes;for(let n=0;n<6;n++)if(e[n].distanceToPoint(t)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}};var Rn=class extends Ie{constructor(t,e,n,i,s,r,a,l,c){super(t,e,n,i,s,r,a,l,c),this.isCanvasTexture=!0,this.needsUpdate=!0}};var ot=class o extends Pt{constructor(t=1,e=1,n=1,i=1,s=1,r=1){super(),this.type="BoxGeometry",this.parameters={width:t,height:e,depth:n,widthSegments:i,heightSegments:s,depthSegments:r};let a=this;i=Math.floor(i),s=Math.floor(s),r=Math.floor(r);let l=[],c=[],u=[],d=[],h=0,f=0;p("z","y","x",-1,-1,n,e,t,r,s,0),p("z","y","x",1,-1,n,e,-t,r,s,1),p("x","z","y",1,1,t,n,e,i,r,2),p("x","z","y",1,-1,t,n,-e,i,r,3),p("x","y","z",1,-1,t,e,n,i,s,4),p("x","y","z",-1,-1,t,e,-n,i,s,5),this.setIndex(l),this.setAttribute("position",new ct(c,3)),this.setAttribute("normal",new ct(u,3)),this.setAttribute("uv",new ct(d,2));function p(m,x,v,S,y,M,A,b,R,T,I){let C=M/R,P=A/T,k=M/2,w=A/2,U=b/2,L=R+1,V=T+1,X=0,J=0,K=new _;for(let E=0;E<V;E++){let N=E*P-w;for(let H=0;H<L;H++){let $=H*C-k;K[m]=$*S,K[x]=N*y,K[v]=U,c.push(K.x,K.y,K.z),K[m]=0,K[x]=0,K[v]=b>0?1:-1,u.push(K.x,K.y,K.z),d.push(H/R),d.push(1-E/T),X+=1}}for(let E=0;E<T;E++)for(let N=0;N<R;N++){let H=h+N+L*E,$=h+N+L*(E+1),ut=h+(N+1)+L*(E+1),_t=h+(N+1)+L*E;l.push(H,$,_t),l.push($,ut,_t),J+=6}a.addGroup(f,J,I),f+=J,h+=X}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new o(t.width,t.height,t.depth,t.widthSegments,t.heightSegments,t.depthSegments)}};var ae=class o extends Pt{constructor(t=1,e=32,n=0,i=Math.PI*2){super(),this.type="CircleGeometry",this.parameters={radius:t,segments:e,thetaStart:n,thetaLength:i},e=Math.max(3,e);let s=[],r=[],a=[],l=[],c=new _,u=new O;r.push(0,0,0),a.push(0,0,1),l.push(.5,.5);for(let d=0,h=3;d<=e;d++,h+=3){let f=n+d/e*i;c.x=t*Math.cos(f),c.y=t*Math.sin(f),r.push(c.x,c.y,c.z),a.push(0,0,1),u.x=(r[h]/t+1)/2,u.y=(r[h+1]/t+1)/2,l.push(u.x,u.y)}for(let d=1;d<=e;d++)s.push(d,d+1,0);this.setIndex(s),this.setAttribute("position",new ct(r,3)),this.setAttribute("normal",new ct(a,3)),this.setAttribute("uv",new ct(l,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new o(t.radius,t.segments,t.thetaStart,t.thetaLength)}},Tt=class o extends Pt{constructor(t=1,e=1,n=1,i=32,s=1,r=!1,a=0,l=Math.PI*2){super(),this.type="CylinderGeometry",this.parameters={radiusTop:t,radiusBottom:e,height:n,radialSegments:i,heightSegments:s,openEnded:r,thetaStart:a,thetaLength:l};let c=this;i=Math.floor(i),s=Math.floor(s);let u=[],d=[],h=[],f=[],p=0,m=[],x=n/2,v=0;S(),r===!1&&(t>0&&y(!0),e>0&&y(!1)),this.setIndex(u),this.setAttribute("position",new ct(d,3)),this.setAttribute("normal",new ct(h,3)),this.setAttribute("uv",new ct(f,2));function S(){let M=new _,A=new _,b=0,R=(e-t)/n;for(let T=0;T<=s;T++){let I=[],C=T/s,P=C*(e-t)+t;for(let k=0;k<=i;k++){let w=k/i,U=w*l+a,L=Math.sin(U),V=Math.cos(U);A.x=P*L,A.y=-C*n+x,A.z=P*V,d.push(A.x,A.y,A.z),M.set(L,R,V).normalize(),h.push(M.x,M.y,M.z),f.push(w,1-C),I.push(p++)}m.push(I)}for(let T=0;T<i;T++)for(let I=0;I<s;I++){let C=m[I][T],P=m[I+1][T],k=m[I+1][T+1],w=m[I][T+1];(t>0||I!==0)&&(u.push(C,P,w),b+=3),(e>0||I!==s-1)&&(u.push(P,k,w),b+=3)}c.addGroup(v,b,0),v+=b}function y(M){let A=p,b=new O,R=new _,T=0,I=M===!0?t:e,C=M===!0?1:-1;for(let k=1;k<=i;k++)d.push(0,x*C,0),h.push(0,C,0),f.push(.5,.5),p++;let P=p;for(let k=0;k<=i;k++){let U=k/i*l+a,L=Math.cos(U),V=Math.sin(U);R.x=I*V,R.y=x*C,R.z=I*L,d.push(R.x,R.y,R.z),h.push(0,C,0),b.x=L*.5+.5,b.y=V*.5*C+.5,f.push(b.x,b.y),p++}for(let k=0;k<i;k++){let w=A+k,U=P+k;M===!0?u.push(U,U+1,w):u.push(U+1,U,w),T+=3}c.addGroup(v,T,M===!0?1:2),v+=T}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new o(t.radiusTop,t.radiusBottom,t.height,t.radialSegments,t.heightSegments,t.openEnded,t.thetaStart,t.thetaLength)}};var Zt=class{constructor(){this.type="Curve",this.arcLengthDivisions=200,this.needsUpdate=!1,this.cacheArcLengths=null}getPoint(){St("Curve: .getPoint() not implemented.")}getPointAt(t,e){let n=this.getUtoTmapping(t);return this.getPoint(n,e)}getPoints(t=5){let e=[];for(let n=0;n<=t;n++)e.push(this.getPoint(n/t));return e}getSpacedPoints(t=5){let e=[];for(let n=0;n<=t;n++)e.push(this.getPointAt(n/t));return e}getLength(){let t=this.getLengths();return t[t.length-1]}getLengths(t=this.arcLengthDivisions){if(this.cacheArcLengths&&this.cacheArcLengths.length===t+1&&!this.needsUpdate)return this.cacheArcLengths;this.needsUpdate=!1;let e=[],n,i=this.getPoint(0),s=0;e.push(0);for(let r=1;r<=t;r++)n=this.getPoint(r/t),s+=n.distanceTo(i),e.push(s),i=n;return this.cacheArcLengths=e,e}updateArcLengths(){this.needsUpdate=!0,this.getLengths()}getUtoTmapping(t,e=null){let n=this.getLengths(),i=0,s=n.length,r;e?r=e:r=t*n[s-1];let a=0,l=s-1,c;for(;a<=l;)if(i=Math.floor(a+(l-a)/2),c=n[i]-r,c<0)a=i+1;else if(c>0)l=i-1;else{l=i;break}if(i=l,n[i]===r)return i/(s-1);let u=n[i],h=n[i+1]-u,f=(r-u)/h;return(i+f)/(s-1)}getTangent(t,e){let i=t-1e-4,s=t+1e-4;i<0&&(i=0),s>1&&(s=1);let r=this.getPoint(i),a=this.getPoint(s),l=e||(r.isVector2?new O:new _);return l.copy(a).sub(r).normalize(),l}getTangentAt(t,e){let n=this.getUtoTmapping(t);return this.getTangent(n,e)}computeFrenetFrames(t,e=!1){let n=new _,i=[],s=[],r=[],a=new _,l=new lt;for(let f=0;f<=t;f++){let p=f/t;i[f]=this.getTangentAt(p,new _)}s[0]=new _,r[0]=new _;let c=Number.MAX_VALUE,u=Math.abs(i[0].x),d=Math.abs(i[0].y),h=Math.abs(i[0].z);u<=c&&(c=u,n.set(1,0,0)),d<=c&&(c=d,n.set(0,1,0)),h<=c&&n.set(0,0,1),a.crossVectors(i[0],n).normalize(),s[0].crossVectors(i[0],a),r[0].crossVectors(i[0],s[0]);for(let f=1;f<=t;f++){if(s[f]=s[f-1].clone(),r[f]=r[f-1].clone(),a.crossVectors(i[f-1],i[f]),a.length()>Number.EPSILON){a.normalize();let p=Math.acos(Q(i[f-1].dot(i[f]),-1,1));s[f].applyMatrix4(l.makeRotationAxis(a,p))}r[f].crossVectors(i[f],s[f])}if(e===!0){let f=Math.acos(Q(s[0].dot(s[t]),-1,1));f/=t,i[0].dot(a.crossVectors(s[0],s[t]))>0&&(f=-f);for(let p=1;p<=t;p++)s[p].applyMatrix4(l.makeRotationAxis(i[p],f*p)),r[p].crossVectors(i[p],s[p])}return{tangents:i,normals:s,binormals:r}}clone(){return new this.constructor().copy(this)}copy(t){return this.arcLengthDivisions=t.arcLengthDivisions,this}toJSON(){let t={metadata:{version:4.7,type:"Curve",generator:"Curve.toJSON"}};return t.arcLengthDivisions=this.arcLengthDivisions,t.type=this.type,t}fromJSON(t){return this.arcLengthDivisions=t.arcLengthDivisions,this}},Cn=class extends Zt{constructor(t=0,e=0,n=1,i=1,s=0,r=Math.PI*2,a=!1,l=0){super(),this.isEllipseCurve=!0,this.type="EllipseCurve",this.aX=t,this.aY=e,this.xRadius=n,this.yRadius=i,this.aStartAngle=s,this.aEndAngle=r,this.aClockwise=a,this.aRotation=l}getPoint(t,e=new O){let n=e,i=Math.PI*2,s=this.aEndAngle-this.aStartAngle,r=Math.abs(s)<Number.EPSILON;for(;s<0;)s+=i;for(;s>i;)s-=i;s<Number.EPSILON&&(r?s=0:s=i),this.aClockwise===!0&&!r&&(s===i?s=-i:s=s-i);let a=this.aStartAngle+t*s,l=this.aX+this.xRadius*Math.cos(a),c=this.aY+this.yRadius*Math.sin(a);if(this.aRotation!==0){let u=Math.cos(this.aRotation),d=Math.sin(this.aRotation),h=l-this.aX,f=c-this.aY;l=h*u-f*d+this.aX,c=h*d+f*u+this.aY}return n.set(l,c)}copy(t){return super.copy(t),this.aX=t.aX,this.aY=t.aY,this.xRadius=t.xRadius,this.yRadius=t.yRadius,this.aStartAngle=t.aStartAngle,this.aEndAngle=t.aEndAngle,this.aClockwise=t.aClockwise,this.aRotation=t.aRotation,this}toJSON(){let t=super.toJSON();return t.aX=this.aX,t.aY=this.aY,t.xRadius=this.xRadius,t.yRadius=this.yRadius,t.aStartAngle=this.aStartAngle,t.aEndAngle=this.aEndAngle,t.aClockwise=this.aClockwise,t.aRotation=this.aRotation,t}fromJSON(t){return super.fromJSON(t),this.aX=t.aX,this.aY=t.aY,this.xRadius=t.xRadius,this.yRadius=t.yRadius,this.aStartAngle=t.aStartAngle,this.aEndAngle=t.aEndAngle,this.aClockwise=t.aClockwise,this.aRotation=t.aRotation,this}},ts=class extends Cn{constructor(t,e,n,i,s,r){super(t,e,n,n,i,s,r),this.isArcCurve=!0,this.type="ArcCurve"}};function Xr(){let o=0,t=0,e=0,n=0;function i(s,r,a,l){o=s,t=a,e=-3*s+3*r-2*a-l,n=2*s-2*r+a+l}return{initCatmullRom:function(s,r,a,l,c){i(r,a,c*(a-s),c*(l-r))},initNonuniformCatmullRom:function(s,r,a,l,c,u,d){let h=(r-s)/c-(a-s)/(c+u)+(a-r)/u,f=(a-r)/u-(l-r)/(u+d)+(l-a)/d;h*=u,f*=u,i(r,a,h,f)},calc:function(s){let r=s*s,a=r*s;return o+t*s+e*r+n*a}}}var ko=new _,zo=new _,js=new Xr,tr=new Xr,er=new Xr,Le=class extends Zt{constructor(t=[],e=!1,n="centripetal",i=.5){super(),this.isCatmullRomCurve3=!0,this.type="CatmullRomCurve3",this.points=t,this.closed=e,this.curveType=n,this.tension=i}getPoint(t,e=new _){let n=e,i=this.points,s=i.length,r=(s-(this.closed?0:1))*t,a=Math.floor(r),l=r-a;this.closed?a+=a>0?0:(Math.floor(Math.abs(a)/s)+1)*s:l===0&&a===s-1&&(a=s-2,l=1);let c,u;this.closed||a>0?c=i[(a-1)%s]:(zo.subVectors(i[0],i[1]).add(i[0]),c=zo);let d=i[a%s],h=i[(a+1)%s];if(this.closed||a+2<s?u=i[(a+2)%s]:(ko.subVectors(i[s-1],i[s-2]).add(i[s-1]),u=ko),this.curveType==="centripetal"||this.curveType==="chordal"){let f=this.curveType==="chordal"?.5:.25,p=Math.pow(c.distanceToSquared(d),f),m=Math.pow(d.distanceToSquared(h),f),x=Math.pow(h.distanceToSquared(u),f);m<1e-4&&(m=1),p<1e-4&&(p=m),x<1e-4&&(x=m),js.initNonuniformCatmullRom(c.x,d.x,h.x,u.x,p,m,x),tr.initNonuniformCatmullRom(c.y,d.y,h.y,u.y,p,m,x),er.initNonuniformCatmullRom(c.z,d.z,h.z,u.z,p,m,x)}else this.curveType==="catmullrom"&&(js.initCatmullRom(c.x,d.x,h.x,u.x,this.tension),tr.initCatmullRom(c.y,d.y,h.y,u.y,this.tension),er.initCatmullRom(c.z,d.z,h.z,u.z,this.tension));return n.set(js.calc(l),tr.calc(l),er.calc(l)),n}copy(t){super.copy(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let i=t.points[e];this.points.push(i.clone())}return this.closed=t.closed,this.curveType=t.curveType,this.tension=t.tension,this}toJSON(){let t=super.toJSON();t.points=[];for(let e=0,n=this.points.length;e<n;e++){let i=this.points[e];t.points.push(i.toArray())}return t.closed=this.closed,t.curveType=this.curveType,t.tension=this.tension,t}fromJSON(t){super.fromJSON(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let i=t.points[e];this.points.push(new _().fromArray(i))}return this.closed=t.closed,this.curveType=t.curveType,this.tension=t.tension,this}};function Ho(o,t,e,n,i){let s=(n-t)*.5,r=(i-e)*.5,a=o*o,l=o*a;return(2*e-2*n+s+r)*l+(-3*e+3*n-2*s-r)*a+s*o+e}function ql(o,t){let e=1-o;return e*e*t}function Yl(o,t){return 2*(1-o)*o*t}function Zl(o,t){return o*o*t}function qn(o,t,e,n){return ql(o,t)+Yl(o,e)+Zl(o,n)}function Jl(o,t){let e=1-o;return e*e*e*t}function Kl(o,t){let e=1-o;return 3*e*e*o*t}function Ql(o,t){return 3*(1-o)*o*o*t}function jl(o,t){return o*o*o*t}function Yn(o,t,e,n,i){return Jl(o,t)+Kl(o,e)+Ql(o,n)+jl(o,i)}var ti=class extends Zt{constructor(t=new O,e=new O,n=new O,i=new O){super(),this.isCubicBezierCurve=!0,this.type="CubicBezierCurve",this.v0=t,this.v1=e,this.v2=n,this.v3=i}getPoint(t,e=new O){let n=e,i=this.v0,s=this.v1,r=this.v2,a=this.v3;return n.set(Yn(t,i.x,s.x,r.x,a.x),Yn(t,i.y,s.y,r.y,a.y)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this.v3.copy(t.v3),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t.v3=this.v3.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this.v3.fromArray(t.v3),this}},es=class extends Zt{constructor(t=new _,e=new _,n=new _,i=new _){super(),this.isCubicBezierCurve3=!0,this.type="CubicBezierCurve3",this.v0=t,this.v1=e,this.v2=n,this.v3=i}getPoint(t,e=new _){let n=e,i=this.v0,s=this.v1,r=this.v2,a=this.v3;return n.set(Yn(t,i.x,s.x,r.x,a.x),Yn(t,i.y,s.y,r.y,a.y),Yn(t,i.z,s.z,r.z,a.z)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this.v3.copy(t.v3),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t.v3=this.v3.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this.v3.fromArray(t.v3),this}},ei=class extends Zt{constructor(t=new O,e=new O){super(),this.isLineCurve=!0,this.type="LineCurve",this.v1=t,this.v2=e}getPoint(t,e=new O){let n=e;return t===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(t).add(this.v1)),n}getPointAt(t,e){return this.getPoint(t,e)}getTangent(t,e=new O){return e.subVectors(this.v2,this.v1).normalize()}getTangentAt(t,e){return this.getTangent(t,e)}copy(t){return super.copy(t),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},ns=class extends Zt{constructor(t=new _,e=new _){super(),this.isLineCurve3=!0,this.type="LineCurve3",this.v1=t,this.v2=e}getPoint(t,e=new _){let n=e;return t===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(t).add(this.v1)),n}getPointAt(t,e){return this.getPoint(t,e)}getTangent(t,e=new _){return e.subVectors(this.v2,this.v1).normalize()}getTangentAt(t,e){return this.getTangent(t,e)}copy(t){return super.copy(t),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},ni=class extends Zt{constructor(t=new O,e=new O,n=new O){super(),this.isQuadraticBezierCurve=!0,this.type="QuadraticBezierCurve",this.v0=t,this.v1=e,this.v2=n}getPoint(t,e=new O){let n=e,i=this.v0,s=this.v1,r=this.v2;return n.set(qn(t,i.x,s.x,r.x),qn(t,i.y,s.y,r.y)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},In=class extends Zt{constructor(t=new _,e=new _,n=new _){super(),this.isQuadraticBezierCurve3=!0,this.type="QuadraticBezierCurve3",this.v0=t,this.v1=e,this.v2=n}getPoint(t,e=new _){let n=e,i=this.v0,s=this.v1,r=this.v2;return n.set(qn(t,i.x,s.x,r.x),qn(t,i.y,s.y,r.y),qn(t,i.z,s.z,r.z)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},ii=class extends Zt{constructor(t=[]){super(),this.isSplineCurve=!0,this.type="SplineCurve",this.points=t}getPoint(t,e=new O){let n=e,i=this.points,s=(i.length-1)*t,r=Math.floor(s),a=s-r,l=i[r===0?r:r-1],c=i[r],u=i[r>i.length-2?i.length-1:r+1],d=i[r>i.length-3?i.length-1:r+2];return n.set(Ho(a,l.x,c.x,u.x,d.x),Ho(a,l.y,c.y,u.y,d.y)),n}copy(t){super.copy(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let i=t.points[e];this.points.push(i.clone())}return this}toJSON(){let t=super.toJSON();t.points=[];for(let e=0,n=this.points.length;e<n;e++){let i=this.points[e];t.points.push(i.toArray())}return t}fromJSON(t){super.fromJSON(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let i=t.points[e];this.points.push(new O().fromArray(i))}return this}},Mr=Object.freeze({__proto__:null,ArcCurve:ts,CatmullRomCurve3:Le,CubicBezierCurve:ti,CubicBezierCurve3:es,EllipseCurve:Cn,LineCurve:ei,LineCurve3:ns,QuadraticBezierCurve:ni,QuadraticBezierCurve3:In,SplineCurve:ii}),is=class extends Zt{constructor(){super(),this.type="CurvePath",this.curves=[],this.autoClose=!1}add(t){this.curves.push(t)}closePath(){let t=this.curves[0].getPoint(0),e=this.curves[this.curves.length-1].getPoint(1);if(!t.equals(e)){let n=t.isVector2===!0?"LineCurve":"LineCurve3";this.curves.push(new Mr[n](e,t))}return this}getPoint(t,e){let n=t*this.getLength(),i=this.getCurveLengths(),s=0;for(;s<i.length;){if(i[s]>=n){let r=i[s]-n,a=this.curves[s],l=a.getLength(),c=l===0?0:1-r/l;return a.getPointAt(c,e)}s++}return null}getLength(){let t=this.getCurveLengths();return t[t.length-1]}updateArcLengths(){this.needsUpdate=!0,this.cacheLengths=null,this.getCurveLengths()}getCurveLengths(){if(this.cacheLengths&&this.cacheLengths.length===this.curves.length)return this.cacheLengths;let t=[],e=0;for(let n=0,i=this.curves.length;n<i;n++)e+=this.curves[n].getLength(),t.push(e);return this.cacheLengths=t,t}getSpacedPoints(t=40){let e=[];for(let n=0;n<=t;n++)e.push(this.getPoint(n/t));return this.autoClose&&e.push(e[0]),e}getPoints(t=12){let e=[],n;for(let i=0,s=this.curves;i<s.length;i++){let r=s[i],a=r.isEllipseCurve?t*2:r.isLineCurve||r.isLineCurve3?1:r.isSplineCurve?t*r.points.length:t,l=r.getPoints(a);for(let c=0;c<l.length;c++){let u=l[c];n&&n.equals(u)||(e.push(u),n=u)}}return this.autoClose&&e.length>1&&!e[e.length-1].equals(e[0])&&e.push(e[0]),e}copy(t){super.copy(t),this.curves=[];for(let e=0,n=t.curves.length;e<n;e++){let i=t.curves[e];this.curves.push(i.clone())}return this.autoClose=t.autoClose,this}toJSON(){let t=super.toJSON();t.autoClose=this.autoClose,t.curves=[];for(let e=0,n=this.curves.length;e<n;e++){let i=this.curves[e];t.curves.push(i.toJSON())}return t}fromJSON(t){super.fromJSON(t),this.autoClose=t.autoClose,this.curves=[];for(let e=0,n=t.curves.length;e<n;e++){let i=t.curves[e];this.curves.push(new Mr[i.type]().fromJSON(i))}return this}},Je=class extends is{constructor(t){super(),this.type="Path",this.currentPoint=new O,t&&this.setFromPoints(t)}setFromPoints(t){this.moveTo(t[0].x,t[0].y);for(let e=1,n=t.length;e<n;e++)this.lineTo(t[e].x,t[e].y);return this}moveTo(t,e){return this.currentPoint.set(t,e),this}lineTo(t,e){let n=new ei(this.currentPoint.clone(),new O(t,e));return this.curves.push(n),this.currentPoint.set(t,e),this}quadraticCurveTo(t,e,n,i){let s=new ni(this.currentPoint.clone(),new O(t,e),new O(n,i));return this.curves.push(s),this.currentPoint.set(n,i),this}bezierCurveTo(t,e,n,i,s,r){let a=new ti(this.currentPoint.clone(),new O(t,e),new O(n,i),new O(s,r));return this.curves.push(a),this.currentPoint.set(s,r),this}splineThru(t){let e=[this.currentPoint.clone()].concat(t),n=new ii(e);return this.curves.push(n),this.currentPoint.copy(t[t.length-1]),this}arc(t,e,n,i,s,r){let a=this.currentPoint.x,l=this.currentPoint.y;return this.absarc(t+a,e+l,n,i,s,r),this}absarc(t,e,n,i,s,r){return this.absellipse(t,e,n,n,i,s,r),this}ellipse(t,e,n,i,s,r,a,l){let c=this.currentPoint.x,u=this.currentPoint.y;return this.absellipse(t+c,e+u,n,i,s,r,a,l),this}absellipse(t,e,n,i,s,r,a,l){let c=new Cn(t,e,n,i,s,r,a,l);if(this.curves.length>0){let d=c.getPoint(0);d.equals(this.currentPoint)||this.lineTo(d.x,d.y)}this.curves.push(c);let u=c.getPoint(1);return this.currentPoint.copy(u),this}copy(t){return super.copy(t),this.currentPoint.copy(t.currentPoint),this}toJSON(){let t=super.toJSON();return t.currentPoint=this.currentPoint.toArray(),t}fromJSON(t){return super.fromJSON(t),this.currentPoint.fromArray(t.currentPoint),this}},ye=class extends Je{constructor(t){super(t),this.uuid=je(),this.type="Shape",this.holes=[]}getPointsHoles(t){let e=[];for(let n=0,i=this.holes.length;n<i;n++)e[n]=this.holes[n].getPoints(t);return e}extractPoints(t){return{shape:this.getPoints(t),holes:this.getPointsHoles(t)}}copy(t){super.copy(t),this.holes=[];for(let e=0,n=t.holes.length;e<n;e++){let i=t.holes[e];this.holes.push(i.clone())}return this}toJSON(){let t=super.toJSON();t.uuid=this.uuid,t.holes=[];for(let e=0,n=this.holes.length;e<n;e++){let i=this.holes[e];t.holes.push(i.toJSON())}return t}fromJSON(t){super.fromJSON(t),this.uuid=t.uuid,this.holes=[];for(let e=0,n=t.holes.length;e<n;e++){let i=t.holes[e];this.holes.push(new Je().fromJSON(i))}return this}};function tc(o,t,e=2){let n=t&&t.length,i=n?t[0]*e:o.length,s=ya(o,0,i,e,!0),r=[];if(!s||s.next===s.prev)return r;let a,l,c;if(n&&(s=rc(o,t,s,e)),o.length>80*e){a=o[0],l=o[1];let u=a,d=l;for(let h=e;h<i;h+=e){let f=o[h],p=o[h+1];f<a&&(a=f),p<l&&(l=p),f>u&&(u=f),p>d&&(d=p)}c=Math.max(u-a,d-l),c=c!==0?32767/c:0}return si(s,r,e,a,l,c,0),r}function ya(o,t,e,n,i){let s;if(i===gc(o,t,e,n)>0)for(let r=t;r<e;r+=n)s=Vo(r/n|0,o[r],o[r+1],s);else for(let r=e-n;r>=t;r-=n)s=Vo(r/n|0,o[r],o[r+1],s);return s&&Pn(s,s.next)&&(oi(s),s=s.next),s}function Ke(o,t){if(!o)return o;t||(t=o);let e=o,n;do if(n=!1,!e.steiner&&(Pn(e,e.next)||vt(e.prev,e,e.next)===0)){if(oi(e),e=t=e.prev,e===e.next)break;n=!0}else e=e.next;while(n||e!==t);return t}function si(o,t,e,n,i,s,r){if(!o)return;!r&&s&&uc(o,n,i,s);let a=o;for(;o.prev!==o.next;){let l=o.prev,c=o.next;if(s?nc(o,n,i,s):ec(o)){t.push(l.i,o.i,c.i),oi(o),o=c.next,a=c.next;continue}if(o=c,o===a){r?r===1?(o=ic(Ke(o),t),si(o,t,e,n,i,s,2)):r===2&&sc(o,t,e,n,i,s):si(Ke(o),t,e,n,i,s,1);break}}}function ec(o){let t=o.prev,e=o,n=o.next;if(vt(t,e,n)>=0)return!1;let i=t.x,s=e.x,r=n.x,a=t.y,l=e.y,c=n.y,u=Math.min(i,s,r),d=Math.min(a,l,c),h=Math.max(i,s,r),f=Math.max(a,l,c),p=n.next;for(;p!==t;){if(p.x>=u&&p.x<=h&&p.y>=d&&p.y<=f&&Wn(i,a,s,l,r,c,p.x,p.y)&&vt(p.prev,p,p.next)>=0)return!1;p=p.next}return!0}function nc(o,t,e,n){let i=o.prev,s=o,r=o.next;if(vt(i,s,r)>=0)return!1;let a=i.x,l=s.x,c=r.x,u=i.y,d=s.y,h=r.y,f=Math.min(a,l,c),p=Math.min(u,d,h),m=Math.max(a,l,c),x=Math.max(u,d,h),v=Sr(f,p,t,e,n),S=Sr(m,x,t,e,n),y=o.prevZ,M=o.nextZ;for(;y&&y.z>=v&&M&&M.z<=S;){if(y.x>=f&&y.x<=m&&y.y>=p&&y.y<=x&&y!==i&&y!==r&&Wn(a,u,l,d,c,h,y.x,y.y)&&vt(y.prev,y,y.next)>=0||(y=y.prevZ,M.x>=f&&M.x<=m&&M.y>=p&&M.y<=x&&M!==i&&M!==r&&Wn(a,u,l,d,c,h,M.x,M.y)&&vt(M.prev,M,M.next)>=0))return!1;M=M.nextZ}for(;y&&y.z>=v;){if(y.x>=f&&y.x<=m&&y.y>=p&&y.y<=x&&y!==i&&y!==r&&Wn(a,u,l,d,c,h,y.x,y.y)&&vt(y.prev,y,y.next)>=0)return!1;y=y.prevZ}for(;M&&M.z<=S;){if(M.x>=f&&M.x<=m&&M.y>=p&&M.y<=x&&M!==i&&M!==r&&Wn(a,u,l,d,c,h,M.x,M.y)&&vt(M.prev,M,M.next)>=0)return!1;M=M.nextZ}return!0}function ic(o,t){let e=o;do{let n=e.prev,i=e.next.next;!Pn(n,i)&&Ma(n,e,e.next,i)&&ri(n,i)&&ri(i,n)&&(t.push(n.i,e.i,i.i),oi(e),oi(e.next),e=o=i),e=e.next}while(e!==o);return Ke(e)}function sc(o,t,e,n,i,s){let r=o;do{let a=r.next.next;for(;a!==r.prev;){if(r.i!==a.i&&fc(r,a)){let l=Sa(r,a);r=Ke(r,r.next),l=Ke(l,l.next),si(r,t,e,n,i,s,0),si(l,t,e,n,i,s,0);return}a=a.next}r=r.next}while(r!==o)}function rc(o,t,e,n){let i=[];for(let s=0,r=t.length;s<r;s++){let a=t[s]*n,l=s<r-1?t[s+1]*n:o.length,c=ya(o,a,l,n,!1);c===c.next&&(c.steiner=!0),i.push(dc(c))}i.sort(oc);for(let s=0;s<i.length;s++)e=ac(i[s],e);return e}function oc(o,t){let e=o.x-t.x;if(e===0&&(e=o.y-t.y,e===0)){let n=(o.next.y-o.y)/(o.next.x-o.x),i=(t.next.y-t.y)/(t.next.x-t.x);e=n-i}return e}function ac(o,t){let e=lc(o,t);if(!e)return t;let n=Sa(e,o);return Ke(n,n.next),Ke(e,e.next)}function lc(o,t){let e=t,n=o.x,i=o.y,s=-1/0,r;if(Pn(o,e))return e;do{if(Pn(o,e.next))return e.next;if(i<=e.y&&i>=e.next.y&&e.next.y!==e.y){let d=e.x+(i-e.y)*(e.next.x-e.x)/(e.next.y-e.y);if(d<=n&&d>s&&(s=d,r=e.x<e.next.x?e:e.next,d===n))return r}e=e.next}while(e!==t);if(!r)return null;let a=r,l=r.x,c=r.y,u=1/0;e=r;do{if(n>=e.x&&e.x>=l&&n!==e.x&&va(i<c?n:s,i,l,c,i<c?s:n,i,e.x,e.y)){let d=Math.abs(i-e.y)/(n-e.x);ri(e,o)&&(d<u||d===u&&(e.x>r.x||e.x===r.x&&cc(r,e)))&&(r=e,u=d)}e=e.next}while(e!==a);return r}function cc(o,t){return vt(o.prev,o,t.prev)<0&&vt(t.next,o,o.next)<0}function uc(o,t,e,n){let i=o;do i.z===0&&(i.z=Sr(i.x,i.y,t,e,n)),i.prevZ=i.prev,i.nextZ=i.next,i=i.next;while(i!==o);i.prevZ.nextZ=null,i.prevZ=null,hc(i)}function hc(o){let t,e=1;do{let n=o,i;o=null;let s=null;for(t=0;n;){t++;let r=n,a=0;for(let c=0;c<e&&(a++,r=r.nextZ,!!r);c++);let l=e;for(;a>0||l>0&&r;)a!==0&&(l===0||!r||n.z<=r.z)?(i=n,n=n.nextZ,a--):(i=r,r=r.nextZ,l--),s?s.nextZ=i:o=i,i.prevZ=s,s=i;n=r}s.nextZ=null,e*=2}while(t>1);return o}function Sr(o,t,e,n,i){return o=(o-e)*i|0,t=(t-n)*i|0,o=(o|o<<8)&16711935,o=(o|o<<4)&252645135,o=(o|o<<2)&858993459,o=(o|o<<1)&1431655765,t=(t|t<<8)&16711935,t=(t|t<<4)&252645135,t=(t|t<<2)&858993459,t=(t|t<<1)&1431655765,o|t<<1}function dc(o){let t=o,e=o;do(t.x<e.x||t.x===e.x&&t.y<e.y)&&(e=t),t=t.next;while(t!==o);return e}function va(o,t,e,n,i,s,r,a){return(i-r)*(t-a)>=(o-r)*(s-a)&&(o-r)*(n-a)>=(e-r)*(t-a)&&(e-r)*(s-a)>=(i-r)*(n-a)}function Wn(o,t,e,n,i,s,r,a){return!(o===r&&t===a)&&va(o,t,e,n,i,s,r,a)}function fc(o,t){return o.next.i!==t.i&&o.prev.i!==t.i&&!pc(o,t)&&(ri(o,t)&&ri(t,o)&&mc(o,t)&&(vt(o.prev,o,t.prev)||vt(o,t.prev,t))||Pn(o,t)&&vt(o.prev,o,o.next)>0&&vt(t.prev,t,t.next)>0)}function vt(o,t,e){return(t.y-o.y)*(e.x-t.x)-(t.x-o.x)*(e.y-t.y)}function Pn(o,t){return o.x===t.x&&o.y===t.y}function Ma(o,t,e,n){let i=Oi(vt(o,t,e)),s=Oi(vt(o,t,n)),r=Oi(vt(e,n,o)),a=Oi(vt(e,n,t));return!!(i!==s&&r!==a||i===0&&Bi(o,e,t)||s===0&&Bi(o,n,t)||r===0&&Bi(e,o,n)||a===0&&Bi(e,t,n))}function Bi(o,t,e){return t.x<=Math.max(o.x,e.x)&&t.x>=Math.min(o.x,e.x)&&t.y<=Math.max(o.y,e.y)&&t.y>=Math.min(o.y,e.y)}function Oi(o){return o>0?1:o<0?-1:0}function pc(o,t){let e=o;do{if(e.i!==o.i&&e.next.i!==o.i&&e.i!==t.i&&e.next.i!==t.i&&Ma(e,e.next,o,t))return!0;e=e.next}while(e!==o);return!1}function ri(o,t){return vt(o.prev,o,o.next)<0?vt(o,t,o.next)>=0&&vt(o,o.prev,t)>=0:vt(o,t,o.prev)<0||vt(o,o.next,t)<0}function mc(o,t){let e=o,n=!1,i=(o.x+t.x)/2,s=(o.y+t.y)/2;do e.y>s!=e.next.y>s&&e.next.y!==e.y&&i<(e.next.x-e.x)*(s-e.y)/(e.next.y-e.y)+e.x&&(n=!n),e=e.next;while(e!==o);return n}function Sa(o,t){let e=br(o.i,o.x,o.y),n=br(t.i,t.x,t.y),i=o.next,s=t.prev;return o.next=t,t.prev=o,e.next=i,i.prev=e,n.next=e,e.prev=n,s.next=n,n.prev=s,n}function Vo(o,t,e,n){let i=br(o,t,e);return n?(i.next=n.next,i.prev=n,n.next.prev=i,n.next=i):(i.prev=i,i.next=i),i}function oi(o){o.next.prev=o.prev,o.prev.next=o.next,o.prevZ&&(o.prevZ.nextZ=o.nextZ),o.nextZ&&(o.nextZ.prevZ=o.prevZ)}function br(o,t,e){return{i:o,x:t,y:e,prev:null,next:null,z:0,prevZ:null,nextZ:null,steiner:!1}}function gc(o,t,e,n){let i=0;for(let s=t,r=e-n;s<e;s+=n)i+=(o[r]-o[s])*(o[s+1]+o[r+1]),r=s;return i}var Er=class{static triangulate(t,e,n=2){return tc(t,e,n)}},qe=class o{static area(t){let e=t.length,n=0;for(let i=e-1,s=0;s<e;i=s++)n+=t[i].x*t[s].y-t[s].x*t[i].y;return n*.5}static isClockWise(t){return o.area(t)<0}static triangulateShape(t,e){let n=[],i=[],s=[];Go(t),Wo(n,t);let r=t.length;e.forEach(Go);for(let l=0;l<e.length;l++)i.push(r),r+=e[l].length,Wo(n,e[l]);let a=Er.triangulate(n,i);for(let l=0;l<a.length;l+=3)s.push(a.slice(l,l+3));return s}};function Go(o){let t=o.length;t>2&&o[t-1].equals(o[0])&&o.pop()}function Wo(o,t){for(let e=0;e<t.length;e++)o.push(t[e].x),o.push(t[e].y)}var De=class o extends Pt{constructor(t=new ye([new O(.5,.5),new O(-.5,.5),new O(-.5,-.5),new O(.5,-.5)]),e={}){super(),this.type="ExtrudeGeometry",this.parameters={shapes:t,options:e},t=Array.isArray(t)?t:[t];let n=this,i=[],s=[];for(let a=0,l=t.length;a<l;a++){let c=t[a];r(c)}this.setAttribute("position",new ct(i,3)),this.setAttribute("uv",new ct(s,2)),this.computeVertexNormals();function r(a){let l=[],c=e.curveSegments!==void 0?e.curveSegments:12,u=e.steps!==void 0?e.steps:1,d=e.depth!==void 0?e.depth:1,h=e.bevelEnabled!==void 0?e.bevelEnabled:!0,f=e.bevelThickness!==void 0?e.bevelThickness:.2,p=e.bevelSize!==void 0?e.bevelSize:f-.1,m=e.bevelOffset!==void 0?e.bevelOffset:0,x=e.bevelSegments!==void 0?e.bevelSegments:3,v=e.extrudePath,S=e.UVGenerator!==void 0?e.UVGenerator:xc,y,M=!1,A,b,R,T;if(v){y=v.getSpacedPoints(u),M=!0,h=!1;let F=v.isCatmullRomCurve3?v.closed:!1;A=v.computeFrenetFrames(u,F),b=new _,R=new _,T=new _}h||(x=0,f=0,p=0,m=0);let I=a.extractPoints(c),C=I.shape,P=I.holes;if(!qe.isClockWise(C)){C=C.reverse();for(let F=0,G=P.length;F<G;F++){let W=P[F];qe.isClockWise(W)&&(P[F]=W.reverse())}}function w(F){let W=10000000000000001e-36,Z=F[0];for(let Y=1;Y<=F.length;Y++){let ht=Y%F.length,st=F[ht],xt=st.x-Z.x,yt=st.y-Z.y,At=xt*xt+yt*yt,Gt=Math.max(Math.abs(st.x),Math.abs(st.y),Math.abs(Z.x),Math.abs(Z.y)),Ve=W*Gt*Gt;if(At<=Ve){F.splice(ht,1),Y--;continue}Z=st}}w(C),P.forEach(w);let U=P.length,L=C;for(let F=0;F<U;F++){let G=P[F];C=C.concat(G)}function V(F,G,W){return G||gt("ExtrudeGeometry: vec does not exist"),F.clone().addScaledVector(G,W)}let X=C.length;function J(F,G,W){let Z,Y,ht,st=F.x-G.x,xt=F.y-G.y,yt=W.x-F.x,At=W.y-F.y,Gt=st*st+xt*xt,Ve=st*At-xt*yt;if(Math.abs(Ve)>Number.EPSILON){let Wt=Math.sqrt(Gt),go=Math.sqrt(yt*yt+At*At),xo=G.x-xt/Wt,_o=G.y+st/Wt,ll=W.x-At/go,cl=W.y+yt/go,yo=((ll-xo)*At-(cl-_o)*yt)/(st*At-xt*yt);Z=xo+st*yo-F.x,Y=_o+xt*yo-F.y;let vo=Z*Z+Y*Y;if(vo<=2)return new O(Z,Y);ht=Math.sqrt(vo/2)}else{let Wt=!1;st>Number.EPSILON?yt>Number.EPSILON&&(Wt=!0):st<-Number.EPSILON?yt<-Number.EPSILON&&(Wt=!0):Math.sign(xt)===Math.sign(At)&&(Wt=!0),Wt?(Z=-xt,Y=st,ht=Math.sqrt(Gt)):(Z=st,Y=xt,ht=Math.sqrt(Gt/2))}return new O(Z/ht,Y/ht)}let K=[];for(let F=0,G=L.length,W=G-1,Z=F+1;F<G;F++,W++,Z++)W===G&&(W=0),Z===G&&(Z=0),K[F]=J(L[F],L[W],L[Z]);let E=[],N,H=K.concat();for(let F=0,G=U;F<G;F++){let W=P[F];N=[];for(let Z=0,Y=W.length,ht=Y-1,st=Z+1;Z<Y;Z++,ht++,st++)ht===Y&&(ht=0),st===Y&&(st=0),N[Z]=J(W[Z],W[ht],W[st]);E.push(N),H=H.concat(N)}let $;if(x===0)$=qe.triangulateShape(L,P);else{let F=[],G=[];for(let W=0;W<x;W++){let Z=W/x,Y=f*Math.cos(Z*Math.PI/2),ht=p*Math.sin(Z*Math.PI/2)+m;for(let st=0,xt=L.length;st<xt;st++){let yt=V(L[st],K[st],ht);Et(yt.x,yt.y,-Y),Z===0&&F.push(yt)}for(let st=0,xt=U;st<xt;st++){let yt=P[st];N=E[st];let At=[];for(let Gt=0,Ve=yt.length;Gt<Ve;Gt++){let Wt=V(yt[Gt],N[Gt],ht);Et(Wt.x,Wt.y,-Y),Z===0&&At.push(Wt)}Z===0&&G.push(At)}}$=qe.triangulateShape(F,G)}let ut=$.length,_t=p+m;for(let F=0;F<X;F++){let G=h?V(C[F],H[F],_t):C[F];M?(R.copy(A.normals[0]).multiplyScalar(G.x),b.copy(A.binormals[0]).multiplyScalar(G.y),T.copy(y[0]).add(R).add(b),Et(T.x,T.y,T.z)):Et(G.x,G.y,0)}for(let F=1;F<=u;F++)for(let G=0;G<X;G++){let W=h?V(C[G],H[G],_t):C[G];M?(R.copy(A.normals[F]).multiplyScalar(W.x),b.copy(A.binormals[F]).multiplyScalar(W.y),T.copy(y[F]).add(R).add(b),Et(T.x,T.y,T.z)):Et(W.x,W.y,d/u*F)}for(let F=x-1;F>=0;F--){let G=F/x,W=f*Math.cos(G*Math.PI/2),Z=p*Math.sin(G*Math.PI/2)+m;for(let Y=0,ht=L.length;Y<ht;Y++){let st=V(L[Y],K[Y],Z);Et(st.x,st.y,d+W)}for(let Y=0,ht=P.length;Y<ht;Y++){let st=P[Y];N=E[Y];for(let xt=0,yt=st.length;xt<yt;xt++){let At=V(st[xt],N[xt],Z);M?Et(At.x,At.y+y[u-1].y,y[u-1].x+W):Et(At.x,At.y,d+W)}}}Ct(),Mt();function Ct(){let F=i.length/3;if(h){let G=0,W=X*G;for(let Z=0;Z<ut;Z++){let Y=$[Z];Ut(Y[2]+W,Y[1]+W,Y[0]+W)}G=u+x*2,W=X*G;for(let Z=0;Z<ut;Z++){let Y=$[Z];Ut(Y[0]+W,Y[1]+W,Y[2]+W)}}else{for(let G=0;G<ut;G++){let W=$[G];Ut(W[2],W[1],W[0])}for(let G=0;G<ut;G++){let W=$[G];Ut(W[0]+X*u,W[1]+X*u,W[2]+X*u)}}n.addGroup(F,i.length/3-F,0)}function Mt(){let F=i.length/3,G=0;bt(L,G),G+=L.length;for(let W=0,Z=P.length;W<Z;W++){let Y=P[W];bt(Y,G),G+=Y.length}n.addGroup(F,i.length/3-F,1)}function bt(F,G){let W=F.length;for(;--W>=0;){let Z=W,Y=W-1;Y<0&&(Y=F.length-1);for(let ht=0,st=u+x*2;ht<st;ht++){let xt=X*ht,yt=X*(ht+1),At=G+Z+xt,Gt=G+Y+xt,Ve=G+Y+yt,Wt=G+Z+yt;He(At,Gt,Ve,Wt)}}}function Et(F,G,W){l.push(F),l.push(G),l.push(W)}function Ut(F,G,W){Vt(F),Vt(G),Vt(W);let Z=i.length/3,Y=S.generateTopUV(n,i,Z-3,Z-2,Z-1);he(Y[0]),he(Y[1]),he(Y[2])}function He(F,G,W,Z){Vt(F),Vt(G),Vt(Z),Vt(G),Vt(W),Vt(Z);let Y=i.length/3,ht=S.generateSideWallUV(n,i,Y-6,Y-3,Y-2,Y-1);he(ht[0]),he(ht[1]),he(ht[3]),he(ht[1]),he(ht[2]),he(ht[3])}function Vt(F){i.push(l[F*3+0]),i.push(l[F*3+1]),i.push(l[F*3+2])}function he(F){s.push(F.x),s.push(F.y)}}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}toJSON(){let t=super.toJSON(),e=this.parameters.shapes,n=this.parameters.options;return _c(e,n,t)}static fromJSON(t,e){let n=[];for(let s=0,r=t.shapes.length;s<r;s++){let a=e[t.shapes[s]];n.push(a)}let i=t.options.extrudePath;return i!==void 0&&(t.options.extrudePath=new Mr[i.type]().fromJSON(i)),new o(n,t.options)}},xc={generateTopUV:function(o,t,e,n,i){let s=t[e*3],r=t[e*3+1],a=t[n*3],l=t[n*3+1],c=t[i*3],u=t[i*3+1];return[new O(s,r),new O(a,l),new O(c,u)]},generateSideWallUV:function(o,t,e,n,i,s){let r=t[e*3],a=t[e*3+1],l=t[e*3+2],c=t[n*3],u=t[n*3+1],d=t[n*3+2],h=t[i*3],f=t[i*3+1],p=t[i*3+2],m=t[s*3],x=t[s*3+1],v=t[s*3+2];return Math.abs(a-u)<Math.abs(r-c)?[new O(r,1-l),new O(c,1-d),new O(h,1-p),new O(m,1-v)]:[new O(a,1-l),new O(u,1-d),new O(f,1-p),new O(x,1-v)]}};function _c(o,t,e){if(e.shapes=[],Array.isArray(o))for(let n=0,i=o.length;n<i;n++){let s=o[n];e.shapes.push(s.uuid)}else e.shapes.push(o.uuid);return e.options=Object.assign({},t),t.extrudePath!==void 0&&(e.options.extrudePath=t.extrudePath.toJSON()),e}var Rt=class o extends Pt{constructor(t=1,e=1,n=1,i=1){super(),this.type="PlaneGeometry",this.parameters={width:t,height:e,widthSegments:n,heightSegments:i};let s=t/2,r=e/2,a=Math.floor(n),l=Math.floor(i),c=a+1,u=l+1,d=t/a,h=e/l,f=[],p=[],m=[],x=[];for(let v=0;v<u;v++){let S=v*h-r;for(let y=0;y<c;y++){let M=y*d-s;p.push(M,-S,0),m.push(0,0,1),x.push(y/a),x.push(1-v/l)}}for(let v=0;v<l;v++)for(let S=0;S<a;S++){let y=S+c*v,M=S+c*(v+1),A=S+1+c*(v+1),b=S+1+c*v;f.push(y,M,b),f.push(M,A,b)}this.setIndex(f),this.setAttribute("position",new ct(p,3)),this.setAttribute("normal",new ct(m,3)),this.setAttribute("uv",new ct(x,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new o(t.width,t.height,t.widthSegments,t.heightSegments)}},ai=class o extends Pt{constructor(t=.5,e=1,n=32,i=1,s=0,r=Math.PI*2){super(),this.type="RingGeometry",this.parameters={innerRadius:t,outerRadius:e,thetaSegments:n,phiSegments:i,thetaStart:s,thetaLength:r},n=Math.max(3,n),i=Math.max(1,i);let a=[],l=[],c=[],u=[],d=t,h=(e-t)/i,f=new _,p=new O;for(let m=0;m<=i;m++){for(let x=0;x<=n;x++){let v=s+x/n*r;f.x=d*Math.cos(v),f.y=d*Math.sin(v),l.push(f.x,f.y,f.z),c.push(0,0,1),p.x=(f.x/e+1)/2,p.y=(f.y/e+1)/2,u.push(p.x,p.y)}d+=h}for(let m=0;m<i;m++){let x=m*(n+1);for(let v=0;v<n;v++){let S=v+x,y=S,M=S+n+1,A=S+n+2,b=S+1;a.push(y,M,b),a.push(M,A,b)}}this.setIndex(a),this.setAttribute("position",new ct(l,3)),this.setAttribute("normal",new ct(c,3)),this.setAttribute("uv",new ct(u,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new o(t.innerRadius,t.outerRadius,t.thetaSegments,t.phiSegments,t.thetaStart,t.thetaLength)}};var Ln=class o extends Pt{constructor(t=1,e=32,n=16,i=0,s=Math.PI*2,r=0,a=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:t,widthSegments:e,heightSegments:n,phiStart:i,phiLength:s,thetaStart:r,thetaLength:a},e=Math.max(3,Math.floor(e)),n=Math.max(2,Math.floor(n));let l=Math.min(r+a,Math.PI),c=0,u=[],d=new _,h=new _,f=[],p=[],m=[],x=[];for(let v=0;v<=n;v++){let S=[],y=v/n,M=r+y*a,A=t*Math.cos(M),b=Math.sqrt(t*t-A*A),R=0;v===0&&r===0?R=.5/e:v===n&&l===Math.PI&&(R=-.5/e);for(let T=0;T<=e;T++){let I=T/e,C=i+I*s;d.x=-b*Math.cos(C),d.y=A,d.z=b*Math.sin(C),p.push(d.x,d.y,d.z),h.copy(d).normalize(),m.push(h.x,h.y,h.z),x.push(I+R,1-y),S.push(c++)}u.push(S)}for(let v=0;v<n;v++)for(let S=0;S<e;S++){let y=u[v][S+1],M=u[v][S],A=u[v+1][S],b=u[v+1][S+1];(v!==0||r>0)&&f.push(y,M,b),(v!==n-1||l<Math.PI)&&f.push(M,A,b)}this.setIndex(f),this.setAttribute("position",new ct(p,3)),this.setAttribute("normal",new ct(m,3)),this.setAttribute("uv",new ct(x,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new o(t.radius,t.widthSegments,t.heightSegments,t.phiStart,t.phiLength,t.thetaStart,t.thetaLength)}};var Ne=class o extends Pt{constructor(t=1,e=.4,n=12,i=48,s=Math.PI*2,r=0,a=Math.PI*2){super(),this.type="TorusGeometry",this.parameters={radius:t,tube:e,radialSegments:n,tubularSegments:i,arc:s,thetaStart:r,thetaLength:a},n=Math.floor(n),i=Math.floor(i);let l=[],c=[],u=[],d=[],h=new _,f=new _,p=new _;for(let m=0;m<=n;m++){let x=r+m/n*a;for(let v=0;v<=i;v++){let S=v/i*s;f.x=(t+e*Math.cos(x))*Math.cos(S),f.y=(t+e*Math.cos(x))*Math.sin(S),f.z=e*Math.sin(x),c.push(f.x,f.y,f.z),h.x=t*Math.cos(S),h.y=t*Math.sin(S),p.subVectors(f,h).normalize(),u.push(p.x,p.y,p.z),d.push(v/i),d.push(m/n)}}for(let m=1;m<=n;m++)for(let x=1;x<=i;x++){let v=(i+1)*m+x-1,S=(i+1)*(m-1)+x-1,y=(i+1)*(m-1)+x,M=(i+1)*m+x;l.push(v,S,M),l.push(S,y,M)}this.setIndex(l),this.setAttribute("position",new ct(c,3)),this.setAttribute("normal",new ct(u,3)),this.setAttribute("uv",new ct(d,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new o(t.radius,t.tube,t.radialSegments,t.tubularSegments,t.arc,t.thetaStart,t.thetaLength)}};function ba(o){let t={};for(let e in o){t[e]={};for(let n in o[e]){let i=o[e][n];if(Xo(i))i.isRenderTargetTexture?(St("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),t[e][n]=null):t[e][n]=i.clone();else if(Array.isArray(i))if(Xo(i[0])){let s=[];for(let r=0,a=i.length;r<a;r++)s[r]=i[r].clone();t[e][n]=s}else t[e][n]=i.slice();else t[e][n]=i}}return t}function Ot(o){let t={};for(let e=0;e<o.length;e++){let n=ba(o[e]);for(let i in n)t[i]=n[i]}return t}function Xo(o){return o&&(o.isColor||o.isMatrix3||o.isMatrix4||o.isVector2||o.isVector3||o.isVector4||o.isTexture||o.isQuaternion)}var j=class extends Qn{constructor(t){super(),this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new ft(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new ft(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=pa,this.normalScale=new O(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Ze,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(t)}copy(t){return super.copy(t),this.defines={STANDARD:""},this.color.copy(t.color),this.roughness=t.roughness,this.metalness=t.metalness,this.map=t.map,this.lightMap=t.lightMap,this.lightMapIntensity=t.lightMapIntensity,this.aoMap=t.aoMap,this.aoMapIntensity=t.aoMapIntensity,this.emissive.copy(t.emissive),this.emissiveMap=t.emissiveMap,this.emissiveIntensity=t.emissiveIntensity,this.bumpMap=t.bumpMap,this.bumpScale=t.bumpScale,this.normalMap=t.normalMap,this.normalMapType=t.normalMapType,this.normalScale.copy(t.normalScale),this.displacementMap=t.displacementMap,this.displacementScale=t.displacementScale,this.displacementBias=t.displacementBias,this.roughnessMap=t.roughnessMap,this.metalnessMap=t.metalnessMap,this.alphaMap=t.alphaMap,this.envMap=t.envMap,this.envMapRotation.copy(t.envMapRotation),this.envMapIntensity=t.envMapIntensity,this.wireframe=t.wireframe,this.wireframeLinewidth=t.wireframeLinewidth,this.wireframeLinecap=t.wireframeLinecap,this.wireframeLinejoin=t.wireframeLinejoin,this.flatShading=t.flatShading,this.fog=t.fog,this}},zt=class extends j{constructor(t){super(),this.isMeshPhysicalMaterial=!0,this.defines={STANDARD:"",PHYSICAL:""},this.type="MeshPhysicalMaterial",this.anisotropyRotation=0,this.anisotropyMap=null,this.clearcoatMap=null,this.clearcoatRoughness=0,this.clearcoatRoughnessMap=null,this.clearcoatNormalScale=new O(1,1),this.clearcoatNormalMap=null,this.ior=1.5,Object.defineProperty(this,"reflectivity",{get:function(){return Q(2.5*(this.ior-1)/(this.ior+1),0,1)},set:function(e){this.ior=(1+.4*e)/(1-.4*e)}}),this.iridescenceMap=null,this.iridescenceIOR=1.3,this.iridescenceThicknessRange=[100,400],this.iridescenceThicknessMap=null,this.sheenColor=new ft(0),this.sheenColorMap=null,this.sheenRoughness=1,this.sheenRoughnessMap=null,this.transmissionMap=null,this.thickness=0,this.thicknessMap=null,this.attenuationDistance=1/0,this.attenuationColor=new ft(1,1,1),this.specularIntensity=1,this.specularIntensityMap=null,this.specularColor=new ft(1,1,1),this.specularColorMap=null,this._anisotropy=0,this._clearcoat=0,this._dispersion=0,this._iridescence=0,this._retroreflectivity=0,this._sheen=0,this._transmission=0,this.setValues(t)}get anisotropy(){return this._anisotropy}set anisotropy(t){this._anisotropy>0!=t>0&&this.version++,this._anisotropy=t}get clearcoat(){return this._clearcoat}set clearcoat(t){this._clearcoat>0!=t>0&&this.version++,this._clearcoat=t}get iridescence(){return this._iridescence}set iridescence(t){this._iridescence>0!=t>0&&this.version++,this._iridescence=t}get dispersion(){return this._dispersion}set dispersion(t){this._dispersion>0!=t>0&&this.version++,this._dispersion=t}get retroreflectivity(){return this._retroreflectivity}set retroreflectivity(t){this._retroreflectivity>0!=t>0&&this.version++,this._retroreflectivity=t}get sheen(){return this._sheen}set sheen(t){this._sheen>0!=t>0&&this.version++,this._sheen=t}get transmission(){return this._transmission}set transmission(t){this._transmission>0!=t>0&&this.version++,this._transmission=t}copy(t){return super.copy(t),this.defines={STANDARD:"",PHYSICAL:""},this.anisotropy=t.anisotropy,this.anisotropyRotation=t.anisotropyRotation,this.anisotropyMap=t.anisotropyMap,this.clearcoat=t.clearcoat,this.clearcoatMap=t.clearcoatMap,this.clearcoatRoughness=t.clearcoatRoughness,this.clearcoatRoughnessMap=t.clearcoatRoughnessMap,this.clearcoatNormalMap=t.clearcoatNormalMap,this.clearcoatNormalScale.copy(t.clearcoatNormalScale),this.dispersion=t.dispersion,this.ior=t.ior,this.iridescence=t.iridescence,this.iridescenceMap=t.iridescenceMap,this.iridescenceIOR=t.iridescenceIOR,this.iridescenceThicknessRange=[...t.iridescenceThicknessRange],this.iridescenceThicknessMap=t.iridescenceThicknessMap,this.retroreflectivity=t.retroreflectivity,this.sheen=t.sheen,this.sheenColor.copy(t.sheenColor),this.sheenColorMap=t.sheenColorMap,this.sheenRoughness=t.sheenRoughness,this.sheenRoughnessMap=t.sheenRoughnessMap,this.transmission=t.transmission,this.transmissionMap=t.transmissionMap,this.thickness=t.thickness,this.thicknessMap=t.thicknessMap,this.attenuationDistance=t.attenuationDistance,this.attenuationColor.copy(t.attenuationColor),this.specularIntensity=t.specularIntensity,this.specularIntensityMap=t.specularIntensityMap,this.specularColor.copy(t.specularColor),this.specularColorMap=t.specularColorMap,this}};function yn(o,t){return!o||o.constructor===t?o:typeof t.BYTES_PER_ELEMENT=="number"?new t(o):Array.prototype.slice.call(o)}function nr(o){return o!==void 0&&o.inTangents!==void 0&&o.outTangents!==void 0}var Ue=class{constructor(t,e,n,i){this.parameterPositions=t,this._cachedIndex=0,this.resultBuffer=i!==void 0?i:new e.constructor(n),this.sampleValues=e,this.valueSize=n,this.settings=null,this.DefaultSettings_={}}evaluate(t){let e=this.parameterPositions,n=this._cachedIndex,i=e[n],s=e[n-1];n:{t:{let r;e:{i:if(!(t<i)){for(let a=n+2;;){if(i===void 0){if(t<s)break i;return n=e.length,this._cachedIndex=n,this.copySampleValue_(n-1)}if(n===a)break;if(s=i,i=e[++n],t<i)break t}r=e.length;break e}if(!(t>=s)){let a=e[1];t<a&&(n=2,s=a);for(let l=n-2;;){if(s===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(n===l)break;if(i=s,s=e[--n-1],t>=s)break t}r=n,n=0;break e}break n}for(;n<r;){let a=n+r>>>1;t<e[a]?r=a:n=a+1}if(i=e[n],s=e[n-1],s===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(i===void 0)return n=e.length,this._cachedIndex=n,this.copySampleValue_(n-1)}this._cachedIndex=n,this.intervalChanged_(n,s,i)}return this.interpolate_(n,s,t,i)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(t){let e=this.resultBuffer,n=this.sampleValues,i=this.valueSize,s=t*i;for(let r=0;r!==i;++r)e[r]=n[s+r];return e}interpolate_(){throw new Error("THREE.Interpolant: Call to abstract method.")}intervalChanged_(){}},ss=class extends Ue{constructor(t,e,n,i){super(t,e,n,i),this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:mr,endingEnd:mr}}intervalChanged_(t,e,n){let i=this.parameterPositions,s=t-2,r=t+1,a=i[s],l=i[r];if(a===void 0)switch(this.getSettings_().endingStart){case gr:s=t,a=2*e-n;break;case xr:s=i.length-2,a=e+i[s]-i[s+1];break;default:s=t,a=n}if(l===void 0)switch(this.getSettings_().endingEnd){case gr:r=t,l=2*n-e;break;case xr:r=1,l=n+i[1]-i[0];break;default:r=t-1,l=e}let c=(n-e)*.5,u=this.valueSize;this._weightPrev=c/(e-a),this._weightNext=c/(l-n),this._offsetPrev=s*u,this._offsetNext=r*u}interpolate_(t,e,n,i){let s=this.resultBuffer,r=this.sampleValues,a=this.valueSize,l=t*a,c=l-a,u=this._offsetPrev,d=this._offsetNext,h=this._weightPrev,f=this._weightNext,p=(n-e)/(i-e),m=p*p,x=m*p,v=-h*x+2*h*m-h*p,S=(1+h)*x+(-1.5-2*h)*m+(-.5+h)*p+1,y=(-1-f)*x+(1.5+f)*m+.5*p,M=f*x-f*m;for(let A=0;A!==a;++A)s[A]=v*r[u+A]+S*r[c+A]+y*r[l+A]+M*r[d+A];return s}},rs=class extends Ue{constructor(t,e,n,i){super(t,e,n,i)}interpolate_(t,e,n,i){let s=this.resultBuffer,r=this.sampleValues,a=this.valueSize,l=t*a,c=l-a,u=(n-e)/(i-e),d=1-u;for(let h=0;h!==a;++h)s[h]=r[c+h]*d+r[l+h]*u;return s}},os=class extends Ue{constructor(t,e,n,i){super(t,e,n,i)}interpolate_(t){return this.copySampleValue_(t-1)}},as=class extends Ue{interpolate_(t,e,n,i){let s=this.resultBuffer,r=this.sampleValues,a=this.valueSize,l=t*a,c=l-a,u=this.inTangents,d=this.outTangents;if(!u||!d){let p=(n-e)/(i-e),m=1-p;for(let x=0;x!==a;++x)s[x]=r[c+x]*m+r[l+x]*p;return s}let h=a*2,f=t-1;for(let p=0;p!==a;++p){let m=r[c+p],x=r[l+p],v=f*h+p*2,S=d[v],y=d[v+1],M=t*h+p*2,A=u[M],b=u[M+1],R=vc(n,e,S,A,i);s[p]=Ea(R,m,y,b,x)}return s}};function Ea(o,t,e,n,i){let s=1-o;return s*s*s*t+3*s*s*o*e+3*s*o*o*n+o*o*o*i}function yc(o,t,e,n,i){let s=1-o;return 3*s*s*(e-t)+6*s*o*(n-e)+3*o*o*(i-n)}function vc(o,t,e,n,i){let s=(o-t)/(i-t);for(let r=0;r<8;r++){let a=Ea(s,t,e,n,i)-o;if(Math.abs(a)<1e-10)break;let l=yc(s,t,e,n,i);if(Math.abs(l)<1e-10)break;s=Math.max(0,Math.min(1,s-a/l))}return s}var Jt=class{constructor(t,e,n,i){if(t===void 0)throw new Error("THREE.KeyframeTrack: track name is undefined");if(e===void 0||e.length===0)throw new Error("THREE.KeyframeTrack: no keyframes in track named "+t);this.name=t,this.times=yn(e,this.TimeBufferType),this.values=yn(n,this.ValueBufferType),this.setInterpolation(i||this.DefaultInterpolation)}static toJSON(t){let e=t.constructor,n;if(e.toJSON!==this.toJSON)n=e.toJSON(t);else{n={name:t.name,times:yn(t.times,Array),values:yn(t.values,Array)};let i=t.getInterpolation();i!==t.DefaultInterpolation&&(n.interpolation=i),nr(t.settings)&&(n.settings={inTangents:yn(t.settings.inTangents,Array),outTangents:yn(t.settings.outTangents,Array)})}return n.type=t.ValueTypeName,n}InterpolantFactoryMethodDiscrete(t){return new os(this.times,this.values,this.getValueSize(),t)}InterpolantFactoryMethodLinear(t){return new rs(this.times,this.values,this.getValueSize(),t)}InterpolantFactoryMethodSmooth(t){return new ss(this.times,this.values,this.getValueSize(),t)}InterpolantFactoryMethodBezier(t){let e=new as(this.times,this.values,this.getValueSize(),t);return this.settings&&(e.inTangents=this.settings.inTangents,e.outTangents=this.settings.outTangents),e}setInterpolation(t){let e;switch(t){case Zn:e=this.InterpolantFactoryMethodDiscrete;break;case $i:e=this.InterpolantFactoryMethodLinear;break;case Vi:e=this.InterpolantFactoryMethodSmooth;break;case pr:e=this.InterpolantFactoryMethodBezier;break}if(e===void 0){let n="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(t!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw new Error(n);return St("KeyframeTrack:",n),this}return this.createInterpolant=e,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return Zn;case this.InterpolantFactoryMethodLinear:return $i;case this.InterpolantFactoryMethodSmooth:return Vi;case this.InterpolantFactoryMethodBezier:return pr}}getValueSize(){return this.values.length/this.times.length}shift(t){if(t!==0){let e=this.times;for(let n=0,i=e.length;n!==i;++n)e[n]+=t}return this}scale(t){if(t!==1){let e=this.times;for(let n=0,i=e.length;n!==i;++n)e[n]*=t;nr(this.settings)&&($o(this.settings.inTangents,t),$o(this.settings.outTangents,t))}return this}trim(t,e){let n=this.times,i=n.length,s=0,r=i-1;for(;s!==i&&n[s]<t;)++s;for(;r!==-1&&n[r]>e;)--r;if(++r,s!==0||r!==i){s>=r&&(r=Math.max(r,1),s=r-1);let a=this.getValueSize();this.times=n.slice(s,r),this.values=this.values.slice(s*a,r*a)}return this}validate(){let t=!0,e=this.getValueSize();e-Math.floor(e)!==0&&(gt("KeyframeTrack: Invalid value size in track.",this),t=!1);let n=this.times,i=this.values,s=n.length;s===0&&(gt("KeyframeTrack: Track is empty.",this),t=!1);let r=null;for(let a=0;a!==s;a++){let l=n[a];if(typeof l=="number"&&isNaN(l)){gt("KeyframeTrack: Time is not a valid number.",this,a,l),t=!1;break}if(r!==null&&r>l){gt("KeyframeTrack: Out of order keys.",this,a,l,r),t=!1;break}r=l}if(i!==void 0&&hl(i))for(let a=0,l=i.length;a!==l;++a){let c=i[a];if(isNaN(c)){gt("KeyframeTrack: Value is not a valid number.",this,a,c),t=!1;break}}return t}optimize(){let t=this.times.slice(),e=this.values.slice(),n=this.getValueSize(),i=this.getInterpolation()===Vi,s=t.length-1,r=1;for(let a=1;a<s;++a){let l=!1,c=t[a],u=t[a+1];if(c!==u&&(a!==1||c!==t[0]))if(i)l=!0;else{let d=a*n,h=d-n,f=d+n;for(let p=0;p!==n;++p){let m=e[d+p];if(m!==e[h+p]||m!==e[f+p]){l=!0;break}}}if(l){if(a!==r){t[r]=t[a];let d=a*n,h=r*n;for(let f=0;f!==n;++f)e[h+f]=e[d+f]}++r}}if(s>0){t[r]=t[s];for(let a=s*n,l=r*n,c=0;c!==n;++c)e[l+c]=e[a+c];++r}return r!==t.length?(this.times=t.slice(0,r),this.values=e.slice(0,r*n)):(this.times=t,this.values=e),this}clone(){let t=this.times.slice(),e=this.values.slice(),n=this.constructor,i=new n(this.name,t,e);return i.createInterpolant=this.createInterpolant,nr(this.settings)&&(i.settings={inTangents:this.settings.inTangents.slice(),outTangents:this.settings.outTangents.slice()}),i}};function $o(o,t){for(let e=0,n=o.length;e!==n;e+=2)o[e]*=t}Jt.prototype.ValueTypeName="";Jt.prototype.TimeBufferType=Float32Array;Jt.prototype.ValueBufferType=Float32Array;Jt.prototype.DefaultInterpolation=$i;var Fe=class extends Jt{constructor(t,e,n){super(t,e,n)}};Fe.prototype.ValueTypeName="bool";Fe.prototype.ValueBufferType=Array;Fe.prototype.DefaultInterpolation=Zn;Fe.prototype.InterpolantFactoryMethodLinear=void 0;Fe.prototype.InterpolantFactoryMethodSmooth=void 0;var ls=class extends Jt{constructor(t,e,n,i){super(t,e,n,i)}};ls.prototype.ValueTypeName="color";var cs=class extends Jt{constructor(t,e,n,i){super(t,e,n,i)}};cs.prototype.ValueTypeName="number";var us=class extends Ue{constructor(t,e,n,i){super(t,e,n,i)}interpolate_(t,e,n,i){let s=this.resultBuffer,r=this.sampleValues,a=this.valueSize,l=(n-e)/(i-e),c=t*a;for(let u=c+a;c!==u;c+=4)kt.slerpFlat(s,0,r,c-a,r,c,l);return s}},li=class extends Jt{constructor(t,e,n,i){super(t,e,n,i)}InterpolantFactoryMethodLinear(t){return new us(this.times,this.values,this.getValueSize(),t)}};li.prototype.ValueTypeName="quaternion";li.prototype.InterpolantFactoryMethodSmooth=void 0;var Be=class extends Jt{constructor(t,e,n){super(t,e,n)}};Be.prototype.ValueTypeName="string";Be.prototype.ValueBufferType=Array;Be.prototype.DefaultInterpolation=Zn;Be.prototype.InterpolantFactoryMethodLinear=void 0;Be.prototype.InterpolantFactoryMethodSmooth=void 0;var hs=class extends Jt{constructor(t,e,n,i){super(t,e,n,i)}};hs.prototype.ValueTypeName="vector";var ds=class{constructor(t,e,n){let i=this,s=!1,r=0,a=0,l,c=[];this.onStart=void 0,this.onLoad=t,this.onProgress=e,this.onError=n,this._abortController=null,this.itemStart=function(u){a++,s===!1&&i.onStart!==void 0&&i.onStart(u,r,a),s=!0},this.itemEnd=function(u){r++,i.onProgress!==void 0&&i.onProgress(u,r,a),r===a&&(s=!1,i.onLoad!==void 0&&i.onLoad())},this.itemError=function(u){i.onError!==void 0&&i.onError(u)},this.resolveURL=function(u){return u=u.normalize("NFC"),l?l(u):u},this.setURLModifier=function(u){return l=u,this},this.addHandler=function(u,d){return c.push(u,d),this},this.removeHandler=function(u){let d=c.indexOf(u);return d!==-1&&c.splice(d,2),this},this.getHandler=function(u){for(let d=0,h=c.length;d<h;d+=2){let f=c[d],p=c[d+1];if(f.global&&(f.lastIndex=0),f.test(u))return p}return null},this.abort=function(){return this.abortController.abort(),this._abortController=null,this}}get abortController(){return this._abortController||(this._abortController=new AbortController),this._abortController}},wa=new ds,fs=class{constructor(t){this.manager=t!==void 0?t:wa,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}load(){}loadAsync(t,e){let n=this;return new Promise(function(i,s){n.load(t,i,e,s)})}parse(){}setCrossOrigin(t){return this.crossOrigin=t,this}setWithCredentials(t){return this.withCredentials=t,this}setPath(t){return this.path=t,this}setResourcePath(t){return this.resourcePath=t,this}setRequestHeader(t){return this.requestHeader=t,this}abort(){return this}};fs.DEFAULT_MATERIAL_NAME="__DEFAULT";var ps=class extends Yt{constructor(t,e=1){super(),this.isLight=!0,this.type="Light",this.color=new ft(t),this.intensity=e}copy(t,e){return super.copy(t,e),this.color.copy(t.color),this.intensity=t.intensity,this}toJSON(t){let e=super.toJSON(t);return e.object.color=this.color.getHex(),e.object.intensity=this.intensity,e}};var ir=new lt,qo=new _,Yo=new _,ms=class{constructor(t){this.camera=t,this.intensity=1,this.bias=0,this.biasNode=null,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new O(512,512),this.mapType=zr,this.map=null,this.mapPass=null,this.matrix=new lt,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new ji,this._frameExtents=new O(1,1),this._viewportCount=1,this._viewports=[new Ye(0,0,1,1)]}getViewportCount(){return this._viewportCount}getCamera(){return this.camera}getFrustum(){return this._frustum}updateMatrices(t){let e=this.camera;qo.setFromMatrixPosition(t.matrixWorld),e.position.copy(qo),Yo.setFromMatrixPosition(t.target.matrixWorld),e.lookAt(Yo),e.updateMatrixWorld(),this._updateMatrix(e,this.matrix,this._frustum)}_updateMatrix(t,e,n,i){ir.multiplyMatrices(t.projectionMatrix,t.matrixWorldInverse),n.setFromProjectionMatrix(ir,t.coordinateSystem,t.reversedDepth);let s=this._frameExtents,r=i?i.z/s.x:1,a=i?i.w/s.y:1,l=i?i.x/s.x:0,c=i?i.y/s.y:0;t.coordinateSystem===Jn||t.reversedDepth?e.set(.5*r,0,0,.5*r+l,0,.5*a,0,.5*a+c,0,0,1,0,0,0,0,1):e.set(.5*r,0,0,.5*r+l,0,.5*a,0,.5*a+c,0,0,.5,.5,0,0,0,1),e.multiply(ir)}getViewport(t){return this._viewports[t]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(t){return this.camera=t.camera.clone(),this.intensity=t.intensity,this.bias=t.bias,this.radius=t.radius,this.autoUpdate=t.autoUpdate,this.needsUpdate=t.needsUpdate,this.normalBias=t.normalBias,this.blurSamples=t.blurSamples,this.mapSize.copy(t.mapSize),this.biasNode=t.biasNode,this}clone(){return new this.constructor().copy(this)}toJSON(){let t={};return t.intensity=this.intensity,t.bias=this.bias,t.normalBias=this.normalBias,t.radius=this.radius,t.blurSamples=this.blurSamples,t.mapSize=this.mapSize.toArray(),t.camera=this.camera.toJSON(!1).object,delete t.camera.matrix,t}},ki=new _,zi=new kt,le=new _,gs=class extends Yt{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new lt,this.projectionMatrix=new lt,this.projectionMatrixInverse=new lt,this.coordinateSystem=Re,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(t,e){return super.copy(t,e),this.matrixWorldInverse.copy(t.matrixWorldInverse),this.projectionMatrix.copy(t.projectionMatrix),this.projectionMatrixInverse.copy(t.projectionMatrixInverse),this.coordinateSystem=t.coordinateSystem,this}getWorldDirection(t){return super.getWorldDirection(t).negate()}updateMatrixWorld(t){super.updateMatrixWorld(t),this.matrixWorld.decompose(ki,zi,le),le.x===1&&le.y===1&&le.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(ki,zi,le.set(1,1,1)).invert()}updateWorldMatrix(t,e,n=!1){super.updateWorldMatrix(t,e,n),this.matrixWorld.decompose(ki,zi,le),le.x===1&&le.y===1&&le.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(ki,zi,le.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}},Te=new _,Zo=new O,Jo=new O,xs=class extends gs{constructor(t=50,e=1,n=.1,i=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=t,this.zoom=1,this.near=n,this.far=i,this.focus=10,this.aspect=e,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(t,e){return super.copy(t,e),this.fov=t.fov,this.zoom=t.zoom,this.near=t.near,this.far=t.far,this.focus=t.focus,this.aspect=t.aspect,this.view=t.view===null?null:Object.assign({},t.view),this.filmGauge=t.filmGauge,this.filmOffset=t.filmOffset,this}setFocalLength(t){let e=.5*this.getFilmHeight()/t;this.fov=wn*2*Math.atan(e),this.updateProjectionMatrix()}getFocalLength(){let t=Math.tan(Xn*.5*this.fov);return .5*this.getFilmHeight()/t}getEffectiveFOV(){return wn*2*Math.atan(Math.tan(Xn*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(t,e,n){Te.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),e.set(Te.x,Te.y).multiplyScalar(-t/Te.z),Te.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(Te.x,Te.y).multiplyScalar(-t/Te.z)}getViewSize(t,e){return this.getViewBounds(t,Zo,Jo),e.subVectors(Jo,Zo)}setViewOffset(t,e,n,i,s,r){this.aspect=t/e,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=t,this.view.fullHeight=e,this.view.offsetX=n,this.view.offsetY=i,this.view.width=s,this.view.height=r,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let t=this.near,e=t*Math.tan(Xn*.5*this.fov)/this.zoom,n=2*e,i=this.aspect*n,s=-.5*i,r=this.view;if(this.view!==null&&this.view.enabled){let l=r.fullWidth,c=r.fullHeight;s+=r.offsetX*i/l,e-=r.offsetY*n/c,i*=r.width/l,n*=r.height/c}let a=this.filmOffset;a!==0&&(s+=t*a/this.getFilmWidth()),this.projectionMatrix.makePerspective(s,s+i,e,e-n,t,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(t){let e=super.toJSON(t);return e.object.fov=this.fov,e.object.zoom=this.zoom,e.object.near=this.near,e.object.far=this.far,e.object.focus=this.focus,e.object.aspect=this.aspect,this.view!==null&&(e.object.view=Object.assign({},this.view)),e.object.filmGauge=this.filmGauge,e.object.filmOffset=this.filmOffset,e}},wr=class extends ms{constructor(){super(new xs(50,1,.5,500)),this.isSpotLightShadow=!0,this.focus=1,this.aspect=1}updateMatrices(t){let e=this.camera,n=wn*2*t.angle*this.focus,i=this.mapSize.width/this.mapSize.height*this.aspect,s=t.distance||e.far;(n!==e.fov||i!==e.aspect||s!==e.far)&&(e.fov=n,e.aspect=i,e.far=s,e.updateProjectionMatrix()),super.updateMatrices(t)}copy(t){return super.copy(t),this.focus=t.focus,this.aspect=t.aspect,this}toJSON(){let t=super.toJSON();return t.focus=this.focus,t.aspect=this.aspect,t}},ci=class extends ps{constructor(t,e,n=0,i=Math.PI/3,s=0,r=2){super(t,e),this.isSpotLight=!0,this.type="SpotLight",this.position.copy(Yt.DEFAULT_UP),this.updateMatrix(),this.target=new Yt,this.distance=n,this.angle=i,this.penumbra=s,this.decay=r,this.map=null,this.shadow=new wr}get power(){return this.intensity*Math.PI}set power(t){this.intensity=t/Math.PI}dispose(){super.dispose(),this.shadow.dispose()}copy(t,e){return super.copy(t,e),this.distance=t.distance,this.angle=t.angle,this.penumbra=t.penumbra,this.decay=t.decay,this.target=t.target.clone(),this.map=t.map,this.shadow=t.shadow.clone(),this}toJSON(t){let e=super.toJSON(t);return e.object.distance=this.distance,e.object.angle=this.angle,e.object.decay=this.decay,e.object.penumbra=this.penumbra,e.object.target=this.target.uuid,this.map&&this.map.isTexture&&(e.object.map=this.map.toJSON(t).uuid),e.object.shadow=this.shadow.toJSON(),e}};var $r="\\[\\]\\.:\\/",Mc=new RegExp("["+$r+"]","g"),qr="[^"+$r+"]",Sc="[^"+$r.replace("\\.","")+"]",bc=/((?:WC+[\/:])*)/.source.replace("WC",qr),Ec=/(WCOD+)?/.source.replace("WCOD",Sc),wc=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",qr),Tc=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",qr),Ac=new RegExp("^"+bc+Ec+wc+Tc+"$"),Rc=["material","materials","bones","map"],Tr=class{constructor(t,e,n){let i=n||mt.parseTrackName(e);this._targetGroup=t,this._bindings=t.subscribe_(e,i)}getValue(t,e){this.bind();let n=this._targetGroup.nCachedObjects_,i=this._bindings[n];i!==void 0&&i.getValue(t,e)}setValue(t,e){let n=this._bindings;for(let i=this._targetGroup.nCachedObjects_,s=n.length;i!==s;++i)n[i].setValue(t,e)}bind(){let t=this._bindings;for(let e=this._targetGroup.nCachedObjects_,n=t.length;e!==n;++e)t[e].bind()}unbind(){let t=this._bindings;for(let e=this._targetGroup.nCachedObjects_,n=t.length;e!==n;++e)t[e].unbind()}},mt=class o{constructor(t,e,n){this.path=e,this.parsedPath=n||o.parseTrackName(e),this.node=o.findNode(t,this.parsedPath.nodeName),this.rootNode=t,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(t,e,n){return t&&t.isAnimationObjectGroup?new o.Composite(t,e,n):new o(t,e,n)}static sanitizeNodeName(t){return t.replace(/\s/g,"_").replace(Mc,"")}static parseTrackName(t){let e=Ac.exec(t);if(e===null)throw new Error("THREE.PropertyBinding: Cannot parse trackName: "+t);let n={nodeName:e[2],objectName:e[3],objectIndex:e[4],propertyName:e[5],propertyIndex:e[6]},i=n.nodeName&&n.nodeName.lastIndexOf(".");if(i!==void 0&&i!==-1){let s=n.nodeName.substring(i+1);Rc.indexOf(s)!==-1&&(n.nodeName=n.nodeName.substring(0,i),n.objectName=s)}if(n.propertyName===null||n.propertyName.length===0)throw new Error("THREE.PropertyBinding: can not parse propertyName from trackName: "+t);return n}static findNode(t,e){if(e===void 0||e===""||e==="."||e===-1||e===t.name||e===t.uuid)return t;if(t.skeleton){let n=t.skeleton.getBoneByName(e);if(n!==void 0)return n}if(t.children){let n=function(s){for(let r=0;r<s.length;r++){let a=s[r];if(a.name===e||a.uuid===e)return a;let l=n(a.children);if(l)return l}return null},i=n(t.children);if(i)return i}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(t,e){t[e]=this.targetObject[this.propertyName]}_getValue_array(t,e){let n=this.resolvedProperty;for(let i=0,s=n.length;i!==s;++i)t[e++]=n[i]}_getValue_arrayElement(t,e){t[e]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(t,e){this.resolvedProperty.toArray(t,e)}_setValue_direct(t,e){this.targetObject[this.propertyName]=t[e]}_setValue_direct_setNeedsUpdate(t,e){this.targetObject[this.propertyName]=t[e],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(t,e){this.targetObject[this.propertyName]=t[e],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(t,e){let n=this.resolvedProperty;for(let i=0,s=n.length;i!==s;++i)n[i]=t[e++]}_setValue_array_setNeedsUpdate(t,e){let n=this.resolvedProperty;for(let i=0,s=n.length;i!==s;++i)n[i]=t[e++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(t,e){let n=this.resolvedProperty;for(let i=0,s=n.length;i!==s;++i)n[i]=t[e++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(t,e){this.resolvedProperty[this.propertyIndex]=t[e]}_setValue_arrayElement_setNeedsUpdate(t,e){this.resolvedProperty[this.propertyIndex]=t[e],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(t,e){this.resolvedProperty[this.propertyIndex]=t[e],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(t,e){this.resolvedProperty.fromArray(t,e)}_setValue_fromArray_setNeedsUpdate(t,e){this.resolvedProperty.fromArray(t,e),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(t,e){this.resolvedProperty.fromArray(t,e),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(t,e){this.bind(),this.getValue(t,e)}_setValue_unbound(t,e){this.bind(),this.setValue(t,e)}bind(){let t=this.node,e=this.parsedPath,n=e.objectName,i=e.propertyName,s=e.propertyIndex;if(t||(t=o.findNode(this.rootNode,e.nodeName),this.node=t),this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!t){St("PropertyBinding: No target node found for track: "+this.path+".");return}if(n){let c=e.objectIndex;switch(n){case"materials":if(!t.material){gt("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!t.material.materials){gt("PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}t=t.material.materials;break;case"bones":if(!t.skeleton){gt("PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}t=t.skeleton.bones;for(let u=0;u<t.length;u++)if(t[u].name===c){c=u;break}break;case"map":if("map"in t){t=t.map;break}if(!t.material){gt("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!t.material.map){gt("PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}t=t.material.map;break;default:if(t[n]===void 0){gt("PropertyBinding: Can not bind to objectName of node undefined.",this);return}t=t[n]}if(c!==void 0){if(t[c]===void 0){gt("PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,t);return}t=t[c]}}let r=t[i];if(r===void 0){let c=e.nodeName;gt("PropertyBinding: Trying to update property for track: "+c+"."+i+" but it wasn't found.",t);return}let a=this.Versioning.None;this.targetObject=t,t.isMaterial===!0?a=this.Versioning.NeedsUpdate:t.isObject3D===!0&&(a=this.Versioning.MatrixWorldNeedsUpdate);let l=this.BindingType.Direct;if(s!==void 0){if(i==="morphTargetInfluences"){if(!t.geometry){gt("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!t.geometry.morphAttributes){gt("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}t.morphTargetDictionary[s]!==void 0&&(s=t.morphTargetDictionary[s])}l=this.BindingType.ArrayElement,this.resolvedProperty=r,this.propertyIndex=s}else r.fromArray!==void 0&&r.toArray!==void 0?(l=this.BindingType.HasFromToArray,this.resolvedProperty=r):Array.isArray(r)?(l=this.BindingType.EntireArray,this.resolvedProperty=r):this.propertyName=i;this.getValue=this.GetterByBindingType[l],this.setValue=this.SetterByBindingTypeAndVersioning[l][a]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}};mt.Composite=Tr;mt.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};mt.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};mt.prototype.GetterByBindingType=[mt.prototype._getValue_direct,mt.prototype._getValue_array,mt.prototype._getValue_arrayElement,mt.prototype._getValue_toArray];mt.prototype.SetterByBindingTypeAndVersioning=[[mt.prototype._setValue_direct,mt.prototype._setValue_direct_setNeedsUpdate,mt.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[mt.prototype._setValue_array,mt.prototype._setValue_array_setNeedsUpdate,mt.prototype._setValue_array_setMatrixWorldNeedsUpdate],[mt.prototype._setValue_arrayElement,mt.prototype._setValue_arrayElement_setNeedsUpdate,mt.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[mt.prototype._setValue_fromArray,mt.prototype._setValue_fromArray_setNeedsUpdate,mt.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var kd=new Float32Array(1);var Ko=new lt,ui=class{constructor(t,e,n=0,i=1/0){this.ray=new jn(t,e),this.near=n,this.far=i,this.camera=null,this.layers=new Kn,this.params={Mesh:{},Line:{threshold:1},LOD:{},Points:{threshold:1},Sprite:{}}}set(t,e){this.ray.set(t,e)}setFromCamera(t,e){e.isPerspectiveCamera?(this.ray.origin.setFromMatrixPosition(e.matrixWorld),this.ray.direction.set(t.x,t.y,.5).unproject(e).sub(this.ray.origin).normalize(),this.camera=e):e.isOrthographicCamera?(this.ray.origin.set(t.x,t.y,e.projectionMatrix.elements[14]).unproject(e),this.ray.direction.set(0,0,-1).transformDirection(e.matrixWorld),this.camera=e):gt("Raycaster: Unsupported camera type: "+e.type)}setFromXRController(t){return Ko.identity().extractRotation(t.matrixWorld),this.ray.origin.setFromMatrixPosition(t.matrixWorld),this.ray.direction.set(0,0,-1).applyMatrix4(Ko),this}intersectObject(t,e=!0,n=[]){return Ar(t,this,n,e),n.sort(Qo),n}intersectObjects(t,e=!0,n=[]){for(let i=0,s=t.length;i<s;i++)Ar(t[i],this,n,e);return n.sort(Qo),n}};function Qo(o,t){return o.distance-t.distance}function Ar(o,t,e,n){let i=!0;if(o.layers.test(t.layers)&&o.raycast(t,e)===!1&&(i=!1),i===!0&&n===!0){let s=o.children;for(let r=0,a=s.length;r<a;r++)Ar(s[r],t,e,!0)}}var Qr=class Qr{constructor(t,e,n,i){this.elements=[1,0,0,1],t!==void 0&&this.set(t,e,n,i)}identity(){return this.set(1,0,0,1),this}fromArray(t,e=0){for(let n=0;n<4;n++)this.elements[n]=t[n+e];return this}set(t,e,n,i){let s=this.elements;return s[0]=t,s[2]=e,s[1]=n,s[3]=i,this}};Qr.prototype.isMatrix2=!0;var Rr=Qr;var jo=new _,Hi=new _,vn=new _,Mn=new _,sr=new _,Cc=new _,Ic=new _,Qe=class{constructor(t=new _,e=new _){this.start=t,this.end=e}set(t,e){return this.start.copy(t),this.end.copy(e),this}copy(t){return this.start.copy(t.start),this.end.copy(t.end),this}getCenter(t){return t.addVectors(this.start,this.end).multiplyScalar(.5)}delta(t){return t.subVectors(this.end,this.start)}distanceSq(){return this.start.distanceToSquared(this.end)}distance(){return this.start.distanceTo(this.end)}at(t,e){return this.delta(e).multiplyScalar(t).add(this.start)}closestPointToPointParameter(t,e){jo.subVectors(t,this.start),Hi.subVectors(this.end,this.start);let n=Hi.dot(Hi);if(n===0)return 0;let s=Hi.dot(jo)/n;return e&&(s=Q(s,0,1)),s}closestPointToPoint(t,e,n){let i=this.closestPointToPointParameter(t,e);return this.delta(n).multiplyScalar(i).add(this.start)}distanceSqToLine3(t,e=Cc,n=Ic){let i=10000000000000001e-32,s,r,a=this.start,l=t.start,c=this.end,u=t.end;vn.subVectors(c,a),Mn.subVectors(u,l),sr.subVectors(a,l);let d=vn.dot(vn),h=Mn.dot(Mn),f=Mn.dot(sr);if(d<=i&&h<=i)return e.copy(a),n.copy(l),e.sub(n),e.dot(e);if(d<=i)s=0,r=f/h,r=Q(r,0,1);else{let p=vn.dot(sr);if(h<=i)r=0,s=Q(-p/d,0,1);else{let m=vn.dot(Mn),x=d*h-m*m;x!==0?s=Q((m*f-p*h)/x,0,1):s=0,r=(m*s+f)/h,r<0?(r=0,s=Q(-p/d,0,1)):r>1&&(r=1,s=Q((m-p)/d,0,1))}}return e.copy(a).addScaledVector(vn,s),n.copy(l).addScaledVector(Mn,r),e.distanceToSquared(n)}applyMatrix4(t){return this.start.applyMatrix4(t),this.end.applyMatrix4(t),this}equals(t){return t.start.equals(this.start)&&t.end.equals(this.end)}clone(){return new this.constructor().copy(this)}};typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"186"}}));typeof window<"u"&&(window.__THREE__?St("WARNING: Multiple instances of Three.js being imported."):window.__THREE__="186");var Fc=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,Bc=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,Oc=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,kc=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,zc=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,Hc=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,Vc=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,Gc=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,Wc=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec4 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 );
	}
#endif`,Xc=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,$c=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,qc=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,Yc=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,Zc=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,Jc=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,Kc=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,Qc=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,jc=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,tu=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,eu=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,nu=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,iu=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,su=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec4( 1.0 );
#endif
#ifdef USE_COLOR_ALPHA
	vColor *= color;
#elif defined( USE_COLOR )
	vColor.rgb *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.rgb *= instanceColor.rgb;
#endif
#ifdef USE_BATCHING_COLOR
	vColor *= getBatchingColor( getIndirectIndex( gl_DrawID ) );
#endif`,ru=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
#define inverseTransformDirection transformDirectionByInverseViewMatrix
vec3 transformNormalByInverseViewMatrix( in vec3 normal, in mat4 viewMatrix ) {
	return normalize( ( vec4( normal, 0.0 ) * viewMatrix ).xyz );
}
vec3 transformDirectionByInverseViewMatrix( in vec3 dir, in mat4 viewMatrix ) {
	return normalize( ( vec4( dir, 0.0 ) * viewMatrix ).xyz );
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,ou=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,au=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
#endif`,lu=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,cu=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,uu=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,hu=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,du="gl_FragColor = linearToOutputTexel( gl_FragColor );",fu=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,pu=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * reflectVec );
		#ifdef ENVMAP_BLENDING_MULTIPLY
			outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_MIX )
			outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_ADD )
			outgoingLight += envColor.xyz * specularStrength * reflectivity;
		#endif
	#endif
#endif`,mu=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,gu=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,xu=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,_u=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,yu=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,vu=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,Mu=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,Su=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,bu=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,Eu=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,wu=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,Tu=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,Au=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_SUN_LIGHTS > 0
	struct SunLight {
		vec3 direction;
		vec3 color;
	};
	uniform SunLight sunLights[ NUM_SUN_LIGHTS ];
	void getSunLightInfo( const in SunLight sunLight, out IncidentLight light ) {
		light.color = sunLight.color;
		light.direction = sunLight.direction;
		light.visible = true;
	}
#endif
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif
#include <lightprobes_pars_fragment>`,Ru=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, pow4( roughness ) ) );
			reflectVec = transformDirectionByInverseViewMatrix( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_RETROREFLECTION
		vec3 getIBLRetroRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 retroVec = normalize( mix( viewDir, normal, pow4( roughness ) ) );
				retroVec = transformDirectionByInverseViewMatrix( retroVec, viewMatrix );
				vec4 envMapColor = textureCubeUV( envMap, envMapRotation * retroVec, roughness );
				return envMapColor.rgb * envMapIntensity;
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
		#ifdef USE_RETROREFLECTION
			vec3 getIBLAnisotropyRetroRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
				#ifdef ENVMAP_TYPE_CUBE_UV
					vec3 bentNormal = cross( bitangent, viewDir );
					bentNormal = normalize( cross( bentNormal, bitangent ) );
					bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
					return getIBLRetroRadiance( viewDir, bentNormal, roughness );
				#else
					return vec3( 0.0 );
				#endif
			}
		#endif
	#endif
#endif`,Cu=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,Iu=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,Pu=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,Lu=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,Du=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.diffuseContribution = diffuseColor.rgb * ( 1.0 - metalnessFactor );
material.metalness = metalnessFactor;
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor;
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = vec3( 0.04 );
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_RETROREFLECTION
	material.retroreflectivity = retroreflectivity;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.0001, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,Nu=`uniform sampler2D dfgLUT;
struct PhysicalMaterial {
	vec3 diffuseColor;
	vec3 diffuseContribution;
	vec3 specularColor;
	vec3 specularColorBlended;
	float roughness;
	float metalness;
	float specularF90;
	float dispersion;
	vec2 dfg;
	vec3 multiScatteringCompensation;
	#ifdef USE_RETROREFLECTION
		float retroreflectivity;
	#endif
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0Dielectric;
		vec3 iridescenceF0Metallic;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		return 0.5 / max( gv + gl, EPSILON );
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColorBlended;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transpose( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float rInv = 1.0 / ( roughness + 0.1 );
	float a = -1.9362 + 1.0678 * roughness + 0.4573 * r2 - 0.8469 * rInv;
	float b = -0.6014 + 0.5538 * roughness - 0.4670 * r2 - 0.1255 * rInv;
	float DG = exp( a * dotNV + b );
	return saturate( DG );
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec2 fab, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec2 fab, const in vec3 specularColor, const in float specularF90, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColorBlended * t2.x + ( material.specularF90 - material.specularColorBlended ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseContribution * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
		#ifdef USE_CLEARCOAT
			vec3 Ncc = geometryClearcoatNormal;
			vec2 uvClearcoat = LTC_Uv( Ncc, viewDir, material.clearcoatRoughness );
			vec4 t1Clearcoat = texture2D( ltc_1, uvClearcoat );
			vec4 t2Clearcoat = texture2D( ltc_2, uvClearcoat );
			mat3 mInvClearcoat = mat3(
				vec3( t1Clearcoat.x, 0, t1Clearcoat.y ),
				vec3(             0, 1,             0 ),
				vec3( t1Clearcoat.z, 0, t1Clearcoat.w )
			);
			vec3 fresnelClearcoat = material.clearcoatF0 * t2Clearcoat.x + ( material.clearcoatF90 - material.clearcoatF0 ) * t2Clearcoat.y;
			clearcoatSpecularDirect += lightColor * fresnelClearcoat * LTC_Evaluate( Ncc, viewDir, position, mInvClearcoat, rectCoords );
		#endif
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
 
 		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
 
 		float sheenAlbedoV = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
 		float sheenAlbedoL = IBLSheenBRDF( geometryNormal, directLight.direction, material.sheenRoughness );
 
 		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * max( sheenAlbedoV, sheenAlbedoL );
 
 		irradiance *= sheenEnergyComp;
 
 	#endif
	vec3 specularBRDF = BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );
	#ifdef USE_RETROREFLECTION
		vec3 retroViewDir = reflect( - geometryViewDir, geometryNormal );
		vec3 retroSpecularBRDF = BRDF_GGX( directLight.direction, retroViewDir, geometryNormal, material );
		specularBRDF = mix( specularBRDF, retroSpecularBRDF, saturate( material.retroreflectivity ) );
	#endif
	reflectedLight.directSpecular += irradiance * specularBRDF * material.multiScatteringCompensation;
	vec3 halfDir = normalize( directLight.direction + geometryViewDir );
	float dotVH = saturate( dot( geometryViewDir, halfDir ) );
	vec3 F = F_Schlick( material.specularColor, material.specularF90, dotVH );
	#ifdef USE_RETROREFLECTION
		vec3 retroHalfDir = normalize( directLight.direction + retroViewDir );
		float dotRetroVH = saturate( dot( retroViewDir, retroHalfDir ) );
		vec3 retroF = F_Schlick( material.specularColor, material.specularF90, dotRetroVH );
		F = mix( F, retroF, saturate( material.retroreflectivity ) );
	#endif
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - F );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( material.dfg, material.specularColor, material.specularF90, material.iridescence, material.iridescenceF0Dielectric, singleScattering, multiScattering );
	#else
		computeMultiscattering( material.dfg, material.specularColor, material.specularF90, singleScattering, multiScattering );
	#endif
	vec3 diffuse = irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - singleScattering - multiScattering );
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		sheenSpecularIndirect += irradiance * material.sheenColor * sheenAlbedo * RECIPROCAL_PI;
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		diffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectDiffuse += diffuse;
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness ) * RECIPROCAL_PI;
 	#endif
	vec3 singleScatteringDielectric = vec3( 0.0 );
	vec3 multiScatteringDielectric = vec3( 0.0 );
	vec3 singleScatteringMetallic = vec3( 0.0 );
	vec3 multiScatteringMetallic = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( material.dfg, material.specularColor, material.specularF90, material.iridescence, material.iridescenceF0Dielectric, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscatteringIridescence( material.dfg, material.diffuseColor, material.specularF90, material.iridescence, material.iridescenceF0Metallic, singleScatteringMetallic, multiScatteringMetallic );
	#else
		computeMultiscattering( material.dfg, material.specularColor, material.specularF90, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscattering( material.dfg, material.diffuseColor, material.specularF90, singleScatteringMetallic, multiScatteringMetallic );
	#endif
	vec3 singleScattering = mix( singleScatteringDielectric, singleScatteringMetallic, material.metalness );
	vec3 multiScattering = mix( multiScatteringDielectric, multiScatteringMetallic, material.metalness );
	vec3 totalScatteringDielectric = singleScatteringDielectric + multiScatteringDielectric;
	vec3 diffuse = material.diffuseContribution * ( 1.0 - totalScatteringDielectric );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	vec3 indirectSpecular = radiance * singleScattering;
	indirectSpecular += multiScattering * cosineWeightedIrradiance;
	vec3 indirectDiffuse = diffuse * cosineWeightedIrradiance;
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		indirectSpecular *= sheenEnergyComp;
		indirectDiffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectSpecular += indirectSpecular;
	reflectedLight.indirectDiffuse += indirectDiffuse;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,Uu=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		vec3 iridescenceFresnelDielectric = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		vec3 iridescenceFresnelMetallic = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.diffuseColor );
		material.iridescenceFresnel = mix( iridescenceFresnelDielectric, iridescenceFresnelMetallic, material.metalness );
		material.iridescenceF0Dielectric = Schlick_to_F0( iridescenceFresnelDielectric, 1.0, dotNVi );
		material.iridescenceF0Metallic = Schlick_to_F0( iridescenceFresnelMetallic, 1.0, dotNVi );
	}
#endif
#ifdef STANDARD
	float dotNVms = saturate( dot( geometryNormal, geometryViewDir ) );
	material.dfg = texture2D( dfgLUT, vec2( material.roughness, dotNVms ) ).rg;
	#if ( NUM_SUN_LIGHTS > 0 || NUM_DIR_LIGHTS > 0 || NUM_POINT_LIGHTS > 0 || NUM_SPOT_LIGHTS > 0 )
		float EssMs = material.dfg.x + material.dfg.y;
		material.multiScatteringCompensation = 1.0 + material.specularColorBlended * ( 1.0 / EssMs - 1.0 );
	#endif
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS ) && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SUN_LIGHTS > 0 ) && defined( RE_Direct )
	SunLight sunLight;
	#if defined( USE_SHADOWMAP ) && NUM_SUN_LIGHT_SHADOWS > 0
	SunLightShadow sunLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SUN_LIGHTS; i ++ ) {
		sunLight = sunLights[ i ];
		getSunLightInfo( sunLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SUN_LIGHT_SHADOWS )
		sunLightShadow = sunLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getSunShadow( sunShadowMap[ i ], sunLightShadow, UNROLLED_LOOP_INDEX ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
	#ifdef USE_LIGHT_PROBES_GRID
		vec3 probeWorldPos = ( ( vec4( geometryPosition, 1.0 ) - viewMatrix[ 3 ] ) * viewMatrix ).xyz;
		vec3 probeWorldNormal = transformNormalByInverseViewMatrix( geometryNormal, viewMatrix );
		irradiance += getLightProbeGridIrradiance( probeWorldPos, probeWorldNormal );
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,Fu=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( ENVMAP_TYPE_CUBE_UV )
		#if defined( STANDARD ) || defined( LAMBERT ) || defined( PHONG )
			iblIrradiance += getIBLIrradiance( geometryNormal );
		#endif
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		vec3 iblRadiance = getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		vec3 iblRadiance = getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_RETROREFLECTION
		#ifdef USE_ANISOTROPY
			vec3 retroIBLRadiance = getIBLAnisotropyRetroRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
		#else
			vec3 retroIBLRadiance = getIBLRetroRadiance( geometryViewDir, geometryNormal, material.roughness );
		#endif
		iblRadiance = mix( iblRadiance, retroIBLRadiance, saturate( material.retroreflectivity ) );
	#endif
	radiance += iblRadiance;
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,Bu=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,Ou=`#ifdef USE_LIGHT_PROBES_GRID
uniform highp sampler3D probesSH;
uniform vec3 probesMin;
uniform vec3 probesMax;
uniform vec3 probesResolution;
vec3 getLightProbeGridIrradiance( vec3 worldPos, vec3 worldNormal ) {
	vec3 res = probesResolution;
	vec3 gridRange = probesMax - probesMin;
	vec3 resMinusOne = res - 1.0;
	vec3 probeSpacing = gridRange / resMinusOne;
	vec3 samplePos = worldPos + worldNormal * probeSpacing * 0.5;
	vec3 uvw = clamp( ( samplePos - probesMin ) / gridRange, 0.0, 1.0 );
	uvw = uvw * resMinusOne / res + 0.5 / res;
	float nz          = res.z;
	float paddedSlices = nz + 2.0;
	float atlasDepth  = 7.0 * paddedSlices;
	float uvZBase     = uvw.z * nz + 1.0;
	vec4 s0 = texture( probesSH, vec3( uvw.xy, ( uvZBase                       ) / atlasDepth ) );
	vec4 s1 = texture( probesSH, vec3( uvw.xy, ( uvZBase +       paddedSlices   ) / atlasDepth ) );
	vec4 s2 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 2.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s3 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 3.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s4 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 4.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s5 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 5.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s6 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 6.0 * paddedSlices   ) / atlasDepth ) );
	vec3 c0 = s0.xyz;
	vec3 c1 = vec3( s0.w, s1.xy );
	vec3 c2 = vec3( s1.zw, s2.x );
	vec3 c3 = s2.yzw;
	vec3 c4 = s3.xyz;
	vec3 c5 = vec3( s3.w, s4.xy );
	vec3 c6 = vec3( s4.zw, s5.x );
	vec3 c7 = s5.yzw;
	vec3 c8 = s6.xyz;
	float x = worldNormal.x, y = worldNormal.y, z = worldNormal.z;
	vec3 result = c0 * 0.886227;
	result += c1 * 2.0 * 0.511664 * y;
	result += c2 * 2.0 * 0.511664 * z;
	result += c3 * 2.0 * 0.511664 * x;
	result += c4 * 2.0 * 0.429043 * x * y;
	result += c5 * 2.0 * 0.429043 * y * z;
	result += c6 * ( 0.743125 * z * z - 0.247708 );
	result += c7 * 2.0 * 0.429043 * x * z;
	result += c8 * 0.429043 * ( x * x - y * y );
	return max( result, vec3( 0.0 ) );
}
#endif`,ku=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,zu=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,Hu=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,Vu=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,Gu=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,Wu=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,Xu=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,$u=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,qu=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,Yu=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,Zu=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,Ju=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,Ku=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,Qu=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,ju=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,th=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#ifdef DOUBLE_SIDED
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#ifdef DOUBLE_SIDED
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,eh=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#if defined( USE_PACKED_NORMALMAP )
		mapN = vec3( mapN.xy, sqrt( saturate( 1.0 - dot( mapN.xy, mapN.xy ) ) ) );
	#endif
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,nh=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,ih=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,sh=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
		#ifdef FLIP_SIDED
			vBitangent = - vBitangent;
		#endif
	#endif
#endif`,rh=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,oh=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,ah=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,lh=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,ch=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,uh=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,hh=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	#ifdef USE_REVERSED_DEPTH_BUFFER
	
		return depth * ( far - near ) - far;
	#else
		return depth * ( near - far ) - near;
	#endif
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	
	#ifdef USE_REVERSED_DEPTH_BUFFER
		return ( near * far ) / ( ( near - far ) * depth - near );
	#else
		return ( near * far ) / ( ( far - near ) * depth - far );
	#endif
}`,dh=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,fh=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,ph=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,mh=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,gh=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,xh=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,_h=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
		#define SUN_LIGHT_CASCADES 2
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow sunShadowMap[ NUM_SUN_LIGHT_SHADOWS ];
		#else
			uniform sampler2D sunShadowMap[ NUM_SUN_LIGHT_SHADOWS ];
		#endif
		uniform mat4 sunShadowMatrix[ NUM_SUN_LIGHT_SHADOWS * SUN_LIGHT_CASCADES ];
		uniform vec4 sunShadowCascade[ NUM_SUN_LIGHT_SHADOWS * SUN_LIGHT_CASCADES ];
		varying vec4 vSunShadowWorldPosition;
		varying vec3 vSunShadowWorldNormal;
		struct SunLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SunLightShadow sunLightShadows[ NUM_SUN_LIGHT_SHADOWS ];
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#else
			uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#endif
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#else
			uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#endif
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform samplerCubeShadow pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#elif defined( SHADOWMAP_TYPE_BASIC )
			uniform samplerCube pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#endif
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float interleavedGradientNoise( vec2 position ) {
			return fract( 52.9829189 * fract( dot( position, vec2( 0.06711056, 0.00583715 ) ) ) );
		}
		vec2 vogelDiskSample( int sampleIndex, int samplesCount, float phi ) {
			const float goldenAngle = 2.399963229728653;
			float r = sqrt( ( float( sampleIndex ) + 0.5 ) / float( samplesCount ) );
			float theta = float( sampleIndex ) * goldenAngle + phi;
			return vec2( cos( theta ), sin( theta ) ) * r;
		}
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float getShadow( sampler2DShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
				float radius = shadowRadius * texelSize.x;
				float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
				shadow = (
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 0, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 1, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 2, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 3, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 4, 5, phi ) * radius, shadowCoord.z ) )
				) * 0.2;
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#elif defined( SHADOWMAP_TYPE_VSM )
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 distribution = texture2D( shadowMap, shadowCoord.xy ).rg;
				float mean = distribution.x;
				float variance = distribution.y * distribution.y;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					float hard_shadow = step( mean, shadowCoord.z );
				#else
					float hard_shadow = step( shadowCoord.z, mean );
				#endif
				
				if ( hard_shadow == 1.0 ) {
					shadow = 1.0;
				} else {
					variance = max( variance, 0.0000001 );
					float d = shadowCoord.z - mean;
					float p_max = variance / ( variance + d * d );
					p_max = clamp( ( p_max - 0.3 ) / 0.65, 0.0, 1.0 );
					shadow = max( hard_shadow, p_max );
				}
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#else
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				float depth = texture2D( shadowMap, shadowCoord.xy ).r;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					shadow = step( depth, shadowCoord.z );
				#else
					shadow = step( shadowCoord.z, depth );
				#endif
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#endif
	#if NUM_SUN_LIGHT_SHADOWS > 0
		float getSunShadow(
			#if defined( SHADOWMAP_TYPE_PCF )
				sampler2DShadow shadowMap,
			#else
				sampler2D shadowMap,
			#endif
			SunLightShadow sunLightShadow,
			int shadowIndex
		) {
			vec4 shadowWorldPosition = vec4( vSunShadowWorldPosition.xyz + vSunShadowWorldNormal * sunLightShadow.shadowNormalBias, 1.0 );
			float viewDepth = vSunShadowWorldPosition.w;
			int cascadeOffset = shadowIndex * SUN_LIGHT_CASCADES;
			float shadow = 1.0;
			for ( int i = SUN_LIGHT_CASCADES - 1; i >= 0; i -- ) {
				vec4 cascade = sunShadowCascade[ cascadeOffset + i ];
				if ( viewDepth >= cascade.x && viewDepth < cascade.y ) {
					float cascadeShadow = getShadow(
						shadowMap,
						sunLightShadow.shadowMapSize,
						sunLightShadow.shadowIntensity,
						sunLightShadow.shadowBias,
						sunLightShadow.shadowRadius,
						sunShadowMatrix[ cascadeOffset + i ] * shadowWorldPosition
					);
					shadow = mix( cascadeShadow, shadow, smoothstep( cascade.z, cascade.y, viewDepth ) );
				}
			}
			return shadow;
		}
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	#if defined( SHADOWMAP_TYPE_PCF )
	float getPointShadow( samplerCubeShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 bd3D = normalize( lightToPosition );
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			#ifdef USE_REVERSED_DEPTH_BUFFER
				float dp = ( shadowCameraNear * ( shadowCameraFar - viewSpaceZ ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp -= shadowBias;
			#else
				float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp += shadowBias;
			#endif
			float texelSize = shadowRadius / shadowMapSize.x;
			vec3 absDir = abs( bd3D );
			vec3 tangent = absDir.x > absDir.z ? vec3( 0.0, 1.0, 0.0 ) : vec3( 1.0, 0.0, 0.0 );
			tangent = normalize( cross( bd3D, tangent ) );
			vec3 bitangent = cross( bd3D, tangent );
			float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
			vec2 sample0 = vogelDiskSample( 0, 5, phi );
			vec2 sample1 = vogelDiskSample( 1, 5, phi );
			vec2 sample2 = vogelDiskSample( 2, 5, phi );
			vec2 sample3 = vogelDiskSample( 3, 5, phi );
			vec2 sample4 = vogelDiskSample( 4, 5, phi );
			shadow = (
				texture( shadowMap, vec4( bd3D + ( tangent * sample0.x + bitangent * sample0.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample1.x + bitangent * sample1.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample2.x + bitangent * sample2.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample3.x + bitangent * sample3.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample4.x + bitangent * sample4.y ) * texelSize, dp ) )
			) * 0.2;
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#elif defined( SHADOWMAP_TYPE_BASIC )
	float getPointShadow( samplerCube shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			float depth = textureCube( shadowMap, bd3D ).r;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				depth = 1.0 - depth;
			#endif
			shadow = step( dp, depth );
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#endif
	#endif
#endif`,yh=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
		varying vec4 vSunShadowWorldPosition;
		varying vec3 vSunShadowWorldNormal;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,vh=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_SUN_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	#ifdef HAS_NORMAL
		vec3 shadowWorldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
	#else
		vec3 shadowWorldNormal = vec3( 0.0 );
	#endif
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_SUN_LIGHT_SHADOWS > 0
		vSunShadowWorldPosition = vec4( worldPosition.xyz, - mvPosition.z );
		vSunShadowWorldNormal = shadowWorldNormal;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,Mh=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
	SunLightShadow sunLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SUN_LIGHT_SHADOWS; i ++ ) {
		sunLight = sunLightShadows[ i ];
		shadow *= receiveShadow ? getSunShadow( sunShadowMap[ i ], sunLight, UNROLLED_LOOP_INDEX ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0 && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,Sh=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,bh=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,Eh=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,wh=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,Th=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,Ah=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,Rh=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,Ch=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,Ih=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseContribution, material.specularColorBlended, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,Ph=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,Lh=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,Dh=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,Nh=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,Uh=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,Fh=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,Bh=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Oh=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,kh=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vWorldDirection );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,zh=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,Hh=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Vh=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,Gh=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,Wh=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,Xh=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = vec4( dist, 0.0, 0.0, 1.0 );
}`,$h=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,qh=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Yh=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,Zh=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Jh=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,Kh=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Qh=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,jh=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,td=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,ed=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,nd=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,id=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( normalize( normal ) * 0.5 + 0.5, diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,sd=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,rd=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,od=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,ad=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_RETROREFLECTION
	uniform float retroreflectivity;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
 
		outgoingLight = outgoingLight + sheenSpecularDirect + sheenSpecularIndirect;
 
 	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,ld=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,cd=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,ud=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,hd=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,dd=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,fd=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,pd=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,md=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,at={alphahash_fragment:Fc,alphahash_pars_fragment:Bc,alphamap_fragment:Oc,alphamap_pars_fragment:kc,alphatest_fragment:zc,alphatest_pars_fragment:Hc,aomap_fragment:Vc,aomap_pars_fragment:Gc,batching_pars_vertex:Wc,batching_vertex:Xc,begin_vertex:$c,beginnormal_vertex:qc,bsdfs:Yc,iridescence_fragment:Zc,bumpmap_pars_fragment:Jc,clipping_planes_fragment:Kc,clipping_planes_pars_fragment:Qc,clipping_planes_pars_vertex:jc,clipping_planes_vertex:tu,color_fragment:eu,color_pars_fragment:nu,color_pars_vertex:iu,color_vertex:su,common:ru,cube_uv_reflection_fragment:ou,defaultnormal_vertex:au,displacementmap_pars_vertex:lu,displacementmap_vertex:cu,emissivemap_fragment:uu,emissivemap_pars_fragment:hu,colorspace_fragment:du,colorspace_pars_fragment:fu,envmap_fragment:pu,envmap_common_pars_fragment:mu,envmap_pars_fragment:gu,envmap_pars_vertex:xu,envmap_physical_pars_fragment:Ru,envmap_vertex:_u,fog_vertex:yu,fog_pars_vertex:vu,fog_fragment:Mu,fog_pars_fragment:Su,gradientmap_pars_fragment:bu,lightmap_pars_fragment:Eu,lights_lambert_fragment:wu,lights_lambert_pars_fragment:Tu,lights_pars_begin:Au,lights_toon_fragment:Cu,lights_toon_pars_fragment:Iu,lights_phong_fragment:Pu,lights_phong_pars_fragment:Lu,lights_physical_fragment:Du,lights_physical_pars_fragment:Nu,lights_fragment_begin:Uu,lights_fragment_maps:Fu,lights_fragment_end:Bu,lightprobes_pars_fragment:Ou,logdepthbuf_fragment:ku,logdepthbuf_pars_fragment:zu,logdepthbuf_pars_vertex:Hu,logdepthbuf_vertex:Vu,map_fragment:Gu,map_pars_fragment:Wu,map_particle_fragment:Xu,map_particle_pars_fragment:$u,metalnessmap_fragment:qu,metalnessmap_pars_fragment:Yu,morphinstance_vertex:Zu,morphcolor_vertex:Ju,morphnormal_vertex:Ku,morphtarget_pars_vertex:Qu,morphtarget_vertex:ju,normal_fragment_begin:th,normal_fragment_maps:eh,normal_pars_fragment:nh,normal_pars_vertex:ih,normal_vertex:sh,normalmap_pars_fragment:rh,clearcoat_normal_fragment_begin:oh,clearcoat_normal_fragment_maps:ah,clearcoat_pars_fragment:lh,iridescence_pars_fragment:ch,opaque_fragment:uh,packing:hh,premultiplied_alpha_fragment:dh,project_vertex:fh,dithering_fragment:ph,dithering_pars_fragment:mh,roughnessmap_fragment:gh,roughnessmap_pars_fragment:xh,shadowmap_pars_fragment:_h,shadowmap_pars_vertex:yh,shadowmap_vertex:vh,shadowmask_pars_fragment:Mh,skinbase_vertex:Sh,skinning_pars_vertex:bh,skinning_vertex:Eh,skinnormal_vertex:wh,specularmap_fragment:Th,specularmap_pars_fragment:Ah,tonemapping_fragment:Rh,tonemapping_pars_fragment:Ch,transmission_fragment:Ih,transmission_pars_fragment:Ph,uv_pars_fragment:Lh,uv_pars_vertex:Dh,uv_vertex:Nh,worldpos_vertex:Uh,background_vert:Fh,background_frag:Bh,backgroundCube_vert:Oh,backgroundCube_frag:kh,cube_vert:zh,cube_frag:Hh,depth_vert:Vh,depth_frag:Gh,distance_vert:Wh,distance_frag:Xh,equirect_vert:$h,equirect_frag:qh,linedashed_vert:Yh,linedashed_frag:Zh,meshbasic_vert:Jh,meshbasic_frag:Kh,meshlambert_vert:Qh,meshlambert_frag:jh,meshmatcap_vert:td,meshmatcap_frag:ed,meshnormal_vert:nd,meshnormal_frag:id,meshphong_vert:sd,meshphong_frag:rd,meshphysical_vert:od,meshphysical_frag:ad,meshtoon_vert:ld,meshtoon_frag:cd,points_vert:ud,points_frag:hd,shadow_vert:dd,shadow_frag:fd,sprite_vert:pd,sprite_frag:md},z={common:{diffuse:{value:new ft(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new nt},alphaMap:{value:null},alphaMapTransform:{value:new nt},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new nt}},envmap:{envMap:{value:null},envMapRotation:{value:new nt},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new nt}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new nt}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new nt},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new nt},normalScale:{value:new O(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new nt},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new nt}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new nt}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new nt}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new ft(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},sunLights:{value:[],properties:{direction:{},color:{}}},sunLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},sunShadowMatrix:{value:[]},sunShadowCascade:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new _},probesMax:{value:new _},probesResolution:{value:new _}},points:{diffuse:{value:new ft(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new nt},alphaTest:{value:0},uvTransform:{value:new nt}},sprite:{diffuse:{value:new ft(16777215)},opacity:{value:1},center:{value:new O(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new nt},alphaMap:{value:null},alphaMapTransform:{value:new nt},alphaTest:{value:0}}},Ta={basic:{uniforms:Ot([z.common,z.specularmap,z.envmap,z.aomap,z.lightmap,z.fog]),vertexShader:at.meshbasic_vert,fragmentShader:at.meshbasic_frag},lambert:{uniforms:Ot([z.common,z.specularmap,z.envmap,z.aomap,z.lightmap,z.emissivemap,z.bumpmap,z.normalmap,z.displacementmap,z.fog,z.lights,{emissive:{value:new ft(0)},envMapIntensity:{value:1}}]),vertexShader:at.meshlambert_vert,fragmentShader:at.meshlambert_frag},phong:{uniforms:Ot([z.common,z.specularmap,z.envmap,z.aomap,z.lightmap,z.emissivemap,z.bumpmap,z.normalmap,z.displacementmap,z.fog,z.lights,{emissive:{value:new ft(0)},specular:{value:new ft(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:at.meshphong_vert,fragmentShader:at.meshphong_frag},standard:{uniforms:Ot([z.common,z.envmap,z.aomap,z.lightmap,z.emissivemap,z.bumpmap,z.normalmap,z.displacementmap,z.roughnessmap,z.metalnessmap,z.fog,z.lights,{emissive:{value:new ft(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:at.meshphysical_vert,fragmentShader:at.meshphysical_frag},toon:{uniforms:Ot([z.common,z.aomap,z.lightmap,z.emissivemap,z.bumpmap,z.normalmap,z.displacementmap,z.gradientmap,z.fog,z.lights,{emissive:{value:new ft(0)}}]),vertexShader:at.meshtoon_vert,fragmentShader:at.meshtoon_frag},matcap:{uniforms:Ot([z.common,z.bumpmap,z.normalmap,z.displacementmap,z.fog,{matcap:{value:null}}]),vertexShader:at.meshmatcap_vert,fragmentShader:at.meshmatcap_frag},points:{uniforms:Ot([z.points,z.fog]),vertexShader:at.points_vert,fragmentShader:at.points_frag},dashed:{uniforms:Ot([z.common,z.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:at.linedashed_vert,fragmentShader:at.linedashed_frag},depth:{uniforms:Ot([z.common,z.displacementmap]),vertexShader:at.depth_vert,fragmentShader:at.depth_frag},normal:{uniforms:Ot([z.common,z.bumpmap,z.normalmap,z.displacementmap,{opacity:{value:1}}]),vertexShader:at.meshnormal_vert,fragmentShader:at.meshnormal_frag},sprite:{uniforms:Ot([z.sprite,z.fog]),vertexShader:at.sprite_vert,fragmentShader:at.sprite_frag},background:{uniforms:{uvTransform:{value:new nt},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:at.background_vert,fragmentShader:at.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new nt}},vertexShader:at.backgroundCube_vert,fragmentShader:at.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:at.cube_vert,fragmentShader:at.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:at.equirect_vert,fragmentShader:at.equirect_frag},distance:{uniforms:Ot([z.common,z.displacementmap,{referencePosition:{value:new _},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:at.distance_vert,fragmentShader:at.distance_frag},shadow:{uniforms:Ot([z.lights,z.fog,{color:{value:new ft(0)},opacity:{value:1}}]),vertexShader:at.shadow_vert,fragmentShader:at.shadow_frag}};Ta.physical={uniforms:Ot([Ta.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new nt},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new nt},clearcoatNormalScale:{value:new O(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new nt},dispersion:{value:0},retroreflectivity:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new nt},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new nt},sheen:{value:0},sheenColor:{value:new ft(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new nt},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new nt},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new nt},transmissionSamplerSize:{value:new O},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new nt},attenuationDistance:{value:0},attenuationColor:{value:new ft(0)},specularColor:{value:new ft(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new nt},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new nt},anisotropyVector:{value:new O},anisotropyMap:{value:null},anisotropyMapTransform:{value:new nt}}]),vertexShader:at.meshphysical_vert,fragmentShader:at.meshphysical_frag};var gd=new nt;gd.set(-1,0,0,0,1,0,0,0,1);var ax={[Pr]:"LINEAR_TONE_MAPPING",[Lr]:"REINHARD_TONE_MAPPING",[Dr]:"CINEON_TONE_MAPPING",[Nr]:"ACES_FILMIC_TONE_MAPPING",[Fr]:"AGX_TONE_MAPPING",[Br]:"NEUTRAL_TONE_MAPPING",[Ur]:"CUSTOM_TONE_MAPPING"};var lx=new Float32Array(16),cx=new Float32Array(9),ux=new Float32Array(4);var hx={[Pr]:"Linear",[Lr]:"Reinhard",[Dr]:"Cineon",[Nr]:"ACESFilmic",[Fr]:"AgX",[Br]:"Neutral",[Ur]:"Custom"};var dx={[ta]:"SHADOWMAP_TYPE_PCF",[ea]:"SHADOWMAP_TYPE_VSM"};var fx={[la]:"ENVMAP_TYPE_CUBE",[kr]:"ENVMAP_TYPE_CUBE",[ca]:"ENVMAP_TYPE_CUBE_UV"};var px={[kr]:"ENVMAP_MODE_REFRACTION"};var mx={[Ir]:"ENVMAP_BLENDING_MULTIPLY",[oa]:"ENVMAP_BLENDING_MIX",[aa]:"ENVMAP_BLENDING_ADD"};var xd=new nt;xd.set(-1,0,0,0,1,0,0,0,1);var gx=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]);function di(o,t=!1){let e=o[0].index!==null,n=new Set(Object.keys(o[0].attributes)),i=new Set(Object.keys(o[0].morphAttributes)),s={},r={},a=o[0].morphTargetsRelative,l=new Pt,c=0;for(let u=0;u<o.length;++u){let d=o[u],h=0;if(e!==(d.index!==null))return console.error("THREE.BufferGeometryUtils: .mergeGeometries() failed with geometry at index "+u+". All geometries must have compatible attributes; make sure index attribute exists among all geometries, or in none of them."),null;for(let f in d.attributes){if(!n.has(f))return console.error("THREE.BufferGeometryUtils: .mergeGeometries() failed with geometry at index "+u+'. All geometries must have compatible attributes; make sure "'+f+'" attribute exists among all geometries, or in none of them.'),null;s[f]===void 0&&(s[f]=[]),s[f].push(d.attributes[f]),h++}if(h!==n.size)return console.error("THREE.BufferGeometryUtils: .mergeGeometries() failed with geometry at index "+u+". Make sure all geometries have the same number of attributes."),null;if(a!==d.morphTargetsRelative)return console.error("THREE.BufferGeometryUtils: .mergeGeometries() failed with geometry at index "+u+". .morphTargetsRelative must be consistent throughout all geometries."),null;for(let f in d.morphAttributes){if(!i.has(f))return console.error("THREE.BufferGeometryUtils: .mergeGeometries() failed with geometry at index "+u+".  .morphAttributes must be consistent throughout all geometries."),null;r[f]===void 0&&(r[f]=[]),r[f].push(d.morphAttributes[f])}if(t){let f;if(e)f=d.index.count;else if(d.attributes.position!==void 0)f=d.attributes.position.count;else return console.error("THREE.BufferGeometryUtils: .mergeGeometries() failed with geometry at index "+u+". The geometry must have either an index or a position attribute"),null;l.addGroup(c,f,u),c+=f}}if(e){let u=0,d=[];for(let h=0;h<o.length;++h){let f=o[h].index;for(let p=0;p<f.count;++p)d.push(f.getX(p)+u);u+=o[h].attributes.position.count}l.setIndex(d)}for(let u in s){let d=Aa(s[u]);if(!d)return console.error("THREE.BufferGeometryUtils: .mergeGeometries() failed while trying to merge the "+u+" attribute."),null;l.setAttribute(u,d)}for(let u in r){let d=r[u][0].length;if(d!==0){l.morphAttributes=l.morphAttributes||{},l.morphAttributes[u]=[];for(let h=0;h<d;++h){let f=[];for(let m=0;m<r[u].length;++m)f.push(r[u][m][h]);let p=Aa(f);if(!p)return console.error("THREE.BufferGeometryUtils: .mergeGeometries() failed while trying to merge the "+u+" morphAttribute."),null;l.morphAttributes[u].push(p)}}}return l}function Aa(o){let t,e,n,i=-1,s=0;for(let c=0;c<o.length;++c){let u=o[c];if(t===void 0&&(t=u.array.constructor),t!==u.array.constructor)return console.error("THREE.BufferGeometryUtils: .mergeAttributes() failed. BufferAttribute.array must be of consistent array types across matching attributes."),null;if(e===void 0&&(e=u.itemSize),e!==u.itemSize)return console.error("THREE.BufferGeometryUtils: .mergeAttributes() failed. BufferAttribute.itemSize must be consistent across matching attributes."),null;if(n===void 0&&(n=u.normalized),n!==u.normalized)return console.error("THREE.BufferGeometryUtils: .mergeAttributes() failed. BufferAttribute.normalized must be consistent across matching attributes."),null;if(i===-1&&(i=u.gpuType),i!==u.gpuType)return console.error("THREE.BufferGeometryUtils: .mergeAttributes() failed. BufferAttribute.gpuType must be consistent across matching attributes."),null;s+=u.count*e}let r=new t(s),a=new te(r,e,n),l=0;for(let c=0;c<o.length;++c){let u=o[c];if(u.isInterleavedBufferAttribute){let d=l/e;for(let h=0,f=u.count;h<f;h++)for(let p=0;p<e;p++){let m=u.getComponent(h,p);a.setComponent(h+d,p,m)}}else r.set(u.array,l);l+=u.count*e}return i!==void 0&&(a.gpuType=i),a}var it=o=>new _(o[0],o[2],-o[1]);function _d(o,t,e=8){let n=o.map(r=>r.isVector3?r.clone():new _(...r)),i=[n[0]];for(let r of n.slice(1))r.distanceTo(i[i.length-1])>1e-5&&i.push(r);if(i.length<3||t<=0)return i;let s=[i[0].clone()];for(let r=1;r<i.length-1;r++){let a=i[r-1],l=i[r],c=i[r+1],u=l.clone().sub(a),d=c.clone().sub(l),h=u.length(),f=d.length();u.normalize(),d.normalize();let p=u.angleTo(d);if(p<.001){s.push(l.clone());continue}let m=Math.min(t*Math.tan(p/2),h*.48,f*.48),x=l.clone().addScaledVector(u,-m),v=l.clone().addScaledVector(d,m),S=new In(x,l,v);for(let y=0;y<=e;y++)s.push(S.getPoint(y/e))}return s.push(i[i.length-1].clone()),s}function ne(o,t,e=10,{caps:n=!0}={}){let i=o.length;if(i<2)return null;let s=o.map((p,m)=>{let x=o[Math.max(0,m-1)];return o[Math.min(i-1,m+1)].clone().sub(x).normalize()}),r=new _(0,1,0);Math.abs(r.dot(s[0]))>.9&&r.set(1,0,0),r.sub(s[0].clone().multiplyScalar(r.dot(s[0]))).normalize();let a=[r.clone()];for(let p=1;p<i;p++){let m=s[p-1].clone().cross(s[p]),x=m.length();if(x>1e-8){let v=Math.acos(Wr.clamp(s[p-1].dot(s[p]),-1,1));r=r.clone().applyAxisAngle(m.divideScalar(x),v)}a.push(r.clone())}let l=[],c=[],u=[],d=[],h=0;for(let p=0;p<i;p++){p&&(h+=o[p].distanceTo(o[p-1]));let m=s[p],x=a[p],v=m.clone().cross(x).normalize();for(let S=0;S<=e;S++){let y=S/e*Math.PI*2,M=x.clone().multiplyScalar(Math.cos(y)).addScaledVector(v,Math.sin(y));l.push(o[p].x+M.x*t,o[p].y+M.y*t,o[p].z+M.z*t),c.push(M.x,M.y,M.z),u.push(S/e,h)}}for(let p=0;p<i-1;p++)for(let m=0;m<e;m++){let x=p*(e+1)+m,v=x+e+1;d.push(x,v,x+1,v,v+1,x+1)}if(n)for(let[p,m]of[[0,-1],[i-1,1]]){let x=l.length/3,v=s[p];l.push(o[p].x,o[p].y,o[p].z),c.push(v.x*m,v.y*m,v.z*m),u.push(.5,.5);for(let S=0;S<=e;S++){let y=p*(e+1)+S;l.push(l[y*3],l[y*3+1],l[y*3+2]),c.push(v.x*m,v.y*m,v.z*m),u.push(0,0)}for(let S=0;S<e;S++){let y=x+1+S,M=y+1;m<0?d.push(x,M,y):d.push(x,y,M)}}let f=new Pt;return f.setAttribute("position",new ct(l,3)),f.setAttribute("normal",new ct(c,3)),f.setAttribute("uv",new ct(u,2)),f.setIndex(d),f}function Ra(o,t,{bend:e=t*4,radial:n=10,bendSegments:i=8,caps:s=!0}={}){return ne(_d(o,e,i),t,n,{caps:s})}function Ca(o,t,{samples:e=40,radial:n=8,tension:i=.5}={}){let s=new Le(o.map(r=>r.isVector3?r:new _(...r)),!1,"centripetal",i);return ne(s.getPoints(e),t,n)}function tn(o,t,e,n=.006,i=.0015){let s=o/2-i,r=t/2-i,a=Math.min(n,s,r),l=new ye;l.moveTo(-s+a,-r),l.lineTo(s-a,-r),l.quadraticCurveTo(s,-r,s,-r+a),l.lineTo(s,r-a),l.quadraticCurveTo(s,r,s-a,r),l.lineTo(-s+a,r),l.quadraticCurveTo(-s,r,-s,r-a),l.lineTo(-s,-r+a),l.quadraticCurveTo(-s,-r,-s+a,-r);let c=new De(l,{depth:Math.max(1e-4,e-2*i),bevelEnabled:i>0,bevelThickness:i,bevelSize:i,bevelSegments:2,curveSegments:6});return c.translate(0,0,i),c}function Oe(o,t,e,n,i,s=.004){let r=new ye,a=o/2,l=t/2;r.moveTo(-a,-l),r.lineTo(a,-l),r.lineTo(a,l),r.lineTo(-a,l),r.lineTo(-a,-l);let c=new Je,u=e/2,d=n/2;return c.moveTo(-u+s,-d),c.lineTo(u-s,-d),c.quadraticCurveTo(u,-d,u,-d+s),c.lineTo(u,d-s),c.quadraticCurveTo(u,d,u-s,d),c.lineTo(-u+s,d),c.quadraticCurveTo(-u,d,-u,d-s),c.lineTo(-u,-d+s),c.quadraticCurveTo(-u,-d,-u+s,-d),r.holes.push(c),new De(r,{depth:i,bevelEnabled:!1,curveSegments:4})}function ys(o,t,e,n=.0012){let i=[],s=new ot(o,t,n);s.translate(0,0,-e+n/2),i.push(s);let r=new ot(o,n,e);r.translate(0,t/2-n/2,-e/2),i.push(r);let a=new ot(o,n,e);a.translate(0,-t/2+n/2,-e/2),i.push(a);let l=new ot(n,t,e);l.translate(-o/2+n/2,0,-e/2),i.push(l);let c=new ot(n,t,e);return c.translate(o/2-n/2,0,-e/2),i.push(c),di(i.map(u=>u.toNonIndexed()))}var vs=class{constructor(t){this.data=t,this.byId=new Map;for(let e of["enclosures","devices","terminals","switches","regulators","points","boxes","circuits","conduits","conductors","rooms"])for(let n of t[e])n._type=e,this.byId.set(n.id,n);this.sources=new Map(t.sources.map(e=>[e.id,e])),this.facts=new Map(t.facts.map(e=>[e.id,e])),this.assumptions=new Map(t.assumptions.map(e=>[e.id,e])),this.termsByOwner=new Map;for(let e of t.terminals){let n=e.enclosureId||e.boxId;this.termsByOwner.has(n)||this.termsByOwner.set(n,[]),this.termsByOwner.get(n).push(e)}this.conductorsByConduit=new Map,this.conductorsByOwner=new Map;for(let e of t.conductors){for(let n of e.conduits)this.conductorsByConduit.has(n)||this.conductorsByConduit.set(n,[]),this.conductorsByConduit.get(n).push(e);for(let n of[e.from,e.to]){let i=this.byId.get(n),s=i&&(i.enclosureId||i.boxId);s&&(this.conductorsByOwner.has(s)||this.conductorsByOwner.set(s,new Set),this.conductorsByOwner.get(s).add(e))}}this.devicesByEnclosure=new Map;for(let e of t.devices)e.enclosureId&&(this.devicesByEnclosure.has(e.enclosureId)||this.devicesByEnclosure.set(e.enclosureId,[]),this.devicesByEnclosure.get(e.enclosureId).push(e));this.pointsByCircuit=new Map;for(let e of t.points)this.pointsByCircuit.has(e.circuitId)||this.pointsByCircuit.set(e.circuitId,[]),this.pointsByCircuit.get(e.circuitId).push(e);this._frames=new Map}get(t){return this.byId.get(t)}circuit(t){return this.byId.get(t)}room(t){return this.data.rooms.find(e=>e.id===t)}roomName(t){let e=this.room(t);return e?e.name:t===null?"Outside":t}source(t){return this.sources.get(t)}frame(t){if(this._frames.has(t.id))return this._frames.get(t.id);let e=new lt;if(t.mount){let n=t.mount.normal,i=new _(n[0],0,-n[1]),s=new _(0,1,0),r=s.clone().cross(i).normalize();e.makeBasis(r,s,i).setPosition(it(t.mount.face))}else t.kind==="earth-pit"?e.makeBasis(new _(1,0,0),new _(0,0,-1),new _(0,1,0)).setPosition(it(t.position)):e.makeBasis(new _(1,0,0),new _(0,0,1),new _(0,-1,0)).setPosition(it(t.position));return this._frames.set(t.id,e),e}local(t,e){return new _(e[0],e[1],e[2]).applyMatrix4(this.frame(t))}terminalWorld(t){let e=this.byId.get(t);if(!e)return null;let n=this.byId.get(e.enclosureId||e.boxId);return this.local(n,e.local)}ownerOf(t){let e=this.byId.get(t);return e?this.byId.get(e.enclosureId||e.boxId):null}conductorsOf(t){return[...this.conductorsByOwner.get(t)||[]]}circuitOfObject(t){return t?t.circuitId?t.circuitId:t._type==="conduits"?t.circuitIds[0]||null:t._type==="enclosures"?t.circuitIds?.[0]||null:t._type==="boxes"&&t.pointId?this.get(t.pointId)?.circuitId||null:t._type==="devices"&&(t.circuitId||this.get(t.pointId)?.circuitId||this.byId.get(t.enclosureId)?.circuitIds?.[0])||null:null}colour(t){return this.data.colours[t]||this.data.colours.LIVE}roleText(t){let e=t.circuitId&&this.circuit(t.circuitId),n=e?e.phase:null;switch(t.role){case"L1":return"Phase L1 (R)";case"L2":return"Phase L2 (Y)";case"L3":return"Phase L3 (B)";case"L":return n?`Phase (live), ${n} phase`:"Phase (live)";case"SW":return"Switched live";case"REG":return"Regulated live (fan feed)";case"N":return"Neutral (return)";case"PE":return"Protective earth";default:return t.role}}endName(t){if(t==="DISCOM network")return"DISCOM network (beyond the property)";let e=this.byId.get(t),n=this.ownerOf(t);if(!e||!n)return t;let i=n.label||n.kind;return`${e.label} \xB7 ${i}`}};function jr(o){let t={devices:{},switches:{},regulators:{},faults:{},tripped:{},utility:!0};for(let e of o.devices)e.operable&&(t.devices[e.id]=e.defaultOn!==!1);for(let e of o.switches)t.switches[e.id]=!!e.defaultOn;for(let e of o.regulators||[])t.regulators[e.id]=e.defaultStep??3;return t}var Ms=class{constructor(t,e=jr(t)){this.model=t,this.state=e,this.devices=new Map(t.devices.map(n=>[n.id,n])),this.circuits=new Map(t.circuits.map(n=>[n.id,n])),this.points=new Map(t.points.map(n=>[n.id,n])),this.switches=new Map(t.switches.map(n=>[n.id,n])),this.regulators=new Map((t.regulators||[]).map(n=>[n.id,n])),this.conductors=new Map(t.conductors.map(n=>[n.id,n]))}closed(t){let e=this.devices.get(t);return e?e.operable?!!this.state.devices[t]&&!this.state.tripped[t]:!0:!1}circuitLive(t){let e=this.circuits.get(t);return!e||!this.state.utility?!1:e.chain.every(n=>this.closed(n))}switchClosed(t){return!!this.state.switches[t]}regulatorStep(t){return this.state.regulators[t]??0}pointSupplied(t){let e=this.points.get(t);if(!e||!this.circuitLive(e.circuitId))return!1;for(let n of e.controls||[])if(!this.switchControlClosed(n))return!1;return!(e.regulator&&this.regulatorStep(e.regulator)<=0)}switchControlClosed(t){return typeof t=="string"?this.switchClosed(t):t.type==="two-way"?this.switchClosed(t.a)===this.switchClosed(t.b):!1}pointOperating(t){return this.pointSupplied(t)}conductorStatus(t){let e=this.conductors.get(t);if(!e)return null;let i=(e.serves||[]).some(a=>this.pointOperating(a)),s=!1;switch(e.role){case"service":s=this.state.utility;break;case"L":case"L1":case"L2":case"L3":s=this.upstreamLive(e);break;case"SW":s=this.upstreamLive(e)&&(e.controls||[]).every(a=>this.switchControlClosed(a));break;case"REG":s=this.upstreamLive(e)&&(e.controls||[]).every(a=>this.switchControlClosed(a))&&this.regulatorStep(e.regulator)>0;break;case"STRAP":s=this.upstreamLive(e);break;case"N":case"PE":s=!1;break;default:s=!1}let r=e.role==="PE"?!1:(e.role==="N"||s)&&i;return{live:s,current:r,role:e.role}}upstreamLive(t){return this.state.utility?(t.chain||this.circuits.get(t.circuitId)?.chain||[]).every(e=>this.closed(e)):!1}toggleDevice(t){if(!this.devices.get(t)?.operable)return!1;if(this.state.tripped[t])return this.state.tripped[t]=!1,this.state.devices[t]=!1,!0;if(this.state.devices[t]=!this.state.devices[t],this.state.devices[t])for(let[n,i]of Object.entries(this.state.faults))i&&this.protects(t,n)&&(this.state.faults[n]=null);return!0}toggleSwitch(t){return this.switches.has(t)?(this.state.switches[t]=!this.state.switches[t],!0):!1}setRegulator(t,e){let n=this.regulators.get(t);return n?(this.state.regulators[t]=Math.max(0,Math.min(n.steps,Math.round(e))),!0):!1}protects(t,e){return this.circuits.get(e)?.chain.includes(t)}injectFault(t,e){let n=this.circuits.get(t);if(!n||!this.circuitLive(t))return null;let i=n.chain.map(r=>this.devices.get(r)),s=null;return e==="leakage"?s=[...i].reverse().find(r=>r.residual):(e==="overload"||e==="short")&&(s=[...i].reverse().find(r=>r.overcurrent)),s?(this.state.faults[t]=e,this.state.tripped[s.id]=!0,{circuitId:t,kind:e,device:s.id}):{circuitId:t,kind:e,device:null}}clearFault(t){this.state.faults[t]=null}snapshot(){let t={},e={},n={},i={};for(let s of this.circuits.keys())n[s]=this.circuitLive(s);for(let s of this.points.keys())t[s]=this.pointSupplied(s);for(let s of this.conductors.keys())e[s]=this.conductorStatus(s);for(let[s,r]of this.devices)i[s]={closed:this.closed(s),tripped:!!this.state.tripped[s],operable:!!r.operable};return{points:t,conductors:e,circuits:n,devices:i}}};var to=new Map,et=(o,t)=>(to.has(o)||to.set(o,t()),to.get(o)),Ia={selected:"#f0a63a",trace:"#3ec7d8",traceDim:"#2a8e9b",energised:"#f6c25b"};function B(o){switch(o){case"plate":return et(o,()=>new zt({color:"#f4f3ee",roughness:.32,clearcoat:.55,clearcoatRoughness:.25,sheen:.1}));case"module":return et(o,()=>new zt({color:"#f7f6f2",roughness:.28,clearcoat:.65,clearcoatRoughness:.2}));case"moduleRear":return et(o,()=>new j({color:"#e9e6dc",roughness:.62}));case"frame":return et(o,()=>new j({color:"#b7bcc0",metalness:.85,roughness:.42}));case"galv":return et(o,()=>new j({color:"#a9b0b4",metalness:.88,roughness:.5}));case"galvDark":return et(o,()=>new j({color:"#7f878c",metalness:.82,roughness:.55}));case"screw":return et(o,()=>new j({color:"#c8ccce",metalness:1,roughness:.32}));case"brass":return et(o,()=>new j({color:"#c6a35a",metalness:1,roughness:.34}));case"copper":return et(o,()=>new j({color:"#c47a4e",metalness:1,roughness:.3}));case"tinned":return et(o,()=>new j({color:"#c9c7bf",metalness:.95,roughness:.38}));case"conduit":return et(o,()=>new j({color:"#e6e3d9",roughness:.58}));case"conduitCut":return et(o,()=>new j({color:"#d9d4c6",roughness:.66,side:ue}));case"chase":return et(o,()=>new j({color:"#8f8a80",roughness:.95}));case"chaseEdge":return et(o,()=>new j({color:"#b9b3a6",roughness:.9}));case"concrete":return et(o,()=>new j({color:"#9b9a95",roughness:.96}));case"pvcBox":return et(o,()=>new j({color:"#d7d4c9",roughness:.7}));case"enclosure":return et(o,()=>new j({color:"#dcdad3",roughness:.48,metalness:.25}));case"enclosureInner":return et(o,()=>new j({color:"#c9c7c0",roughness:.6,metalness:.2}));case"deadFront":return et(o,()=>new j({color:"#e4e2db",roughness:.45,metalness:.2}));case"device":return et(o,()=>new zt({color:"#f1f0ea",roughness:.38,clearcoat:.3}));case"deviceGrey":return et(o,()=>new j({color:"#5d6266",roughness:.5}));case"toggle":return et(o,()=>new j({color:"#2f3336",roughness:.45}));case"toggleRed":return et(o,()=>new j({color:"#b5332a",roughness:.45}));case"dinRail":return et(o,()=>new j({color:"#c0c4c4",metalness:.9,roughness:.4}));case"meterBody":return et(o,()=>new zt({color:"#e8e8e2",roughness:.4,clearcoat:.3}));case"meterWindow":return et(o,()=>new zt({color:"#ffffff",roughness:.05,transmission:.85,thickness:.004,transparent:!0,opacity:.35}));case"lcd":return et(o,()=>new j({color:"#9fb39a",roughness:.3,emissive:"#1d2a1c",emissiveIntensity:.4}));case"seal":return et(o,()=>new j({color:"#b2342a",roughness:.5}));case"fanBody":return et(o,()=>new zt({color:"#e9e7e0",roughness:.35,metalness:.25,clearcoat:.4}));case"fanBlade":return et(o,()=>new j({color:"#dedbd2",roughness:.4,metalness:.35}));case"downrod":return et(o,()=>new j({color:"#d9d7d0",roughness:.3,metalness:.6}));case"hook":return et(o,()=>new j({color:"#6c6f70",metalness:.9,roughness:.45}));case"connector":return et(o,()=>new j({color:"#f0eee6",roughness:.55}));case"rubber":return et(o,()=>new j({color:"#2a2b2c",roughness:.8}));case"pit":return et(o,()=>new j({color:"#8d8b84",roughness:.92}));case"pitCover":return et(o,()=>new j({color:"#5b5e5f",metalness:.7,roughness:.55}));case"lensOn":return et(o,()=>new j({color:"#fff4dc",emissive:"#ffd59a",emissiveIntensity:2.4,roughness:.3}));case"lensOff":return et(o,()=>new j({color:"#d9d8d2",roughness:.35,metalness:.05}));case"exhaust":return et(o,()=>new j({color:"#efede6",roughness:.5}));default:throw Error("Unknown material "+o)}}function en(o){return et("ins:"+o,()=>new zt({color:o,roughness:.42,clearcoat:.25,clearcoatRoughness:.4}))}function Ss(o,t){return et(`stripe:${o}:${t}`,()=>{let e=document.createElement("canvas");e.width=64,e.height=64;let n=e.getContext("2d");n.fillStyle=o,n.fillRect(0,0,64,64),n.fillStyle=t;for(let s=-64;s<128;s+=22)n.beginPath(),n.moveTo(s,0),n.lineTo(s+11,0),n.lineTo(s+11-64,64),n.lineTo(s-64,64),n.fill();let i=new Rn(e);return i.colorSpace=Bt,i.wrapS=i.wrapT=_e,i.repeat.set(1,40),new zt({map:i,roughness:.42,clearcoat:.25})})}function eo(o,t,e,n){return et("tex:"+n,()=>{let i=document.createElement("canvas");i.width=o,i.height=t,e(i.getContext("2d"),o,t);let s=new Rn(i);return s.colorSpace=Bt,s.anisotropy=4,s})}function ie(o,t,e,n,i={}){return et("pm:"+o,()=>new j({map:eo(t,e,n,o),roughness:.45,...i}))}var Pa=.0225,La=.045;function nn(o,t,e,n){let i=o.clone();return i.translate(t,e,n),i}function bs(o,t=.002){let e=new ae(o,20);return e.translate(0,0,t),e}function Da(o,t,e){let n=new rt;n.name=t.id,o.frame(t).decompose(n.position,n.quaternion,n.scale);let s=t.size.w,r=t.size.h,a=t.size.plateDepth||.0065,l=t.plateModules<=8?t.plateModules:6,c=t.plateModules<=8?1:2,u=l*Pa+.003,d=c*La+(c-1)*0+.003,h=new rt;h.name="assembly",n.add(h);let f=new D(Oe(s,r,u,d,a,.002),B("plate"));f.userData={kind:"plate",ref:t.id},h.add(f);let p=new D(tn(s,r,.0012,.006,6e-4),B("plate"));h.add(p);let m=new D(new Rt(u,d),B("frame"));m.position.z=5e-4,h.add(m);let x=[],v=[],S={group:n,assembly:h,plate:f,rockers:new Map,knobs:new Map,modules:[]};for(let y of t.modules){let A=y.span*Pa-8e-4,b=La-8e-4,R=y.x,T=y.y,I=new ot(A,b,.004);if(x.push(nn(I,R,T,a-.002)),y.kind==="switch"||y.kind==="switch16"){let C=new D(new ot(.0148,.031,.0042),B("module"));C.position.set(R,T,a+.0018),C.userData={kind:"switch",ref:y.switchId,enclosure:t.id};let P=new D(new Rt(.004,.0016),B("toggleRed"));P.position.set(0,-.0115,.0022),C.add(P),h.add(C),S.rockers.set(y.switchId,C),e.push(C)}else if(y.kind==="socket6"||y.kind==="socket16"){let C=y.kind==="socket16",P=C?.0254:.0191,k=C?.0259:.02,w=C?.004:.003,U=C?.0045:.0037,L=new Tt(.019,.019,.0015,32);L.rotateX(Math.PI/2),x.push(nn(L,R,T,a+6e-4)),v.push(nn(bs(w),R-P/2,T-k/3,a+2e-4+.0015)),v.push(nn(bs(w),R+P/2,T-k/3,a+2e-4+.0015)),v.push(nn(bs(U),R,T+k*2/3,a+2e-4+.0015));let V=new D(new ot(A,b,.006),B("module"));V.position.set(R,T,a),V.visible=!1,V.userData={kind:"device",ref:y.deviceId,enclosure:t.id,proxy:!0},h.add(V),e.push(V)}else if(y.kind==="regulator"){let C=new D(new Tt(.0125,.0135,.011,32),B("module"));C.rotation.x=Math.PI/2,C.position.set(R,T,a+.0055),C.userData={kind:"regulator",ref:y.regulatorId,enclosure:t.id};let P=new D(new ot(.0018,.0015,.007),B("toggle"));P.position.set(0,.0056,-.0055),P.rotation.x=-Math.PI/2,C.add(P),h.add(C),S.knobs.set(y.regulatorId,C),e.push(C);for(let k=0;k<6;k++){let w=Math.PI*(1.25-k*.3);v.push(nn(bs(7e-4),R+Math.cos(w)*.0175,T+Math.sin(w)*.0175,a+1e-4))}}else if(y.kind==="mcb"){let C=new ot(.014,.03,.0015);v.push(nn(C,R,T,a+8e-4));let P=new D(new ot(.008,.012,.006),B("toggle"));P.position.set(R,T+.004,a+.003),P.userData={kind:"switch",ref:y.switchId,enclosure:t.id,mcb:!0},h.add(P),S.rockers.set(y.switchId,P),e.push(P)}S.modules.push(y)}if(x.length){let y=di(x.map(A=>A.toNonIndexed?A.toNonIndexed():A)),M=new D(y,B("module"));M.userData={kind:"plate",ref:t.id},h.add(M),e.push(M)}if(v.length){let y=di(v.map(M=>M.toNonIndexed?M.toNonIndexed():M));h.add(new D(y,B("toggle")))}return e.push(f),h.traverse(y=>{y.isMesh&&(y.castShadow=!1,y.receiveShadow=!0)}),S}function Na(o,t,e=!1){var n;if(e){o.position.y=(n=o.userData).baseY??(n.baseY=o.position.y),o.position.y=o.userData.baseY+(t?.004:-.004);return}o.rotation.x=t?-.13:.13}function Ua(o,t,e,{danger:n=!0}={}){let i=new rt;i.name=t.id,o.frame(t).decompose(i.position,i.quaternion,i.scale);let s=t.size.w,r=t.size.h,a=t.size.depth,l=new D(Oe(s+.024,r+.024,s-.02,r-.02,.006,.002),B("enclosure"));l.userData={kind:"enclosure",ref:t.id},i.add(l),e.push(l);let c=new rt;c.name="doors";let u=(s-.022)/2,d=p=>{let m=new rt;m.position.set(p*(s-.022)/2,0,.006);let x=new D(tn(u-.002,r-.022,.016,.003,.0015),B("enclosure"));if(x.position.set(-p*u/2,0,0),x.userData={kind:"enclosure",ref:t.id,door:!0},m.add(x),e.push(x),p<0){let v=new D(new ot(.012,.05,.01),B("deviceGrey"));v.position.set(u-.016,0,.019),x.add(v)}return c.add(m),m},h=d(-1),f=d(1);if(i.add(c),n&&t.kind!=="loose-wire-box"){let p=new D(new Rt(.075,.05),ie("danger-plate",300,200,(m,x,v)=>{m.fillStyle="#f4f1e8",m.fillRect(0,0,x,v),m.fillStyle="#b4271f",m.fillRect(0,0,x,54),m.fillStyle="#fff",m.font="bold 40px system-ui, sans-serif",m.textAlign="center",m.fillText("DANGER",x/2,42),m.fillStyle="#1d1d1d",m.font="bold 44px system-ui, sans-serif",m.fillText("400 V",x/2,118),m.font="24px system-ui, sans-serif",m.fillText("CEA Reg. 20 notice",x/2,168)}));h.children[0].add(p),p.position.set(0,r/2-.07,.0165)}if(t.kind==="loose-wire-box"){c.visible=!1;let p=new D(tn(s-.02,r-.02,.01,.003,.0012),B("enclosure"));p.position.z=.006,p.userData={kind:"enclosure",ref:t.id},i.add(p),e.push(p);for(let m of[-1,1])for(let x of[-1,1]){let v=new D(new Tt(.003,.003,.002,12),B("screw"));v.rotation.x=Math.PI/2,v.position.set(m*(s/2-.025),x*(r/2-.022),.0165),i.add(v)}return{group:i,doors:null,cover:p,left:null,right:null}}return{group:i,doors:c,left:h,right:f,cover:null}}function Fa(o,t,e){let n=new rt;n.name=t.id,o.frame(t).decompose(n.position,n.quaternion,n.scale);let i=t.size.w,s=t.size.h,r=t.size.surface||.2,a=new D(tn(i,s,r,.012,.004),B("meterBody"));a.userData={kind:"enclosure",ref:t.id},n.add(a),e.push(a);let l=new rt;l.position.set(0,.02,r-.03);let c=new D(tn(.191,.255,.02,.008,.003),B("device"));c.position.z=-.02,l.add(c);let u=new D(new Rt(.085,.028),ie("meter-lcd",340,112,(m,x,v)=>{m.fillStyle="#9db398",m.fillRect(0,0,x,v),m.fillStyle="#1e2a1d",m.font="bold 56px ui-monospace, monospace",m.textAlign="right",m.fillText("00427.6",x-52,74),m.font="bold 26px system-ui",m.fillText("kWh",x-6,74),m.font="20px system-ui",m.textAlign="left",m.fillText("3\xD8 4W",8,102)}));u.position.set(0,.06,.0015),l.add(u);let d=new D(new ae(.0028,16),new j({color:"#ff5b45",emissive:"#ff3b25",emissiveIntensity:0}));d.position.set(.06,.025,.0015),l.add(d);let h=new D(new ot(.18,.055,.01),B("device"));h.position.set(0,-.095,.004),l.add(h);for(let m of[-.07,.07]){let x=new D(new Ln(.004,12,8),B("seal"));x.position.set(m,-.122,.012),l.add(x)}n.add(l);let f=new D(new Rt(.2,.14),new zt({color:"#dfe9ee",roughness:.05,transparent:!0,opacity:.22,depthWrite:!1}));f.position.set(0,.07,r+5e-4),n.add(f);let p=new D(new Rt(.12,.03),ie("meter-label",480,120,(m,x,v)=>{m.fillStyle="#f7f6f0",m.fillRect(0,0,x,v),m.fillStyle="#25302c",m.font="bold 40px system-ui",m.textAlign="center",m.fillText("DISCOM METER",x/2,52),m.font="30px system-ui",m.fillText("Sealed \xB7 licensee only",x/2,100)}));return p.position.set(0,-.13,r+6e-4),n.add(p),{group:n,led:d}}function Ba(o,t,e,n){let i=new rt;i.name=t.id;let s=(t.sweep||1200)/1e3,r=e.position[2],a=t.floor*o.data.floorHeight+2.69;i.position.copy(it([t.position[0],t.position[1],r]));let l=r-a,c=new D(new Tt(.045,.062,.12,32,1,!0),B("fanBody"));c.position.y=-.06,c.userData={kind:"fan-canopy",ref:t.id};let u=new D(new ae(.062,32),B("fanBody"));u.rotation.x=Math.PI/2,u.position.y=-.12;let d=new rt;d.add(c,u),i.add(d),n.push(c);let h=l-.07,f=new D(new Tt(.0105,.0105,h,16),B("downrod"));f.position.y=-h/2-0,i.add(f);let p=new rt;p.position.y=-l;let m=new D(new Tt(.105,.095,.085,40),B("fanBody"));m.userData={kind:"point",ref:t.id},p.add(m);let x=new D(new Ln(.095,32,12,0,Math.PI*2,Math.PI/2,Math.PI/2),B("fanBody"));x.scale.y=.35,x.position.y=-.042,p.add(x),n.push(m);let v=s/2-.1;for(let S=0;S<3;S++){let y=new rt;y.rotation.y=S*Math.PI*2/3;let M=new ye;M.moveTo(0,-.03),M.lineTo(v*.3,-.05),M.quadraticCurveTo(v,-.06,v,0),M.quadraticCurveTo(v,.055,v*.3,.05),M.lineTo(0,.03),M.lineTo(0,-.03);let A=new De(M,{depth:.0025,bevelEnabled:!1});A.rotateX(Math.PI/2);let b=new D(A,B("fanBlade"));b.position.set(.1,0,0),b.rotation.x=.08,b.userData={kind:"point",ref:t.id},y.add(b),n.push(b),p.add(y)}return i.add(p),i.traverse(S=>{S.isMesh&&(S.castShadow=!1,S.receiveShadow=!0)}),{group:i,rotor:p,canopyGroup:d,drop:l}}function Oa(o,t,e){let n=new rt;n.name=t.id;let s=o.get(t.boxId).mount.normal,r=t.position,a=new _(s[0],0,-s[1]),l=new _(0,1,0),c=l.clone().cross(a).normalize();n.matrixAutoUpdate=!0,new lt().makeBasis(c,l,a).setPosition(it([r[0]+s[0]*.002,r[1]+s[1]*.002,r[2]])).decompose(n.position,n.quaternion,n.scale);let d=t.size||.3,h=new D(Oe(d,d,d-.05,d-.05,.025,.006),B("exhaust"));h.userData={kind:"point",ref:t.id},n.add(h),e.push(h);let f=new rt;for(let x=0;x<9;x++){let v=new D(new ot(d-.06,.004,.004),B("exhaust"));v.position.set(0,-d/2+.04+x*(d-.08)/8,.02),f.add(v)}n.add(f);let p=new rt;p.position.z=.006;for(let x=0;x<5;x++){let v=new D(new ot(.1,.035,.002),B("fanBlade"));v.position.x=.055;let S=new rt;S.rotation.z=x*Math.PI*2/5,S.add(v),p.add(S)}n.add(p);let m=new D(new ae((d-.05)/2,32),B("rubber"));return m.position.z=.001,n.add(m),{group:n,hub:p}}function ka(o,t,e){let n=new rt;o.frame(t).decompose(n.position,n.quaternion,n.scale);let i=new rt;n.add(i);let s=new D(tn(.086,.086,.0065,.006,.0012),B("plate"));s.userData={kind:"box",ref:t.id},i.add(s),e.push(s);let r=new D(new Ne(.005,.0018,8,20),B("rubber"));return r.position.set(0,-.02,.0068),i.add(r),{group:n,assembly:i}}function za(o,t,e){let n=new rt;n.position.copy(it(t.position));let i=new D(Oe(.36,.36,.3,.3,.02,.002),B("pit"));i.rotation.x=-Math.PI/2,i.position.y=-.014;let s=new D(new ot(.296,.012,.296),ie("pit-cover",256,256,(r,a,l)=>{r.fillStyle="#4e5355",r.fillRect(0,0,a,l),r.strokeStyle="#626869",r.lineWidth=6;for(let c=20;c<a;c+=28)r.beginPath(),r.moveTo(c,10),r.lineTo(c,l-10),r.stroke();r.fillStyle="#d7d2c4",r.font="bold 34px system-ui",r.textAlign="center",r.fillText("EARTH",a/2,l/2+12)},{metalness:.6,roughness:.55}));return s.position.y=-.0035,s.userData={kind:"box",ref:t.id},n.add(i,s),e.push(s),{group:n}}function Ha(o,t,e){let n=e.filter(d=>d.kind==="downlight"&&d.lens),i=new Tt(1,1,8e-4,28),s=new An(i,B("lensOn"),n.length),r=new An(i,B("lensOff"),n.length),a=new Map,l=new lt,c=new kt,u=new _;return n.forEach((d,h)=>{let f=it([d.lens.xy[0],d.lens.xy[1],d.lens.bottom-6e-4]),p=d.lens.r+.0012;l.compose(f,c,u.set(p,1,p)),s.setMatrixAt(h,l),r.setMatrixAt(h,l),a.set(d.id,h)}),s.frustumCulled=r.frustumCulled=!1,s.userData={kind:"light-caps"},{on:s,off:r,index:a,downs:n}}var Va=.0225,Ga=.045,Wa=.018,rn=o=>new _(o[0],o[1],o[2]);function no(o){return o==null?.0027:{1.5:.0015,2.5:.0017,4:.0021,6:.0024,10:.0031}[o]||.0018}function yd(o,t){let e=o.colour(t.colour);return t.colour==="PE"?Ss(e.hex,e.stripe):en(e.hex)}function Es(o,t,e,{bareEnd:n=!0,bareStart:i=!1,radius:s}={}){let r=s??no(t.size),a=new rt,l=new Le(e,!1,"centripetal",.5),c=Math.max(16,Math.round(l.getLength()/.004)),u=l.getSpacedPoints(c),d=.011,h=l.getLength(),f=i?Math.min(.45,d/h):0,p=n?Math.max(.55,1-d/h):1,m=u.filter((S,y)=>y/c>=f&&y/c<=p),x=ne(m.length>1?m:u,r,8,{caps:!0}),v=new D(x,yd(o,t));if(v.userData={kind:"conductor",ref:t.id},a.add(v),n){let S=u.filter((y,M)=>M/c>=p-.001);S.length>1&&a.add(new D(ne(S,r*.55,6),B("copper")))}if(i){let S=u.filter((y,M)=>M/c<=f+.001);S.length>1&&a.add(new D(ne(S,r*.55,6),B("copper")))}return a.userData={kind:"conductor",ref:t.id},{group:a,mesh:v}}function sn(o=.0026){let t=new D(new Tt(o,o,.0016,14),B("screw"));t.rotation.x=Math.PI/2;let e=new D(new ot(o*1.6,o*.35,6e-4),B("galvDark"));return e.position.y=9e-4,e.rotation.x=-Math.PI/2,t.add(e),t}function ws(o,t,e){let n=new Map;for(let i of t.conduitIds||[]){let s=o.get(i),r=s.points,a=s.from===t.id,l=a?r[0]:r[r.length-1],c=a?r[1]:r[r.length-2],u=it(l).applyMatrix4(e),d=it(c).applyMatrix4(e),h=u.clone().sub(d).normalize();n.set(i,{pos:u,dir:h,conduit:s})}return n}function Ts(o,t,e){if(t<=1)return new O;let n=o/t*Math.PI*2+.4;return new O(Math.cos(n)*e,Math.sin(n)*e)}function As(o){let e=(Math.abs(o.y)>.9?new _(1,0,0):new _(0,1,0)).clone().cross(o).normalize(),n=o.clone().cross(e).normalize();return[e,n]}function Xa(o,t,e){let{model:n}=o,i=new rt;i.name="interior:"+t.id,e.group.add(i);let s=n.frame(t).clone().invert(),r=t.size.boxW,a=t.size.boxH,l=t.size.depth,c=new D(ys(r,a,l,.0012),B("galv"));c.userData={kind:"enclosure",ref:t.id},i.add(c),o.pickables.push(c);let u=ws(n,t,s);for(let[E,N]of u){let H=N.conduit,$=(H.diameter||20)/2e3,ut=N.pos.clone().addScaledVector(N.dir,-.06),_t=N.pos.clone().addScaledVector(N.dir,.004),Ct=new D(ne([ut,_t],$,18),B("conduit"));Ct.userData={kind:"conduit",ref:E},i.add(Ct),o.pickables.push(Ct);let Mt=new D(new Ne($*.93,$*.16,8,24),B("rubber"));Mt.position.copy(_t),Mt.lookAt(_t.clone().add(N.dir)),i.add(Mt);let bt=new D(new ae($*.82,20),B("rubber"));bt.position.copy(_t.clone().addScaledVector(N.dir,-.001)),bt.lookAt(_t.clone().add(N.dir)),i.add(bt)}let d=[],h=new Map,f=new Set(Object.values(t.connectors||{})),p={P:ie("blk-P",32,32,E=>{E.fillStyle="#c23b2f",E.fillRect(0,0,32,32)}),N:ie("blk-N",32,32,E=>{E.fillStyle="#222",E.fillRect(0,0,32,32)}),E:ie("blk-E",32,32,E=>{E.fillStyle="#3f9442",E.fillRect(0,0,32,32),E.fillStyle="#d6c52a",E.fillRect(0,12,32,8)})};for(let[E,N]of Object.entries(t.connectors||{})){let H=n.get(N),$=rn(H.local);if(E==="stud"){let Mt=sn(.0032);Mt.position.copy($),Mt.userData={kind:"terminal",ref:N},i.add(Mt),o.pickables.push(Mt);let bt=new D(new Tt(.0048,.0048,6e-4,16),B("screw"));bt.rotation.x=Math.PI/2,bt.position.copy($).add(new _(0,0,-.0011)),i.add(bt),h.set(N,{pos:$.clone().add(new _(0,0,.002)),dir:new _(0,0,1)}),d.push({local:$.clone(),text:"Box earth stud",ref:N});continue}let ut=new D(new ot(.014,.016,.012),B("connector"));ut.position.copy($).add(new _(0,0,-.004)),ut.userData={kind:"terminal",ref:N},i.add(ut),o.pickables.push(ut);let _t=new D(new Rt(.012,.0035),p[E]);_t.position.set(0,-.0062,.0061),ut.add(_t);let Ct=sn(.0024);Ct.position.set(0,.002,.0062),ut.add(Ct),h.set(N,{pos:$.clone().add(new _(0,-.003,.002)),dir:new _(0,0,1)}),d.push({local:$.clone(),text:{P:"Phase connector",N:"Neutral connector",E:"Earth connector"}[E],ref:N})}let m=e.assembly,x=new rt;m.add(x);for(let E of t.modules){if(E.kind==="blank")continue;let N=E.span,H=E.kind==="regulator"?.056:.036,$=new D(new ot(N*Va-.0012,Ga-.0012,H),B("moduleRear"));$.position.set(E.x,E.y,-H/2),$.userData={kind:"device",ref:E.deviceId},x.add($),o.pickables.push($)}let v=new D(Oe(r-.004,a-.004,Math.min(r-.02,(t.plateModules<=8?t.plateModules:6)*Va+.004),Math.min(a-.02,(t.plateModules<=8?1:2)*Ga+.004),.0015,.001),B("frame"));v.position.z=-.0015,x.add(v);for(let E of[-1,1]){let N=sn(.0026);N.position.set(E*(r/2-.009),0,-5e-4),N.userData={kind:"enclosure",ref:t.id},x.add(N)}for(let E of n.termsByOwner.get(t.id)||[]){if(f.has(E.id))continue;let N=rn(E.local),H=sn(.0021);H.position.copy(N).add(new _(0,0,-.0035)),H.rotation.x=-Math.PI/2,H.userData={kind:"terminal",ref:E.id},x.add(H),o.pickables.push(H),h.set(E.id,{pos:N.clone().add(new _(0,0,-.006)),dir:new _(0,0,-1),moving:!0})}let S=t.modules.filter(E=>E.kind!=="blank"),y=E=>S.find(N=>E.includes(N.kind)),M=y(["switch","switch16"]),A=y(["regulator"]),b=y(["socket6","socket16"]),R=y(["mcb"]),T=d.filter(E=>/connector$/.test(E.text)),I=d.find(E=>E.text==="Box earth stud");if(d.length=0,u.size){let E=[...u.values()][0];d.push({local:E.pos.clone(),text:u.size>1?`${u.size} conduit entries (circuit in, loop out, point wiring)`:"Conduit entry",ref:[...u.keys()][0]})}T.length&&d.push({local:T[0].local.clone().add(new _(.02,0,0)),text:"Phase \xB7 neutral \xB7 earth connector blocks (CPWD 3.5.6)",ref:T[0].ref}),M&&d.push({local:new _(M.x,M.y,-.02),text:S.filter(E=>E.kind.startsWith("switch")).length>1?"Switches: live in \u2192 switched live out":"Switch: live in \u2192 switched live out",ref:M.deviceId,moving:!0}),A&&d.push({local:new _(A.x,A.y,-.03),text:"Fan regulator in series after its switch",ref:A.deviceId,moving:!0}),b&&d.push({local:new _(b.x,b.y,-.02),text:"Socket: L, N and earth terminals",ref:b.deviceId,moving:!0}),R&&d.push({local:new _(R.x,R.y,-.02),text:"Local 16 A MCB (water heater)",ref:R.deviceId,moving:!0}),I&&d.push(I);let C=[],P=new rt;i.add(P);let k=Rs(n,t),w=new Map,U=new Map;for(let E of k)for(let N of[E.a,E.b])N.mouth&&w.set(N.mouth,(w.get(N.mouth)||0)+1);function L(E,N){if(E.mouth){let $=u.get(E.mouth),ut=w.get(E.mouth)||1,_t=U.get(E.mouth+N.id)??(U.set(E.mouth+N.id,U.get(E.mouth+"#")||0),U.set(E.mouth+"#",(U.get(E.mouth+"#")||0)+1),U.get(E.mouth+N.id)),[Ct,Mt]=As($.dir),bt=Ts(_t,ut,($.conduit.diameter||20)/2e3*.5);return{pos:$.pos.clone().addScaledVector(Ct,bt.x).addScaledVector(Mt,bt.y),dir:$.dir.clone(),moving:!1}}let H=h.get(E.terminal);return H?{...H,pos:H.pos.clone(),dir:H.dir.clone()}:null}for(let E of k){let N=L(E.a,E.k),H=L(E.b,E.k);!N||!H||C.push({k:E.k,a:N,b:H,mesh:null,aT:E.a.terminal,bT:E.b.terminal})}let V=()=>{m.updateMatrix();for(let E of C){if(E.mesh){P.remove(E.mesh),E.mesh.traverse(He=>He.geometry?.dispose());let Ut=o.pickables.indexOf(E.pick);Ut>=0&&o.pickables.splice(Ut,1)}let N=E.a.moving?E.a.pos.clone().applyMatrix4(m.matrix):E.a.pos,H=E.b.moving?E.b.pos.clone().applyMatrix4(m.matrix):E.b.pos,$=E.a.moving?E.a.dir.clone().transformDirection(m.matrix):E.a.dir,ut=E.b.moving?E.b.dir.clone().transformDirection(m.matrix):E.b.dir,_t=-l+.01+C.indexOf(E)%5*.003,Ct=(C.indexOf(E)%9-4)*.006,Mt=[N,N.clone().addScaledVector($,.012)],bt=E.a.moving||E.b.moving;if(E.a.moving||Mt.push(new _(N.x+Ct*.5,Math.max(Math.min(N.y,H.y),-a/2+.02)*.6,_t)),bt){let Ut=E.b.moving?H:N;Mt.push(new _((Ut.x+(E.b.moving?N.x:H.x))/2+Ct,-a/2+.006,.02))}else Mt.push(new _((N.x+H.x)/2+Ct,(N.y+H.y)/2-.012,_t+.006));E.b.moving||Mt.push(new _(H.x+Ct*.5,H.y+.012,_t)),Mt.push(H.clone().addScaledVector(ut,.012),H),E.b.moving&&E.a.moving;let Et=Es(o.model,E.k,Mt,{bareEnd:!!E.bT,bareStart:!!E.aT});E.mesh=Et.group,P.add(E.mesh),E.pick=Et.mesh,o.pickables.push(Et.mesh)}};V();let X=t.size.w,J=0;return{enc:t,group:i,wires:C,callouts:d,kind:"box",set(E){J=Math.max(0,Math.min(1,E));let N=J*J*(3-2*J),H=Math.min(1,N/.35),$=Math.max(0,(N-.35)/.65),ut=$*1.35;m.position.set(-X/2*(1-Math.cos(ut))-$*.05,-$*.03,.012+H*.11+Math.sin(ut)*X/2),m.rotation.y=-ut,V()},anchor(E){let N=E.local.clone();return E.moving&&(m.updateMatrix(),N.applyMatrix4(m.matrix)),N.applyMatrix4(e.group.matrixWorld)},dispose(){e.group.remove(i),m.remove(x),i.traverse(E=>E.geometry?.dispose()),x.traverse(E=>E.geometry?.dispose()),m.position.set(0,0,0),m.rotation.set(0,0,0)}}}function Rs(o,t){let e=[],n=s=>{let r=o.get(s);return r&&(r.enclosureId===t.id||r.boxId===t.id)},i=new Set(o.conductorsOf(t.id));for(let s of t.conduitIds||[])for(let r of o.conductorsByConduit.get(s)||[])i.add(r);for(let s of i){let r=n(s.from),a=n(s.to);if(r&&a){e.push({k:s,a:{terminal:s.from},b:{terminal:s.to}});continue}if(r&&s.conduits.length){e.push({k:s,a:{terminal:s.from},b:{mouth:s.conduits[0]}});continue}if(a&&s.conduits.length){e.push({k:s,a:{mouth:s.conduits[s.conduits.length-1]},b:{terminal:s.to}});continue}for(let l=0;l<s.conduits.length-1;l++){let c=o.get(s.conduits[l]),u=o.get(s.conduits[l+1]);[c.from,c.to].find(h=>h===u.from||h===u.to)===t.id&&e.push({k:s,a:{mouth:c.id},b:{mouth:u.id}})}}return e}function $a(o,t,e,n,i){let{model:s}=o,r=new rt;r.name="interior:"+t.id,e.group.add(r);let a=t.size.w,l=t.size.h,c=t.size.depth,u=new D(ys(a-.004,l-.004,c,.0015),B("enclosureInner"));u.userData={kind:"enclosure",ref:t.id},r.add(u),o.pickables.push(u);let d=[],h=s.devicesByEnclosure.get(t.id)||[],f=new Map,p=new Set(h.filter(w=>w.y!=null&&["mcb","mcb4p","rccb4p","isolator2p"].includes(w.kind)).map(w=>w.y));for(let w of p){let U=new D(new ot(a-.05,.035,.0075),B("dinRail"));U.position.set(0,w,-c+.012),r.add(U)}let m=-.006;for(let w of h)if(["mcb","mcb4p","rccb4p","isolator2p"].includes(w.kind)){let U=w.modules*Wa-6e-4,L=new rt;L.position.set(w.x,w.y,0);let V=new D(new ot(U,.081,.044),B("device"));V.position.z=-c+.016+.022;let X=new D(new ot(U,.045,c-.016-.044+m),B("device"));X.position.z=(-c+.016+.044+m)/2,V.userData=X.userData={kind:"device",ref:w.id},L.add(V,X),o.pickables.push(V,X);let J=new D(new ot(Math.min(U-.004,.012*(w.poles>1?2.6:1)),.014,.008),B(w.kind==="rccb4p"?"toggleRed":"toggle"));if(J.position.set(0,.006,m+.002),J.userData={kind:"device",ref:w.id,toggle:!0},L.add(J),o.pickables.push(J),w._toggle=J,w.kind==="rccb4p"){let E=new D(new Tt(.0035,.0035,.004,12),B("deviceGrey"));E.rotation.x=Math.PI/2,E.position.set(U/2-.01,-.014,m+.001),L.add(E)}let K=new D(new Rt(U-.002,.01),ie("lbl:"+w.id,128,40,(E,N,H)=>{E.fillStyle="#f2f1ea",E.fillRect(0,0,N,H),E.fillStyle="#26302c",E.font=`bold ${w.kind==="mcb"?26:22}px system-ui`,E.textAlign="center",E.fillText(w.kind==="mcb"?w.circuitId:w.kind==="rccb4p"?"RCCB 30mA":w.kind==="mcb4p"?"MAIN":"ISOL",N/2,29)}));if(K.position.set(0,-.016,m+5e-4),L.add(K),w.phase){let E=new D(new Rt(.006,.003),en(s.colour(w.phase).hex));E.position.set(0,.019,m+5e-4),L.add(E)}r.add(L);for(let[E,N]of Object.entries(w.terminals||{})){let H=s.get(N),$=rn(H.local),ut=sn(.0022);ut.position.set($.x,$.y+($.y>w.y?-.004:.004),m+4e-4),r.add(ut),f.set(N,{pos:$.clone(),dir:new _(0,Math.sign($.y-w.y)||1,0)})}w.kind==="mcb4p"&&d.push({local:new _(w.x,w.y,m),text:"Incoming 4-pole MCB (main switch)",ref:w.id}),w.kind==="rccb4p"&&d.push({local:new _(w.x,w.y,m),text:"RCCB 4-pole, 30 mA, Type A",ref:w.id}),w.kind==="isolator2p"&&d.push({local:new _(w.x,w.y,m),text:"Incoming 2-pole isolator",ref:w.id})}else if(w.kind==="neutral-bar"||w.kind==="earth-bar"){let U=Object.keys(w.terminals||{}).length,L=Math.max(.07,U*.01+.02),V=new D(new ot(L,.009,.007),B(w.kind==="neutral-bar"?"brass":"tinned")),X=Math.min(...Object.values(w.terminals||{}).map(E=>s.get(E).local[0]).concat([w.x]))-.012;V.position.set(X+L/2,w.y,-c+.03),V.userData={kind:"device",ref:w.id},r.add(V),o.pickables.push(V);for(let E of[X+.004,X+L-.004]){let N=new D(new Tt(.004,.004,.02,12),B(w.kind==="neutral-bar"?"rubber":"galvDark"));N.rotation.x=Math.PI/2,N.position.set(E,w.y,-c+.015),r.add(N)}let J=w.kind==="neutral-bar"?ie("tag-N",64,32,E=>{E.fillStyle="#2a2a2a",E.fillRect(0,0,64,32),E.fillStyle="#fff",E.font="bold 24px system-ui",E.fillText("N",24,25)}):ie("tag-PE",64,32,E=>{E.fillStyle="#3f9442",E.fillRect(0,0,64,32),E.fillStyle="#d6c52a",E.fillRect(0,10,64,12),E.fillStyle="#111",E.font="bold 20px system-ui",E.fillText("PE",18,23)}),K=new D(new Rt(.016,.008),J);K.position.set(X-.012,w.y,-c+.035),r.add(K);for(let E of Object.values(w.terminals||{})){let N=s.get(E),H=sn(.0019);H.position.set(N.local[0],w.y,-c+.034),r.add(H),f.set(E,{pos:new _(N.local[0],w.y-.006,-c+.03),dir:new _(0,-1,.3).normalize()})}d.push({local:new _(X+L/2,w.y,-c+.03),text:w.label,ref:w.id})}else if(w.kind==="busbar"){let U=Object.values(w.terminals||{}),L=h.filter(H=>H.kind==="mcb");if(!L.length)continue;let V=L.map(H=>H.x),X=L[0].y+.034,J=Math.max(...V)-Math.min(...V)+Wa+.02,K=(Math.max(...V)+Math.min(...V))/2,E=new D(new ot(J,.006,.012),B("copper"));E.position.set(K,X+.006,-c+.05),E.userData={kind:"device",ref:w.id};let N=new D(new ot(J+.004,.01,.016),new j({color:"#5d6467",roughness:.5,transparent:!0,opacity:.45}));N.position.copy(E.position),N.userData={kind:"device",ref:w.id},r.add(E,N),o.pickables.push(E,N);for(let H of L){let $=new D(new ot(.004,.012,.006),B("copper"));$.position.set(H.x,X,-c+.05),r.add($);let ut=new D(new ot(.006,.003,.0162),en(s.colour(H.phase).hex));ut.position.set(H.x,X+.011,-c+.05),r.add(ut)}for(let H of U)f.set(H,{pos:rn(s.get(H).local),dir:new _(-1,0,0)});d.push({local:new _(K,X+.006,-c+.05),text:w.label,ref:w.id})}let x=h.filter(w=>w.kind==="mcb");x.length&&d.push({local:new _(x[Math.floor(x.length/2)].x,x[0].y,m),text:`Outgoing MCBs (${x.length} ways)`,ref:x[0].id});let v=new D(Oe(a-.012,l-.012,a-.06,.16,.0015,.002),B("deadFront"));v.position.z=m-2e-4,r.add(v);let S=s.frame(t).clone().invert(),y=ws(s,t,S);for(let[w,U]of y){let L=U.conduit,V=(L.diameter||20)/2e3,X=new D(ne([U.pos.clone().addScaledVector(U.dir,-.07),U.pos.clone().addScaledVector(U.dir,.005)],V,18),B(L.function==="service"?"galvDark":"conduit"));X.userData={kind:"conduit",ref:w},r.add(X),o.pickables.push(X)}let M=new rt;r.add(M);let A=new Map,b=Rs(s,t).filter(w=>w.k.kind!=="busbar");b.forEach(w=>{for(let U of[w.a,w.b])U.mouth&&A.set(U.mouth,(A.get(U.mouth)||0)+1)});let R=new Map,T=(w,U)=>{if(w.terminal)return f.get(w.terminal)||{pos:rn(s.get(w.terminal).local),dir:new _(0,0,1)};let L=y.get(w.mouth),V=R.get(w.mouth)||0;R.set(w.mouth,V+1);let[X,J]=As(L.dir),K=Ts(V,A.get(w.mouth)||1,(L.conduit.diameter||20)/2e3*.55);return{pos:L.pos.clone().addScaledVector(X,K.x).addScaledVector(J,K.y),dir:L.dir.clone()}},I=a/2-.028,C=[];for(let w of b){let U=T(w.a,w.k),L=T(w.b,w.k);if(!U||!L)continue;let V=-c+.022,X=(U.pos.x+L.pos.x)/2>0?I:-I,J=[U.pos,U.pos.clone().addScaledVector(U.dir,.014)];Math.abs(U.pos.y-L.pos.y)>.05?(J.push(new _(X-Math.sign(X)*(C.length%6)*.0035,U.pos.y+U.dir.y*.02,V)),J.push(new _(X-Math.sign(X)*(C.length%6)*.0035,L.pos.y+L.dir.y*.02,V))):J.push(U.pos.clone().add(L.pos).multiplyScalar(.5).add(new _(0,.012,-.004))),J.push(L.pos.clone().addScaledVector(L.dir,.014),L.pos);let K=Es(s,w.k,J,{bareEnd:!!w.b.terminal,bareStart:!!w.a.terminal});M.add(K.group),o.pickables.push(K.mesh),C.push({k:w.k,mesh:K.group})}d.push({local:new _(-a/2+.06,-l/2+.03,-c/2),text:"Incoming meter tails (R, Y, B, N)",ref:C.find(w=>w.k.kind==="meter-tail")?.k.id});let P=null;return n&&i&&(P=vd(o,n,i)),{enc:t,group:r,wires:C,kind:"db",callouts:d.concat(P?P.callouts.map(w=>({...w,lwb:!0})):[]),set(w){let U=Math.max(0,Math.min(1,w)),L=U*U*(3-2*U);e.left&&(e.left.rotation.y=-L*1.9),e.right&&(e.right.rotation.y=L*1.9),v.position.set(-L*.02,-L*(l*.55),m-2e-4+L*.16),v.rotation.x=L*.35,v.visible=L<.999,P?.set(w)},anchor(w){return w.lwb?P.anchor(w):w.local.clone().applyMatrix4(e.group.matrixWorld)},dispose(){e.group.remove(r),r.traverse(w=>w.geometry?.dispose()),e.left&&(e.left.rotation.y=0),e.right&&(e.right.rotation.y=0),P?.dispose()}}}function vd(o,t,e){let{model:n}=o,i=new rt;e.group.add(i);let s=t.size.w,r=t.size.h,a=t.size.depth,l=new D(ys(s-.004,r-.004,a,.0015),B("enclosureInner"));l.userData={kind:"enclosure",ref:t.id},i.add(l),o.pickables.push(l);let c=new D(new ot(s-.04,.035,.0075),B("dinRail"));c.position.set(0,-.02,-a+.012),i.add(c);let u=new Map,d=[],h={P:"#b8352b",N:"#2a2a2a",E:"#3f9442"};for(let M of n.termsByOwner.get(t.id)||[]){let A=rn(M.local),b=new D(new ot(.0062,.042,.045),new j({color:h[M.role]||"#888",roughness:.55}));b.position.set(A.x,-.02,-a+.012+.0225),b.userData={kind:"terminal",ref:M.id},i.add(b),o.pickables.push(b);for(let R of[.012,-.012]){let T=sn(.0017);T.position.set(A.x,-.02+R,-a+.0355),i.add(T)}u.set(M.id+":low",{pos:new _(A.x,-.02-.024,-a+.03),dir:new _(0,-1,0)}),u.set(M.id+":high",{pos:new _(A.x,-.02+.024,-a+.03),dir:new _(0,1,0)})}let f=n.termsByOwner.get(t.id)||[];if(f.length){let M=f.map(A=>A.local[0]);d.push({local:new _((Math.min(...M)+Math.max(...M))/2,-.02,-a+.04),text:`Outgoing P/N/E terminal blocks (${f.length/3} circuits)`,ref:f[0].id})}let p=n.frame(t).clone().invert(),m=ws(n,t,p);for(let[M,A]of m){let b=(A.conduit.diameter||20)/2e3,R=new D(ne([A.pos.clone().addScaledVector(A.dir,-.07),A.pos.clone().addScaledVector(A.dir,.005)],b,18),B("conduit"));R.userData={kind:"conduit",ref:M},i.add(R),o.pickables.push(R)}m.size&&d.push({local:[...m.values()][0].pos.clone(),text:"Outgoing circuit conduits (to slab)",ref:[...m.keys()][0]});let x=new Map,v=Rs(n,t);v.forEach(M=>{for(let A of[M.a,M.b])A.mouth&&x.set(A.mouth,(x.get(A.mouth)||0)+1)});let S=new Map;for(let M of v){let A=J=>J.mouth&&n.get(J.mouth).kind==="coupler",b=M.a.terminal?M.a:M.b,R=M.a.terminal?M.b:M.a;if(!b.terminal||!R.mouth)continue;let T=A(R),I=u.get(b.terminal+(T?":low":":high")),C=m.get(R.mouth);if(!I||!C)continue;let P=S.get(R.mouth)||0;S.set(R.mouth,P+1);let[k,w]=As(C.dir),U=Ts(P,x.get(R.mouth)||1,(C.conduit.diameter||20)/2e3*.55),L=C.pos.clone().addScaledVector(k,U.x).addScaledVector(w,U.y),V=[L,L.clone().addScaledVector(C.dir,.02),I.pos.clone().addScaledVector(I.dir,.02),I.pos],X=Es(n,M.k,V,{bareEnd:!0});i.add(X.group),o.pickables.push(X.mesh)}let y=e.cover;return{callouts:d,set(M){let A=M*M*(3-2*M);y&&(y.position.set(0,A*(r*.9),.006+A*.12),y.visible=A<.999)},anchor(M){return M.local.clone().applyMatrix4(e.group.matrixWorld)},dispose(){e.group.remove(i),i.traverse(M=>M.geometry?.dispose()),y&&(y.position.set(0,0,.006),y.visible=!0)}}}function qa(o,t,e={}){let{model:n}=o,i=n.frame(t),s=new rt;i.decompose(s.position,s.quaternion,s.scale),o.root.add(s);let r=t.size[0]/2,a=t.size[2],l=new D(new Tt(r,r,a,32,1,!0),B("pvcBox"));l.rotation.x=Math.PI/2,l.position.z=-a/2,l.material.side=ue,l.userData={kind:"box",ref:t.id};let c=new D(new ae(r,32),B("pvcBox"));c.position.z=-a,s.add(l,c),o.pickables.push(l);let u=[{local:new _(0,0,-a/2),text:t.label,ref:t.id}];if(t.kind==="fan-box"){let S=Ra([[-.045,0,-a-.05],[-.045,0,.01],[-.045,0,.07],[.045,0,.07],[.045,0,.01],[.045,0,-a-.05]].map(A=>new _(...A)),.006,{bend:.03}),y=new D(S,B("hook"));y.userData={kind:"box",ref:t.id},s.add(y);let M=new D(new Ne(.016,.006,10,24),B("rubber"));M.position.set(0,0,.082),s.add(M),u.push({local:new _(0,0,.07),text:"Fan hook (12 mm MS U-rod) with insulator",ref:t.id})}let d=new Map;for(let S of n.termsByOwner.get(t.id)||[]){let y=rn(S.local);y.z=.01;let M=new D(new ot(.011,.013,.011),B("connector"));M.position.copy(y),M.userData={kind:"terminal",ref:S.id},s.add(M),o.pickables.push(M),d.set(S.id,{pos:y.clone().add(new _(0,0,-.007)),dir:new _(0,0,-1)})}u.push({local:new _(0,0,.012),text:t.kind==="fan-box"?"Fan connector (house wiring side)":"Point connector",ref:(n.termsByOwner.get(t.id)||[])[0]?.id});let h=i.clone().invert(),f=ws(n,t,h);for(let[S,y]of f){let M=(y.conduit.diameter||20)/2e3,A=new D(ne([y.pos.clone().addScaledVector(y.dir,-.08),y.pos.clone().addScaledVector(y.dir,.004)],M,16),B("conduit"));A.userData={kind:"conduit",ref:S},s.add(A),o.pickables.push(A)}let p=new Map,m=Rs(n,t);m.forEach(S=>{for(let y of[S.a,S.b])y.mouth&&p.set(y.mouth,(p.get(y.mouth)||0)+1)});let x=new Map,v=S=>{if(S.terminal)return d.get(S.terminal);let y=f.get(S.mouth);if(!y)return null;let M=x.get(S.mouth)||0;x.set(S.mouth,M+1);let[A,b]=As(y.dir),R=Ts(M,p.get(S.mouth)||1,(y.conduit.diameter||20)/2e3*.5);return{pos:y.pos.clone().addScaledVector(A,R.x).addScaledVector(b,R.y),dir:y.dir.clone()}};for(let S of m){let y=v(S.a),M=v(S.b);if(!y||!M)continue;let A=y.pos.clone().add(M.pos).multiplyScalar(.5);A.z=Math.min(A.z,-.015);let b=Es(n,S.k,[y.pos,y.pos.clone().addScaledVector(y.dir,.015),A,M.pos.clone().addScaledVector(M.dir,.015),M.pos],{bareEnd:!!S.b.terminal,bareStart:!!S.a.terminal});s.add(b.group),o.pickables.push(b.mesh)}if(t.kind==="fan-box"){let S=new rt,y=["#b5302a","#1e1f21","#3e9440"];[-.012,0,.012].forEach((M,A)=>{let b=Ca([new _(M,0,.017),new _(M*.3,.004,.05),new _(0,0,.2)],.0011,{samples:24}),R=new D(b,en(y[A]));R.userData={kind:"fan-lead",ref:t.pointId},S.add(R),o.pickables.push(R)}),s.add(S),u.push({local:new _(0,.004,.08),text:"Fan's own leads (manufacturer side)",ref:t.pointId})}return{enc:t,group:s,callouts:u,kind:"slab",set(){},anchor(S){return S.local.clone().applyMatrix4(s.matrixWorld)},dispose(){o.root.remove(s),s.traverse(S=>S.geometry?.dispose())}}}var Cs=class{constructor(t){this.viewer=t,this.saved=new Map,this.box=null}open(t){this.close();let e=[];t.axes.forEach((s,r)=>{let a=s.clone().normalize(),l=a.dot(t.centre),c=t.half[r];e.push(new qt(a.clone(),-l-c)),e.push(new qt(a.clone().negate(),l-c))});let n=new ee;for(let s of[-1,1])for(let r of[-1,1])for(let a of[-1,1])n.expandByPoint(t.centre.clone().addScaledVector(t.axes[0],s*t.half[0]).addScaledVector(t.axes[1],r*t.half[1]).addScaledVector(t.axes[2],a*t.half[2]));n.expandByScalar(.01);let i=new Set;for(let s of this.viewer.meshes){if(!s.visible)continue;let r=s.geometry;if(r.boundingBox||r.computeBoundingBox(),!r.boundingBox.intersectsBox(n))continue;let a=Array.isArray(s.material)?s.material:[s.material];for(let l of a)i.add(l)}for(let s of i)this.saved.set(s,{planes:s.clippingPlanes,intersection:s.clipIntersection,shadows:s.clipShadows}),s.clippingPlanes=e,s.clipIntersection=!0,s.clipShadows=!0,s.needsUpdate=!0;return this.box=t,this.viewer.dirty=!0,i.size}close(){for(let[e,n]of this.saved)e.clippingPlanes=n.planes,e.clipIntersection=n.intersection,e.clipShadows=n.shadows,e.needsUpdate=!0;let t=this.saved.size>0;this.saved.clear(),this.box=null,t&&(this.viewer.dirty=!0)}get active(){return!!this.box}};function io(o,t,e,n,{inset:i=.0015,proud:s=.004}={}){let r=o.matrixWorld,a=new _().setFromMatrixColumn(r,0).normalize(),l=new _().setFromMatrixColumn(r,1).normalize(),c=new _().setFromMatrixColumn(r,2).normalize();return{centre:new _().setFromMatrixPosition(r).clone().addScaledVector(c,(s-n)/2),axes:[a,l,c],half:[t/2-i,e/2-i,(n+s)/2]}}function Ya(o,t,e,n,i,{proud:s=.004}={}){let r=t.clone().sub(o),a=r.length();r.normalize();let l=e.clone().normalize(),c=l.clone().cross(r).normalize(),u=r;return{centre:o.clone().add(t).multiplyScalar(.5).addScaledVector(l,(s-i)/2),axes:[u,c,l],half:[a/2,n/2,(i+s)/2]}}var fi=1.2,ke=null;function so(o){return ke||(ke=eo(64,16,(t,e,n)=>{t.clearRect(0,0,e,n);let i=t.createLinearGradient(0,0,0,n);i.addColorStop(0,"rgba(62,199,216,0)"),i.addColorStop(.32,"rgba(62,199,216,.55)"),i.addColorStop(.5,"rgba(160,240,248,1)"),i.addColorStop(.68,"rgba(62,199,216,.55)"),i.addColorStop(1,"rgba(62,199,216,0)"),t.fillStyle=i,t.fillRect(0,0,e,n),t.fillStyle="rgba(255,255,255,.85)",t.fillRect(4,n/2-1.5,14,3)},"trace-strip")),ke.wrapS!==_e&&(ke.wrapS=_e,ke.needsUpdate=!0),new ce({map:ke,color:o?"#ffffff":"#c8f6fb",transparent:!0,opacity:o?.95:.7,depthWrite:!1,toneMapped:!1,side:ue,polygonOffset:!0,polygonOffsetFactor:-2,polygonOffsetUnits:-2})}function Za(o,t,e,n){let i=it(o),s=it(t),r=new _(e[0],e[2],-e[1]),a=s.clone().sub(i),l=a.length();if(l<1e-4)return null;a.normalize();let c=a.clone().cross(r).normalize().multiplyScalar(n/2),u=r.clone().multiplyScalar(.0012),d=[i.clone().add(c).add(u),i.clone().sub(c).add(u),s.clone().sub(c).add(u),s.clone().add(c).add(u)],h=new Pt;return h.setAttribute("position",new ct(d.flatMap(f=>[f.x,f.y,f.z]),3)),h.setAttribute("uv",new ct([0,0,0,1,l/.2,1,l/.2,0],2)),h.setIndex([0,1,2,0,2,3]),h}var Is=class{constructor(t){this.ctx=t,this.group=new rt,this.group.name="Engineering overlay: traced route",this.group.renderOrder=20,t.root.add(this.group),this.cut=null,this.circuitId=null}conduitsFor(t){let e=this.ctx.model,n=e.circuit(t);if(!n)return[];let i=new Set(e.data.conduits.filter(s=>s.circuitIds.includes(t)).map(s=>s.id));for(let s of e.data.conduits)s.function==="service"&&i.add(s.id);if(n.floor===1||t==="SUB")for(let s of e.data.conduits)s.circuitIds.includes("SUB")&&i.add(s.id);return[...i].map(s=>e.get(s))}show(t,{emphasise:e=[]}={}){if(this.clear(),this.circuitId=t,!t)return;let n=new Set(e),i=so(!1),s=so(!0);for(let l of this.conduitsFor(t))for(let[c,u]of(l.reveal||[]).entries()){let d=Za(u.a,u.b,u.normal,n.has(l.id)?.036:.028);if(!d)continue;let h=new D(d,n.has(l.id)?s:i);h.renderOrder=20,h.userData={kind:"trace",ref:l.id,overlay:!0,piece:c},h.frustumCulled=!0,this.group.add(h),this.ctx.pickables.push(h)}let r=new ai(.022,.03,24),a=new ce({color:Ia.trace,transparent:!0,opacity:.9,depthWrite:!1,toneMapped:!1,side:ue,polygonOffset:!0,polygonOffsetFactor:-3});for(let l of this.ctx.model.pointsByCircuit.get(t)||[]){let c=l.boxId&&this.ctx.model.get(l.boxId);if(!c||!c.position||c.mount)continue;let u=new D(r,a);u.position.copy(it([c.position[0],c.position[1],c.position[2]-.003])),u.rotation.x=Math.PI/2,u.renderOrder=21,this.group.add(u)}this.ctx.viewer.dirty=!0}flow(t){ke&&(ke.wrapS=_e,ke.offset.x=t==null?0:-(t*.6)%1)}clear(){for(let t of[...this.group.children])this.group.remove(t),t.geometry?.dispose();this.ctx.pickables.splice(0,this.ctx.pickables.length,...this.ctx.pickables.filter(t=>!t.userData?.overlay)),this.circuitId=null,this.ctx.viewer.dirty=!0}openCut(t,e,n=null){this.closeCut();let i=this.ctx.model,s=i.get(t);if(!s||!s.reveal?.length)return null;let r=s.reveal.filter(T=>!e||T.roomId===e),a=(r.length?r:s.reveal).reduce((T,I)=>{let C=Math.hypot(I.b[0]-I.a[0],I.b[1]-I.a[1],I.b[2]-I.a[2]);return!T||C>T.L?{p:I,L:C}:T},null)?.p;if(!a)return null;let l=it(a.a),c=it(a.b),u=l.distanceTo(c),d=u>fi;if(d){let T=c.clone().sub(l).normalize(),I=n?Math.min(Math.max(n.clone().sub(l).dot(T),fi/2),u-fi/2):u/2,C=l.clone().addScaledVector(T,I);l=C.clone().addScaledVector(T,-fi/2),c=C.clone().addScaledVector(T,fi/2)}let h=new _(a.normal[0],a.normal[2],-a.normal[1]),f=l.distanceTo(c);if(f<.08)return null;let p=this.trueSegment(s,l,c),m=p?Math.min(.09,p.depth+p.r+.012):.06,x=p?Math.max(.09,p.r*2+.06):.09,v=Ya(l,c,h,x,m);this.ctx.apertures.open(v);let S=new rt;S.name="cutaway:"+t;let y=c.clone().sub(l).normalize(),M=y.clone().cross(h).normalize(),A=new D(new Rt(f,x),B("chase")),b=new lt().makeBasis(y,M,h);A.quaternion.setFromRotationMatrix(b),A.position.copy(l.clone().add(c).multiplyScalar(.5)).addScaledVector(h,-m),S.add(A);for(let T of[-1,1]){let I=new D(new Rt(f,m),B("chase")),C=new lt().makeBasis(y,h,M.clone().multiplyScalar(-T));I.quaternion.setFromRotationMatrix(C),I.position.copy(l.clone().add(c).multiplyScalar(.5)).addScaledVector(M,T*x/2).addScaledVector(h,-m/2),I.material=B("chase"),I.material.side=ue,S.add(I)}for(let T of[l,c]){let I=new D(new Rt(x,m),B("chase")),C=new lt().makeBasis(M,h,y);I.quaternion.setFromRotationMatrix(C),I.position.copy(T).addScaledVector(h,-m/2),I.material.side=ue,S.add(I)}if(p){let T=p.a,I=p.b,C=new Tt(p.r,p.r,T.distanceTo(I),28,1,!0,Math.PI/2,Math.PI),P=new D(C,B("conduitCut")),k=I.clone().sub(T).normalize(),w=h.clone().sub(k.clone().multiplyScalar(h.dot(k))).normalize(),U=k.clone().cross(w).normalize();P.quaternion.setFromRotationMatrix(new lt().makeBasis(U,k,w)),P.position.copy(T.clone().add(I).multiplyScalar(.5)),P.userData={kind:"conduit",ref:t},S.add(P),this.ctx.pickables.push(P);let L=i.conductorsByConduit.get(t)||[];L.forEach((V,X)=>{let J=X/Math.max(1,L.length)*Math.PI+Math.PI/2+.25,K=p.r*.52,E=U.clone().multiplyScalar(Math.sin(J)*K).addScaledVector(w,Math.cos(J)*K*.8-p.r*.1),N=T.clone().add(E),H=I.clone().add(E),$=new D(ne([N,H],no(V.size),8),V.colour==="PE"?Ss(i.colour("PE").hex,i.colour("PE").stripe):en(i.colour(V.colour).hex));$.userData={kind:"conductor",ref:V.id},S.add($),this.ctx.pickables.push($)})}this.ctx.root.add(S);let R=s.reveal.indexOf(a);for(let T of this.group.children)T.userData.ref===t&&T.userData.piece===R&&(T.visible=!1);if(d){let T=C=>[C.x,-C.z,C.y],I=so(!0);for(let[C,P]of[[a.a,T(l)],[T(c),a.b]]){let k=Za(C,P,a.normal,.036);if(!k)continue;let w=new D(k,I);w.renderOrder=20,w.userData={kind:"trace",ref:t,overlay:!0},S.add(w),this.ctx.pickables.push(w)}}return this.cut={group:S,conduitId:t,piece:a,A:l.clone(),B:c.clone(),anchor:l.clone().add(c).multiplyScalar(.5)},this.ctx.viewer.dirty=!0,this.cut}trueSegment(t,e,n){let i=e.clone().add(n).multiplyScalar(.5),s=null;for(let l=0;l<t.points.length-1;l++){let c=it(t.points[l]),u=it(t.points[l+1]),f=new Qe(c,u).closestPointToPoint(i,!0,new _).distanceTo(i);(!s||f<s.d)&&(s={d:f,a:c,b:u})}if(!s)return null;let r=s.b.clone().sub(s.a).normalize(),a=l=>s.a.clone().addScaledVector(r,l.clone().sub(s.a).dot(r));return{a:a(e),b:a(n),r:(t.diameter||20)/2e3,depth:s.d}}closeCut(){for(let e of this.group.children)e.visible=!0;if(!this.cut){this.ctx.apertures.close();return}this.ctx.root.remove(this.cut.group),this.cut.group.traverse(e=>e.geometry?.dispose());let t=new Set;this.cut.group.traverse(e=>t.add(e)),this.ctx.pickables.splice(0,this.ctx.pickables.length,...this.ctx.pickables.filter(e=>!t.has(e))),this.cut=null,this.ctx.apertures.close(),this.ctx.viewer.dirty=!0}};var pi=o=>String(o).replace(/[&<>"']/g,t=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[t]),mi=new _,Ps=class{constructor(t,e){this.host=t,this.viewer=e,this.svg=document.createElementNS("http://www.w3.org/2000/svg","svg"),this.svg.setAttribute("class","leader-layer"),this.layer=document.createElement("div"),this.layer.className="label-layer",t.append(this.svg,this.layer),this.selection=null,this.callouts=[],this.selEl=document.createElement("div"),this.selEl.className="scene-label selected",this.selEl.hidden=!0,this.layer.append(this.selEl),this.calloutEls=[],this.visibleCheck=0}select(t,e,n=[],i="selected"){this.selection={anchor:t.clone(),title:e,rows:n,tone:i,seen:!0,checked:0},this.selEl.className=`scene-label ${i}`,this.selEl.innerHTML=`<strong>${pi(e)}</strong>${n.length?`<dl>${n.map(([s,r])=>`<dt>${pi(s)}</dt><dd>${pi(r)}</dd>`).join("")}</dl>`:""}`,this.selEl.hidden=!1}clearSelection(){this.selection=null,this.selEl.hidden=!0}setCallouts(t,{tone:e="trace",onPick:n=null}={}){for(let i of this.calloutEls)i.remove();this.calloutEls=t.map(i=>{let s=document.createElement("button");return s.type="button",s.className=`scene-callout ${e}`,s.innerHTML=`<span class="num">${pi(i.n)}</span><span class="txt">${pi(i.text)}</span>`,n&&i.ref&&s.addEventListener("click",r=>{r.stopPropagation(),n(i.ref)}),this.layer.append(s),s}),this.callouts=t.map(i=>({...i,anchor:i.anchor.clone(),seen:!0}))}clearCallouts(){this.setCallouts([])}project(t){let e=this.viewer.camera;mi.copy(t).project(e);let n=this.host.clientWidth,i=this.host.clientHeight;return{x:(mi.x*.5+.5)*n,y:(-mi.y*.5+.5)*i,inFront:mi.z>-1&&mi.z<1,w:n,h:i}}occluded(t){let e=this.viewer;return e.mode==="walk"&&e.walker?!e.walker.sees(e.camera.position,t,.06):!1}update(t=!1){let e=[],n=t||++this.visibleCheck%6===0;if(this.selection){let i=this.selection,s=this.project(i.anchor);n&&(i.seen=!this.occluded(i.anchor));let r=s.inFront&&i.seen&&s.x>-40&&s.x<s.w+40&&s.y>-40&&s.y<s.h+40;if(this.selEl.hidden=!r,r){let a=this.selEl.getBoundingClientRect(),l=s.x<s.w*.62,c=l?s.x+46:s.x-46-a.width,u=s.y-a.height-26;u<48&&(u=s.y+26),c=Math.max(8,Math.min(s.w-a.width-8,c)),u=Math.max(48,Math.min(s.h-a.height-8,u)),this.selEl.style.transform=`translate(${Math.round(c)}px, ${Math.round(u)}px)`;let d=l?c:c+a.width,h=Math.min(Math.max(s.y,u+10),u+a.height-10);e.push(`<circle cx="${s.x}" cy="${s.y}" r="3.2" class="anchor selected"/><polyline class="leader selected" points="${s.x},${s.y} ${(s.x+d)/2},${h} ${d},${h}"/>`)}}if(this.callouts.length){let s=this.callouts.map(h=>{let f=this.project(h.anchor);return{c:h,p:f}}).filter(({p:h})=>h.inFront&&h.x>0&&h.x<h.w&&h.y>0&&h.y<h.h),r=s.length?s.reduce((h,{p:f})=>h+f.x,0)/s.length:0,a=Math.min(...s.map(({p:h})=>h.x)),l=Math.max(...s.map(({p:h})=>h.x)),c=s.filter(({p:h})=>h.x<=r).sort((h,f)=>h.p.y-f.p.y),u=s.filter(({p:h})=>h.x>r).sort((h,f)=>h.p.y-f.p.y),d=(h,f)=>{let p=-1/0;for(let m of h){let x=this.calloutEls[this.callouts.indexOf(m.c)],v=x.getBoundingClientRect(),S=Math.max(m.p.y-v.height/2,p+4,48);S=Math.min(S,m.p.h-v.height-70),p=S+v.height;let y=34,M=f<0?Math.min(a,m.p.x)-y-v.width:Math.max(l,m.p.x)+y;M=Math.max(6,Math.min(m.p.w-v.width-6,M)),x.style.transform=`translate(${Math.round(M)}px, ${Math.round(S)}px)`,x.hidden=!1;let A=f<0?M+v.width:M,b=S+v.height/2;e.push(`<circle cx="${m.p.x}" cy="${m.p.y}" r="2.6" class="anchor trace"/><polyline class="leader trace" points="${m.p.x},${m.p.y} ${A+(f<0?10:-10)},${b} ${A},${b}"/>`)}};for(let h of this.calloutEls)h.hidden=!0;d(c,-1),d(u,1)}this.svg.innerHTML=e.join("")}};var on=o=>String(o).replace(/[&<>"']/g,t=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[t]),q=o=>Math.round(o*1e3)/1e3;function Md(o,t,e){let n=o.plan.floors.find(f=>f.floor===t),i=[];if(e){for(let f of o.conduits)if(f.circuitIds.includes(e)&&f.planFloor===t)for(let p of f.points)i.push(p);for(let f of o.enclosures)f.floor===t&&f.circuitIds?.includes(e)&&i.push(f.mount.face)}if(i.length<2)for(let f of n.walls)for(let p of f)i.push(p);let s=i.map(f=>f[0]),r=i.map(f=>f[1]),a=e&&i.length>=2?1.6:.9,l=Math.min(...s)-a,c=Math.max(...s)+a,u=Math.min(...r)-a,d=Math.max(...r)+a,h=7;if(c-l<h){let f=(l+c)/2;l=f-h/2,c=f+h/2}if(d-u<h*.6){let f=(u+d)/2;u=f-h*.3,d=f+h*.3}return[l,-d,c-l,d-u]}function Ja(o,t){let{floor:e,selection:n,circuitId:i,traceStep:s,snapshot:r}=t,a=o.plan.floors.find(b=>b.floor===e);if(!a)return"";let[l,c,u,d]=o.plan.bounds,h=t.view||Md(o,e,i),f=Math.max(.12,h[2]/70),p=Math.max(1,h[2]/10),m=b=>-b,x=b=>`${q(b[0])},${q(m(b[1]))}`,v=o.circuits.find(b=>b.id===i),S=n?.ref,y=[];y.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${h.map(q).join(" ")}" data-vb="${h.map(q).join(" ")}" class="plan-drawing" role="img" aria-label="${on(`${e?"First":"Ground"}-floor wiring plan`)}" style="--k:${q(f)};--sym:${q(p)}">`),y.push('<defs><pattern id="hatch" width=".12" height=".12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2=".12" stroke="var(--plan-wall-hatch)" stroke-width=".03"/></pattern></defs>');for(let b of a.rooms){let R=v?.rooms?.includes(b.id);y.push(`<polygon class="plan-room${R?" served":""}" data-room="${on(b.id)}" points="${b.polygon.map(x).join(" ")}"/>`)}for(let b of a.voids||[])y.push(`<polygon class="plan-void" points="${b.map(x).join(" ")}"/>`);for(let b of a.walls)y.push(`<polygon class="plan-wall" points="${b.map(x).join(" ")}"/>`);for(let b of a.openings)if(b.kind==="window"||b.kind==="glazed")y.push(`<line class="plan-window" x1="${q(b.p0[0])}" y1="${q(m(b.p0[1]))}" x2="${q(b.p1[0])}" y2="${q(m(b.p1[1]))}"/>`);else if(b.kind==="door"||b.kind==="entry"){let R=b.hinge==="end"?b.p1:b.p0,T=b.hinge==="end"?b.p0:b.p1,I=Math.hypot(T[0]-R[0],T[1]-R[1]),C=b.swingNormal||[0,0],P=[R[0]+C[0]*I,R[1]+C[1]*I];y.push(`<line class="plan-door-gap" x1="${q(b.p0[0])}" y1="${q(m(b.p0[1]))}" x2="${q(b.p1[0])}" y2="${q(m(b.p1[1]))}"/>`),y.push(`<line class="plan-door" x1="${q(R[0])}" y1="${q(m(R[1]))}" x2="${q(P[0])}" y2="${q(m(P[1]))}"/>`);let k=(T[0]-R[0])*C[1]-(T[1]-R[1])*C[0];y.push(`<path class="plan-swing" d="M${q(P[0])} ${q(m(P[1]))} A${q(I)} ${q(I)} 0 0 ${k>0?1:0} ${q(T[0])} ${q(m(T[1]))}"/>`)}else y.push(`<line class="plan-door-gap" x1="${q(b.p0[0])}" y1="${q(m(b.p0[1]))}" x2="${q(b.p1[0])}" y2="${q(m(b.p1[1]))}"/>`);let M=new Set(v?o.conduits.filter(b=>b.circuitIds.includes(v.id)).map(b=>b.id):[]),A=new Set(s?.refs||[]);for(let b of o.conduits){if(b.planFloor!==e)continue;let R=b.points.map(P=>[P[0],P[1]]),T=R.filter((P,k)=>!k||Math.hypot(P[0]-R[k-1][0],P[1]-R[k-1][1])>.005);if(T.length<2)continue;let I=M.has(b.id),C=["plan-conduit",b.function,I?"traced":"",A.has(b.id)?"step":"",S===b.id?"selected":""].join(" ");if(y.push(`<polyline class="${C}" data-ref="${on(b.id)}" points="${T.map(x).join(" ")}"/>`),I&&b.kind==="chase"){let P=T[0];y.push(`<circle class="plan-drop${I?" traced":""}" cx="${q(P[0])}" cy="${q(m(P[1]))}" r=".05"/>`)}}for(let b of o.enclosures){if(b.floor!==e||!b.mount)continue;let R=b.mount,T=Math.max(.16,b.size.w),I=.07,C=R.face[0]+R.normal[0]*I/2,P=R.face[1]+R.normal[1]*I/2,k=Math.atan2(-R.tangent[1],R.tangent[0])*180/Math.PI,w=S===b.id,U=v?.enclosures?.includes(b.id),L=`plan-enc ${b.kind}${U?" traced":""}${w?" selected":""}${A.has(b.id)?" step":""}`;y.push(`<g class="${L}" data-ref="${on(b.id)}" transform="translate(${q(C)} ${q(m(P))}) rotate(${q(k)})">`),b.kind==="meter"?y.push(`<rect x="${q(-T/2)}" y="${-I}" width="${q(T)}" height="${I*2}" rx=".02"/><text class="plan-sym" y=".04">kWh</text>`):b.kind==="main-db"||b.kind==="sub-db"?y.push(`<rect x="${q(-T/2)}" y="${-I}" width="${q(T)}" height="${I*2}"/><path d="M${q(-T/2)} ${I} L${q(T/2)} ${-I}" class="plan-db-diag"/>`):y.push(`<rect x="${q(-T/2)}" y="${-I/2}" width="${q(T)}" height="${I}" rx=".01"/>`),y.push("</g>")}for(let b of o.points){if(b.floor!==e)continue;let R=r?.points?.[b.id],T=v&&b.circuitId===v.id,I=S===b.id,C=`plan-point ${b.kind}${R?" on":""}${T?" traced":""}${I?" selected":""}${A.has(b.id)?" step":""}`,[P,k]=b.position;y.push(`<g class="${C}" data-ref="${on(b.id)}" transform="translate(${q(P)} ${q(m(k))}) scale(${q(Math.min(p,2.2))})">${Sd(b.kind)}</g>`)}for(let b of o.boxes)b.kind!=="earth-pit"||e!==0||y.push(`<g class="plan-earth${S===b.id?" selected":""}" data-ref="${on(b.id)}" transform="translate(${q(b.position[0])} ${q(m(b.position[1]))})"><rect x="-.15" y="-.15" width=".3" height=".3"/><path d="M-.1 .02H.1M-.065 .07H.065M-.03 .12H.03M0 -.1V.02"/></g>`);for(let b of a.rooms)b.enclosed&&y.push(`<text class="plan-label" x="${q(b.label[0])}" y="${q(m(b.label[1]))}" style="font-size:${q(f)}px">${on(b.name)}</text>`);return y.push(`<text class="plan-front" x="${q((l+u)/2)}" y="${q(m(c)-.3)}" style="font-size:${q(f*.9)}px">FRONT \xB7 ROAD SIDE</text>`),y.push(`<g class="plan-scale" transform="translate(${q(h[0]+f*2)} ${q(h[1]+h[3]-f*2)})"><path d="M0 0H1M0 -.06V.06M1 -.06V.06" style="stroke-width:${q(f*.12)}px"/><text x=".5" y="${q(-f*.5)}" style="font-size:${q(f*.9)}px">1 m</text></g>`),y.push("</svg>"),y.join("")}function Sd(o){switch(o){case"downlight":case"light":return'<circle r=".11"/><path d="M-.078 -.078L.078 .078M-.078 .078L.078 -.078"/>';case"mirror-light":case"undercabinet":case"cove":return'<rect x="-.14" y="-.05" width=".28" height=".1"/><path d="M-.1 0H.1"/>';case"fan":return'<circle r=".13"/><path d="M0 0L.0 -.12M0 0L.104 .06M0 0L-.104 .06"/><circle r=".03" class="hub"/>';case"exhaust":return'<rect x="-.12" y="-.12" width=".24" height=".24"/><path d="M-.08 -.08L.08 .08M-.08 .08L.08 -.08"/>';case"socket6":return'<path d="M-.1 0A.1 .1 0 0 1 .1 0Z"/><path d="M0 -.1V-.16"/>';case"socket16":return'<path d="M-.12 0A.12 .12 0 0 1 .12 0Z"/><path d="M-.05 -.12V-.18M.05 -.12V-.18"/>';case"geyser-outlet":return'<rect x="-.12" y="-.08" width=".24" height=".16"/><text class="plan-sym" y=".04">G</text>';default:return'<circle r=".06"/>'}}var pt=o=>document.getElementById(o),tt=o=>String(o??"").replace(/[&<>"']/g,t=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[t]),bd={conductors:"Conductor",terminals:"Terminal",devices:"Device",enclosures:"Enclosure",points:"Point",conduits:"Conduit",boxes:"Box",circuits:"Circuit",switches:"Switch",regulators:"Regulator"};function Ed(o){return o&&"RYB".includes(o)?`<span class="ph ${o}">${o}</span>`:'<span class="ph" style="background:#7d8a83">\u2013</span>'}function ro(o,t){let e=[{title:"Main DB \xB7 ground floor",list:o.data.circuits.filter(i=>i.floor===0&&i.id!=="SUB")},{title:"Submain",list:o.data.circuits.filter(i=>i.id==="SUB")},{title:"First-floor sub-DB",list:o.data.circuits.filter(i=>i.floor===1&&i.id!=="SUB")}],n=t.snapshot;pt("circuits").innerHTML=e.map(i=>`<div class="kicker">${tt(i.title)}</div>`+i.list.map(s=>{let r={lighting:"\u{1F4A1}",power:"\u{1F50C}",geyser:"\u2668",submain:"\u21EA"}[s.kind]||"";return`<button class="cbtn" data-circuit="${tt(s.id)}" aria-pressed="${t.circuitId===s.id}" title="${tt(s.label)}">
      <span class="id">${tt(s.id)}</span><span class="what">${r} ${tt(s.short)}</span><span>${Ed(s.phase)} <i class="dot ${n?.circuits?.[s.id]?"on":""}" title="${n?.circuits?.[s.id]?"Supplied":"Not supplied"}"></i></span></button>`}).join("")).join("")}function wd(o,t){return t.filter(Boolean).map(e=>{let n=o.facts.get(e);if(n){let s=o.source(n.source);return`<a class="ref" href="${tt(s?.url)}" target="_blank" rel="noopener" title="${tt(n.text)}">${tt(Td(s))} ${tt(n.ref)}</a>`}let i=o.assumptions.get(e);return i?`<span class="ref assume" title="${tt(i.text)}">Assumption: ${tt(i.title)}</span>`:""}).join("")}function Td(o){return o?{"S-CPWD":"CPWD 2023","S-WM":"Wireman TT","S-E9":"Easy9 BQT58820","S-E9DS":"Easy9 datasheets","S-LG":"Legrand India","S-CEA":"CEA 2023","S-CEAM":"CEA meters","S-IS732":"IS 732:2019","S-IS732-1989":"IS 732:1989","S-IS1293":"IS 1293","S-IS9537":"IS 9537-3","S-PC":"Polycab","S-SUPPLY":"Supply codes","S-BIS-TX":"BIS/IS 12360","S-VID":"Video"}[o.id]||o.id:""}function Ka(o){pt("sources").innerHTML=o.data.sources.map(e=>`<li><a href="${tt(e.url)}" target="_blank" rel="noopener">${tt(e.title)}</a> \u2014 ${tt(e.publisher)}${e.note?`. <span style="color:#6b7c72">${tt(e.note)}</span>`:""}</li>`).join(""),pt("assumptions").innerHTML=o.data.assumptions.map(e=>`<li><b>${tt(e.title)}.</b> ${tt(e.text)} <i>Confirm with: ${tt(e.confirm)}.</i></li>`).join(""),pt("not-modelled").innerHTML=o.data.notModelled.map(e=>`<li><b>${tt(e.title)}.</b> ${tt(e.why)}</li>`).join("");let t=o.data.notes||[];pt("placement-notes").innerHTML=t.length?t.map(e=>`<li>${tt(e)}</li>`).join(""):"<li>Every proposed point found a clear position.</li>"}function Ls(o,t,e){if(!e)return"";if(e._type==="conductors"){let n=t.conductorStatus(e.id);if(e.role==="PE")return"Protective earth \u2014 carries no normal load current";if(e.role==="N")return n.current?"Neutral \u2014 carrying return current":"Neutral \u2014 no load current at present";if(n.live)return n.current?"Live, carrying load current":"Live, no load operating";let i=(e.chain||o.circuit(e.circuitId)?.chain||[]).map(s=>o.get(s)).find(s=>s&&!t.closed(s.id));return i?`Not live \u2014 ${i.label} is ${t.state.tripped[i.id]?"tripped":"OFF"}`:(e.controls||[]).some(s=>!t.switchControlClosed(s))?"Not live \u2014 its switch is OFF":e.regulator&&t.regulatorStep(e.regulator)===0?"Not live \u2014 regulator at OFF":"Not live"}return e._type==="points"?t.pointSupplied(e.id)?"Supplied \u2014 operating":"Not supplied / switched off":e._type==="circuits"?t.circuitLive(e.id)?"Supplied":"Not supplied":e._type==="devices"&&e.operable?t.state.tripped[e.id]?"Tripped":t.closed(e.id)?"Closed (ON)":"Open (OFF)":e._type==="devices"&&["switch","switch16","local-mcb"].includes(e.kind)?t.switchClosed(e.switchId)?"ON (closed)":"OFF (open)":e._type==="devices"&&e.kind==="regulator"?`Step ${t.regulatorStep(e.regulatorId)} of 5`:""}function oo(o,t,e){var u;if(!e)return null;let n=e.circuitId?o.circuit(e.circuitId):null,i=d=>d?`${d.id} \xB7 ${d.short}`:"Service (before the main switch)",s=[],r=[],a=[],l=e.label||e.id,c=bd[e._type]||"Item";switch(e._type){case"conductors":{l=`${e.circuitId||"Service"} \xB7 ${o.roleText(e)}`,s.push(["Circuit",i(n)],["Role",o.roleText(e)],["Phase",n?n.phase:{L1:"R",L2:"Y",L3:"B",N:"N"}[e.role]||"\u2014"],["State",Ls(o,t,e)],["From",o.endName(e.from)],["To",o.endName(e.to)],["Size",e.size?`${e.size} mm\xB2 Cu (CPWD minimum)`:"By designer"],["Colour",o.colour(e.colour).name]);let d={L:"Phase (live) conductor from the circuit MCB. Only live conductors pass through switches and MCBs (CPWD 3.11.5; CEA Reg. 17).",L1:"One of the three service phases. It stays live up to the meter and the main switch even when the house is switched off.",L2:"One of the three service phases. It stays live up to the meter and the main switch even when the house is switched off.",L3:"One of the three service phases. It stays live up to the meter and the main switch even when the house is switched off.",SW:"Switched live: the switch (or local MCB) output that energises only its own point when ON. CPWD switches are ON when the knob is down.",REG:"Regulated live from the fan regulator, in series after the fan switch (IS 732:1989 C-8.1). Only the installation side is shown \u2014 not the fan\u2019s internal motor wiring.",N:"Neutral: the normal return path. It runs in the same conduit as its phase (CPWD 5.4.3(g)) and back to the neutral bar after the RCCB, so the RCCB can compare outgoing and returning current. It is never switched or fused (CEA Reg. 17).",PE:"Protective earth: connects exposed metal parts and socket earth pins to the earthing system so a fault can be cleared. It never carries normal return current (CPWD 5.4.4; CEA Reg. 43)."};r.push(d[e.role]||""),e.conduits.length&&r.push(`Runs through ${e.conduits.length} concealed conduit${e.conduits.length>1?"s":""}: ${e.conduits.join(", ")}.`),a.push("F-COLOUR",e.role==="PE"?"F-PE-CONDUIT":e.role==="N"?"F-BUNCH":"F-NEUTRAL",e.size?"F-COND":"A-RATINGS");break}case"terminals":{let d=o.ownerOf(e.id),h=o.data.conductors.filter(p=>p.from===e.id||p.to===e.id);l=e.label,s.push(["In",d?.label||d?.id],["Role",{P:"Phase connector",N:"Neutral connector",E:"Earth",SW:"Switched live",REG:"Regulated live",L:"Live",L1:"Phase R",L2:"Phase Y",L3:"Phase B"}[e.role]||e.role],["Wires",h.map(p=>`${p.circuitId||"svc"} ${p.role}`).join(", ")||"\u2014"]);let f=h.length?t.conductorStatus(h[0].id):null;f&&s.push(["State",e.role==="E"?"Earth: no normal current":f.live?"Live in the simulation":e.role==="N"?f.current?"Neutral: return current":"Neutral":"Not live"]),r.push(e.role==="P"||e.role==="N"||e.role==="E"?"The circuit lands on separate phase, neutral and earth connectors in the first box it reaches; point wiring starts from them (CPWD 3.5.6).":"Device terminal. Strip length about 10\u201312 mm; screw tightened to the maker\u2019s torque (Easy9 1.5\u20132 N\xB7m)."),a.push("F-TERM","F-E9");break}case"devices":{l=e.label;let d=o.get(e.enclosureId);s.push(["In",d?.label||"\u2014"]),e.circuitId&&s.push(["Circuit",i(o.circuit(e.circuitId))]),e.phase&&s.push(["Phase",e.phase]),e.standard&&s.push(["Standard",e.standard]),s.push(["Rating",e.rating?.sensitivity?`${e.rating.sensitivity}; current by designer`:"By designer (not calculated)"]);let h=Ls(o,t,e);h&&s.push(["State",h]);let f={mcb:"Single-pole MCB: opens the phase on overload or short circuit for its own circuit (CEA Reg. 37(4)). The neutral is not broken.",mcb4p:"Incoming 4-pole MCB: isolates R, Y, B and N together and protects the installation (CEA Reg. 37(2)).",rccb4p:"RCCB: compares the current in R, Y, B and N. Any leakage to earth above 30 mA makes it trip (CEA Reg. 44; CPWD G.3.1).",isolator2p:"Linked isolator for the first-floor board: switches phase and neutral together.",switch:"Single-pole modular switch in the live conductor, ON with the knob down (CPWD 3.14.1).",switch16:"16 A switch controlling its socket on the live side (CPWD 3.11.5, 3.11.7).",regulator:"Two-module step regulator in series after the fan switch (CPWD 3.16.1(h)); its metal body is earthed (CPWD 3.16.3).",socket6:"Shuttered 6 A 3-pin socket (IS 1293): live and neutral contacts below, earth contact above.",socket16:"Shuttered 16 A 3-pin socket (IS 1293) on its own switch.","local-mcb":"Local 16 A MCB controlling the water-heater socket (CPWD 3.11.6(c)).","neutral-bar":"Neutral bar: each outgoing circuit has its own neutral terminal; all neutrals here return through the RCCB.","earth-bar":"Earth bar and main earthing terminal: protective conductors of every circuit and the two earthing conductors meet here.",busbar:"Comb busbar: feeds the MCB inputs; each tooth is on one phase.",meter:"DISCOM meter: owned and sealed by the licensee (CEA metering regulations)."};r.push(f[e.kind]||""),a.push(...{mcb:["F-CEA-MAIN","F-E9-DIM"],mcb4p:["F-CEA-MAIN","F-MAINBOARD"],rccb4p:["F-CEA-RCD","F-RCD"],switch:["F-SWITCH-DOWN","F-NEUTRAL"],regulator:["F-FAN","F-REG-EARTH"],socket6:["F-IS1293","F-SOCKET-TYPE"],socket16:["F-IS1293","F-SOCKET-CTRL"],"local-mcb":["F-GEYSER"],meter:["F-CEA-METER"],"neutral-bar":["F-E9"],"earth-bar":["F-CEA-EARTH","F-PE-CONDUIT"]}[e.kind]||[]);break}case"enclosures":{l=e.label,c={switchboard:"Room switchboard","socket-plate":"Socket plate","geyser-mcb":"Geyser control","geyser-outlet":"Water-heater socket","main-db":"Main distribution board","sub-db":"Sub-distribution board","loose-wire-box":"Loose-wire box",meter:"Service meter"}[e.kind]||c;let d=e.mount;s.push(["Room",o.roomName(e.roomId)+(e.exterior?" (outside face)":"")]),s.push(["Mounted",e.exterior?"Surface box on the external wall":`Flush in ${(d.wallThickness*1e3).toFixed(0)} mm wall${d.finish>.02?" (over tiles/panel)":""}`]),s.push(["Box bottom",`${(d.face[2]-e.floor*o.data.floorHeight-e.size.h/2).toFixed(2)} m above floor`]),s.push(["Size",`${(e.size.w*1e3).toFixed(0)} \xD7 ${(e.size.h*1e3).toFixed(0)} mm${e.plateModules?` \xB7 ${e.plateModules}-module plate`:""}`]),e.circuitIds?.length&&s.push(["Circuits",e.circuitIds.join(", ")]);let h={switchboard:"Lighting circuit board: the circuit lands on P/N/E connectors (CPWD 3.5.6), switches in the live feed ceiling lights and fans, and the regulator sits in series after the fan switch. Box bottom at 1.1 m (CPWD 3.15.1).","socket-plate":"Power circuit outlet with its own control switch (CPWD 3.11.7). Light and power wiring use separate conduits (CPWD 3.2.6).","geyser-mcb":"Water-heater control: a 16 A MCB in a modular box at 1.1 m (CPWD 3.11.6(c)), on an independent circuit (CPWD 3.10.3).","geyser-outlet":"Water-heater socket at least 2 m above floor near the assumed heater position (CPWD 3.11.6(c)); the heater itself is not modelled.","main-db":"Main board: incoming 4-pole MCB and 30 mA RCCB, then outgoing MCBs on a comb busbar (CPWD 3.20.9; CEA Regs. 37, 44). 1 m clear in front (CEA Reg. 39).","sub-db":"First-floor board fed by the submain: 2-pole isolator and single-pole MCBs.","loose-wire-box":"Outgoing phase/neutral/earth terminal blocks for every circuit (CPWD 3.18.2, Fig. 8).",meter:"Sealed three-phase DISCOM meter, readable from outside the house; the cable from it is live whenever the DISCOM supply is on."};r.push(h[e.kind]||""),a.push(...{switchboard:["F-BOX-H","F-TERM","F-BOX","F-LG-DIM"],"socket-plate":["F-SOCKET-H","F-SOCKET-CTRL","F-POWER-CCT"],"geyser-mcb":["F-GEYSER"],"geyser-outlet":["F-GEYSER","A-GEYSER"],"main-db":["F-MAINBOARD","F-CEA-CLEAR","F-E9","F-E9-DIM","A-MAINDB"],"sub-db":["A-SUBDB","F-E9-DIM"],"loose-wire-box":["F-DB-PREWIRED"],meter:["F-CEA-METER","A-METER"]}[e.kind]||[]);break}case"points":{l=e.label;let d=e.controls?.length?o.get(e.controls[0]):null;s.push(["Circuit",i(n)],["Controlled by",d?`${d.label} switch`:"Its own switch / MCB"],["State",Ls(o,t,e)],["Position",e.provenance]),e.kind==="fan"&&s.push(["Fan",`${e.sweep} mm sweep, blades about 2.70 m above floor`]);let h={fan:`Ceiling fan point: the regulated live, neutral and protective earth reach a connector in the fan box, which hangs from a 12 mm MS hook cast in the slab (CPWD 3.16.1, Fig. 4). ${e.basis||""}. The fan\u2019s internal wiring is not shown.`,downlight:"Ceiling light point from the architectural scene: switched live, neutral and protective earth reach a point box in the slab above the fitting.",cove:"Cove LED strip in the false-ceiling band; its driver connection box is assumed in the slab above the cove pocket.",exhaust:"Exhaust fan in an external-wall opening, fed by flexible cord from an exhaust-fan point beside it (CPWD 3.16.2).",socket6:"6 A switched socket on a power circuit (CPWD 3.5.4).",socket16:"16 A switched socket on a power circuit.","geyser-outlet":"Water-heater socket controlled by the 16 A MCB near the bathroom door.","mirror-light":"Mirror light from the architectural scene, on the bathroom switchboard.",undercabinet:"Under-cabinet light from the architectural scene."};r.push(h[e.kind]||""),a.push(...{fan:["F-FAN","F-FAN-H","F-FAN-TABLE","A-FAN"],exhaust:["F-EXHAUST"],socket6:["F-SOCKET-H","F-6A-POWER"],socket16:["F-SOCKET-H","F-POWER-CCT"],"geyser-outlet":["F-GEYSER","A-GEYSER"],downlight:["F-LIGHT-CCT","A-POSITIONS"]}[e.kind]||["A-POSITIONS"]);break}case"conduits":{l=`Conduit ${e.id}`,c={service:"Service cable pipe",submain:"Submain riser",earthing:"Earthing conductor route",prewire:"DB pre-wiring passage"}[e.function]||"Concealed conduit";let d=o.conductorsByConduit.get(e.id)||[],h={};for(let f of d)(h[u=f.circuitId||"service"]||(h[u]=[])).push(f.role);s.push(["Route",e.label],["Size",`${e.diameter} mm ${e.material||"rigid PVC (IS 9537-3)"}`],["Carries",Object.entries(h).map(([f,p])=>`${f}: ${p.join(" ")}`).join(" \xB7 ")||"\u2014"]),e.fill&&s.push(["Fill",Object.entries(e.fill).map(([f,p])=>`${p} \xD7 ${f} mm\xB2`).join(", ")+" (CPWD Table 4.1 limit respected)"]),r.push("Concealed in a wall chase or embedded in the RCC slab (laid on the reinforcement before concreting). The cyan strip marks where it runs behind the finished surface; walk to a step of the route to see a cut-open section."),a.push("F-CONDUIT","F-SLAB","F-CHASE","F-BUNCH","A-ROUTES");break}case"boxes":{l=e.label,s.push(["Room",o.roomName(e.roomId)]),e.kind==="earth-pit"?(s.push(["Electrode",e.electrode]),r.push("One of two earth electrodes (CEA Reg. 18 own electrode; Reg. 43 two distinct connections), at least 1.5 m from the building and 3 m apart (CPWD F.8.9)."),a.push("F-CEA-EARTH","F-CEA-2EARTH","F-EARTH","A-EARTHING")):(r.push("Junction or outlet box flush with the slab soffit, at least 65 mm deep (CPWD 4.4.3(d))."),a.push("F-SLAB"));break}case"circuits":{l=e.label,s.push(["Protective device",e.mcb?`${e.id} MCB (single-pole)`:"\u2014"],["RCD","4-pole 30 mA RCCB at the main DB"],["Phase",e.phase],["Conductors",e.conductorSize?`${e.conductorSize} mm\xB2 Cu (${e.conductorBasis})`:e.conductorBasis],["Points",String(e.points.length)],["State",Ls(o,t,e)]),e.designW&&s.push(["Design load",`${e.designW} W on CPWD ratings (LED lights not added)`]),a.push(e.kind==="lighting"?"F-LIGHT-CCT":"F-POWER-CCT","A-GROUPING","F-BALANCE"),r.push("Grouping, phase and protective-device relationships are explicit: one MCB per circuit, all circuits behind the 30 mA RCCB, each circuit\u2019s phase and neutral in the same conduits.");break}default:}return{title:l,type:c,rows:s,text:r,refs:a}}function Qa(o,t,e,n=""){let i=oo(o,t,e);return i?(pt("insp-type").textContent=i.type,pt("insp-title").textContent=i.title,pt("insp-facts").innerHTML=i.rows.map(([s,r])=>`<dt>${tt(s)}</dt><dd>${tt(r)}</dd>`).join(""),pt("insp-text").innerHTML=i.text.filter(Boolean).map(s=>`<p>${tt(s)}</p>`).join(""),pt("insp-refs").innerHTML=wd(o,[...new Set(i.refs)]),pt("insp-actions").innerHTML=n,i):(pt("insp-type").textContent="Nothing selected",pt("insp-title").textContent="Click a board, wire, terminal or fitting",pt("insp-facts").innerHTML="",pt("insp-text").innerHTML="<p>In <b>Walk inside</b>, click a switchboard to open it. Each wire, terminal and device inside can be clicked; a label appears beside it.</p>",pt("insp-refs").innerHTML="",pt("insp-actions").innerHTML=n,null)}function Ds(o,t,e){let{encId:n}=e,i=n?o.get(n):null,s=(h,f,p)=>`<div class="row"><span><strong>${tt(h)}</strong>${f?`<small>${tt(f)}</small>`:""}</span>${p}</div>`,r=(h,f,p,m)=>`<button class="tog${m?" trip":""}" ${h}="${tt(f)}" aria-pressed="${!!(p&&!m)}">${m?"TRIPPED":p?"ON":"OFF"}</button>`;if(i&&["switchboard","socket-plate","geyser-mcb"].includes(i.kind)){pt("ctrl-title").textContent=i.label,pt("ctrl-sub").textContent=`${i.circuitIds.join(", ")} \xB7 ${o.circuit(i.circuitIds[0])?.phase} phase \xB7 operate the switches; only their own points change.`;let h=[];for(let f of o.data.switches.filter(p=>p.enclosureId===i.id)){let p=f.points.map(x=>o.get(x));h.push(s(`${f.label}${f.mcb?"":" switch"}`,p.map(x=>x.label.split(" \xB7 ").slice(1).join(" \xB7 ")).join(", "),r("data-switch",f.id,t.switchClosed(f.id))));let m=o.data.regulators.find(x=>x.points.some(v=>f.points.includes(v)));m&&h.push(s("Regulator",`Step ${t.regulatorStep(m.id)} of ${m.steps}`,`<span><button class="tog" data-reg="${tt(m.id)}" data-step="-1" aria-pressed="true">\u2212</button> <button class="tog" data-reg="${tt(m.id)}" data-step="1" aria-pressed="true">+</button></span>`))}pt("controls").innerHTML=h.join("")||'<p class="sub">No switches.</p>';return}let a=i?.kind==="sub-db"||i?.kind==="loose-wire-box"&&i.floor===1,l=o.get(a?o.data.distribution.subDB:o.data.distribution.mainDB);pt("ctrl-title").textContent=l.label,pt("ctrl-sub").textContent="Operate the main switch, RCCB and MCBs in the simulation. Demonstrate faults on the selected circuit \u2014 software only.";let c=o.devicesByEnclosure.get(l.id)||[],u=[];for(let h of c.filter(f=>f.operable&&f.kind!=="mcb"))u.push(s(h.label,h.residual?"Trips on earth leakage \u2265 30 mA":"Isolates the whole board",r("data-device",h.id,t.state.devices[h.id],t.state.tripped[h.id])));for(let h of c.filter(f=>f.kind==="mcb")){let f=o.circuit(h.circuitId);u.push(s(`${h.circuitId} MCB \xB7 ${h.phase}`,f?.short||"",r("data-device",h.id,t.state.devices[h.id],t.state.tripped[h.id])))}let d=e.circuitId;d&&d!=="SUB"&&u.push(`<div class="row"><span><strong>Demonstrate a fault on ${tt(d)}</strong><small>Shows which device would isolate it; no physics is modelled.</small></span><span>
      <button class="tog" data-fault="leakage" aria-pressed="false">Leakage</button> <button class="tog" data-fault="overload" aria-pressed="false">Overload</button></span></div>`),pt("controls").innerHTML=u.join("")}function ao(o,t,e){let n=o.data,i=n.supply,s=e&&o.circuit(e),r=t.snapshot(),a=n.devices.find(S=>S.kind==="mcb4p"),l=n.devices.find(S=>S.kind==="rccb4p"),c=n.devices.find(S=>S.kind==="isolator2p"),u=S=>r.devices[S]?.closed,d={R:168,Y:210,B:252},h={R:"var(--r)",Y:"var(--y)",B:"var(--b)"},f=S=>s&&s.phase===S?'stroke-width="5"':'stroke-width="2.5" opacity=".55"',p=s&&(s.floor===1||s.id==="SUB"),m=(S,y,M,A,b,R,T)=>`<g><rect x="${S}" y="${y}" width="${M}" height="${A}" rx="7" fill="${T===!1?"#f6e4dc":"#fff"}" stroke="${T===!1?"#c0582f":"#9db3a5"}"/>
    <text x="${S+M/2}" y="${y+A/2-(R?3:-4)}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#24382e">${tt(b)}</text>${R?`<text x="${S+M/2}" y="${y+A/2+10}" text-anchor="middle" font-size="9" fill="#5b6c64">${tt(R)}</text>`:""}</g>`,x=`<svg viewBox="0 0 340 236" role="img" aria-label="Single-line diagram of the assumed supply">
    ${m(6,8,92,34,"11 kV / 433 V","DISCOM transformer")}
    <path d="M98 25H118" stroke="#8a6d45" stroke-width="3"/>
    ${m(118,8,66,34,"Meter","sealed, DISCOM")}
    <path d="M184 25H204" stroke="#555" stroke-width="3"/>
    ${m(204,8,64,34,"Main MCB","4-pole",u(a.id))}
    <path d="M268 25H282" stroke="#555" stroke-width="3"/>
    ${m(282,8,52,34,"RCCB","30 mA",u(l.id)&&!r.devices[l.id]?.tripped)}
    <path d="M308 42V58H140" fill="none" stroke="#666" stroke-width="2"/>
    ${["R","Y","B"].map(S=>`<path d="M${d[S]} 58V120" stroke="${h[S]}" ${f(S)}/><text x="${d[S]}" y="132" text-anchor="middle" font-size="10" font-weight="800" fill="${h[S]}">${S}</text>`).join("")}
    <path d="M120 58V120" stroke="#1e1f21" stroke-width="2.5" opacity=".7"/><text x="120" y="132" text-anchor="middle" font-size="10" font-weight="800">N</text>
    <text x="8" y="80" font-size="9.5" fill="#4b5f54">Busbars after</text><text x="8" y="92" font-size="9.5" fill="#4b5f54">the RCCB</text>
    ${s?`<rect x="${(d[s.phase]||210)-30}" y="140" width="60" height="26" rx="6" fill="#ecfafc" stroke="var(--cyan-ink)"/><text x="${d[s.phase]||210}" y="157" text-anchor="middle" font-size="10.5" font-weight="800" fill="#0f6f7c">${tt(s.id)} MCB</text>
      <path d="M${d[s.phase]||210} 120V140" stroke="${h[s.phase]||"#888"}" stroke-width="4"/>`:""}
    ${p?m(232,176,102,30,"1st-floor sub-DB","isolator + MCBs",u(c.id)):""}
    <g transform="translate(8 182)"><path d="M10 0V14M2 14H18M5 18H15M8 22H12" stroke="var(--pe)" stroke-width="2" fill="none"/><path d="M34 0V14M26 14H42M29 18H39M32 22H36" stroke="var(--pe)" stroke-width="2" fill="none"/>
      <path d="M10 0V-6H118" stroke="var(--pe)" stroke-width="2" stroke-dasharray="5 3" fill="none"/><path d="M34 0V-6" stroke="var(--pe)" stroke-width="2"/>
      <text x="0" y="40" font-size="9.5" fill="#3b6b44">2 electrodes \u2192 main earthing terminal \u2192 PE in every circuit</text></g>
  </svg>`,v=i.phaseLoadW||{};pt("supply-diagram").innerHTML=x,pt("supply-text").innerHTML=`<p><b>Assumed:</b> ${tt(i.kind)}, ${tt(i.nominal)}. Design load on CPWD ratings \u2248 <b>${tt(i.designLoadKW)} kW</b> (R ${((v.R||0)/1e3).toFixed(1)} \xB7 Y ${((v.Y||0)/1e3).toFixed(1)} \xB7 B ${((v.B||0)/1e3).toFixed(1)} kW), LED lighting not added. That exceeds the single-phase limit in most state supply codes, so three-phase is a reasonable assumption \u2014 <b>not a verified fact</b>; the DISCOM confirms the actual connection.</p>
    <p>Each final circuit uses <b>one phase and its own neutral</b>, both returning through the RCCB; the <b>protective earth</b> is a separate fault path from the electrodes and never carries normal current.</p>`}function lo(o,t){pt("steps-section").hidden=!o,o&&(pt("steps").innerHTML=o.map((e,n)=>`<li data-step="${n}" class="${n===t?"current":""}">${tt(e.title)}</li>`).join(""))}var dt=o=>document.getElementById(o),Dn=3.15,g={viewer:null,model:null,sim:null,root:null,pickables:[],parts:new Map,fans:new Map,exhausts:new Map,caps:null,labels:null,apertures:null,routes:null,meterLed:null,cullList:[],cullAt:0,wasWalk:!1,ui:{layout:"3d",labels:!0,floor:0,circuitId:null,selection:null,open:null,trace:null,snapshot:null},sceneLightColour:new Map};function Ht(o){dt("view-status").textContent=o}async function Ad(){let o=window.__ELECTRICAL_TOUR_DATA__,[t,e]=o?[o.scene,o.model]:await Promise.all([fetch("scene.json").then(i=>i.json()),fetch("electrical-model.json").then(i=>i.json())]);if(delete window.__ELECTRICAL_TOUR_DATA__,t.planHash!==e.architecturalPlanHash)throw Error("The electrical model does not match this house.");let n=new window.FloorForgeViewer(dt("home-canvas"),{quality:"auto",hudInset:54,onStatus:()=>{}});g.viewer=n,n.setScene(t),n.setMode("dollhouse"),n.setFloor(0),n.setFocus(!0),g.model=new vs(e),g.sim=new Ms(e,jr(e)),g.root=new rt,g.root.name="Electrical installation (simulation)",n.root.add(g.root),g.apertures=new Cs(n),g.torch=new ci("#fff4e2",0,2.6,.5,.6,1.4),g.torch.castShadow=!1,n.scene.add(g.torch,g.torch.target),g.labels=new Ps(document.querySelector(".view3d"),n),g.routes=new Is(g),Rd(t),po(),Bd(),Ka(g.model),Fn("dollhouse"),Me(),Ht("Choose a circuit, or use Walk inside and click a switchboard to open it."),setInterval(()=>{g.labels.update()},1e3/30),requestAnimationFrame(el),window.__electricalTour=Od()}function Rd(o){let t=g.model;for(let e of t.data.enclosures){let n;if(["switchboard","socket-plate","geyser-mcb","geyser-outlet"].includes(e.kind)){n=Da(t,e,g.pickables);let i=e.mount.face,s=e.mount.normal;n.cull=[it([i[0]+s[0]*.04,i[1]+s[1]*.04,i[2]]),it([i[0]+s[0]*.04,i[1]+s[1]*.04,i[2]+.12])],n.seen=!0,g.cullList.push(n)}else["main-db","sub-db","loose-wire-box"].includes(e.kind)?n=Ua(t,e,g.pickables):e.kind==="meter"&&(n=Fa(t,e,g.pickables),g.meterLed=n.led);n&&(n.floor=e.floor,g.root.add(n.group),g.parts.set(e.id,n))}for(let e of t.data.points)if(e.kind==="fan"){let n=Ba(t,e,t.get(e.boxId),g.pickables);n.floor=e.floor,n.speed=0;let[i,s]=e.position,r=e.floor*Dn+2.69,a=e.sweep/2e3*.85;n.cull=[it([i,s,r]),it([i+a,s,r]),it([i-a,s,r]),it([i,s+a,r]),it([i,s-a,r])],n.seen=!0,g.cullList.push(n),g.root.add(n.group),g.fans.set(e.id,n)}else if(e.kind==="exhaust"){let n=Oa(t,e,g.pickables);n.floor=e.floor,n.speed=0,g.root.add(n.group),g.exhausts.set(e.id,n);let i=t.get(e.boxId),s=ka(t,i,g.pickables);s.floor=e.floor,g.root.add(s.group),g.parts.set(i.id,s)}for(let e of t.data.boxes)if(e.kind==="earth-pit"){let n=za(t,e,g.pickables);n.floor=0,g.root.add(n.group),g.parts.set(e.id,n)}g.caps=Ha(t,o,t.data.points),g.root.add(g.caps.on,g.caps.off),o.lights.forEach((e,n)=>g.sceneLightColour.set(n,e.color||"#ffdfae"))}function po(){let o=g.viewer.materials.clipPlane;g.root.traverse(t=>{if(t.isMesh)for(let e of Array.isArray(t.material)?t.material:[t.material])e.clippingPlanes||(e.clippingPlanes=[o],e.clipShadows=!0,e.needsUpdate=!0)})}function Me(){let{sim:o,model:t}=g,e=g.ui.snapshot=o.snapshot();for(let[s,r]of g.parts){if(r.rockers)for(let[a,l]of r.rockers)Na(l,o.switchClosed(a),!!l.userData.mcb);if(r.knobs)for(let[a,l]of r.knobs)l.rotation.z=-o.regulatorStep(a)*.52+1.3}let n=new lt().makeScale(0,0,0),i=g.viewer.data.lights;for(let s of g.caps.downs){let r=g.caps.index.get(s.id),a=e.points[s.id],l=new lt;(a?g.caps.off:g.caps.on).setMatrixAt(r,n),Cd(s,l),(a?g.caps.on:g.caps.off).setMatrixAt(r,l),s.sceneLight!=null&&(i[s.sceneLight].color=a?g.sceneLightColour.get(s.sceneLight):"#000000")}for(let s of t.data.points)(s.kind==="mirror-light"||s.kind==="undercabinet")&&s.sceneLight!=null&&(i[s.sceneLight].color=e.points[s.id]?g.sceneLightColour.get(s.sceneLight):"#000000");g.caps.on.instanceMatrix.needsUpdate=g.caps.off.instanceMatrix.needsUpdate=!0,g.viewer.updateLights(!0);for(let[s,r]of g.fans){let a=t.get(t.get(s).regulator);r.target=e.points[s]?o.regulatorStep(a.id)/a.steps*9:0}for(let[s,r]of g.exhausts)r.target=e.points[s]?30:0;for(let s of t.data.devices)s._toggle&&(s._toggle.position.y=o.closed(s.id)?.006:-.004);ro(t,g.ui),Ds(t,o,{encId:g.ui.open?.id||tl(),circuitId:g.ui.circuitId}),ao(t,o,g.ui.circuitId),Kt(),Nn(),g.viewer.dirty=!0}function Cd(o,t){let e=o.lens.r+.0012;return t.compose(it([o.lens.xy[0],o.lens.xy[1],o.lens.bottom-6e-4]),new kt,new _(e,1,e))}function tl(){let o=g.ui.selection&&g.model.get(g.ui.selection.ref);return o?o._type==="enclosures"?o.id:o.enclosureId?o.enclosureId:null:null}var ja=performance.now();function el(o){let t=Math.min(.05,(o-ja)/1e3);ja=o;let e=g.viewer,n=e.mode==="walk",i=n?e.levelOf(e.walker.position.y):e.floor,s=Math.max(0,Math.min(1,i));if(n&&s!==g.ui.floor){g.ui.floor=s;for(let h of document.querySelectorAll("[data-floor]"))h.setAttribute("aria-pressed",String(Number(h.dataset.floor)===s));Kt()}let r=!1;for(let[,h]of g.fans)h.speed+=(h.target-h.speed)*Math.min(1,t*1.2),Math.abs(h.speed)>.01&&h.group.visible&&(h.rotor.rotation.y-=h.speed*t,r=!0);for(let[,h]of g.exhausts)h.speed+=(h.target-h.speed)*Math.min(1,t*2),Math.abs(h.speed)>.01&&h.group.visible&&(h.hub.rotation.z-=h.speed*t,r=!0);if(g.meterLed){let h=Id(),f=h/1e3;g.meterLed.material.emissiveIntensity=h>0&&o/1e3*f%1<.12?3:0}let a=e.mode==="dollhouse"||e.mode==="plan";n&&rl(!g.wasWalk),g.wasWalk=n;let l=g.ui.open?.id;for(let h of[g.parts,g.fans,g.exhausts])for(let[f,p]of h)p.group.visible=(!a||p.floor<=i)&&(!n||p.seen!==!1||f===l);if(g.routes.group.visible=!a,g.ui.circuitId&&g.routes.group.children.length){let h=g.ui.snapshot?.circuits?.[g.ui.circuitId];g.routes.flow(h?o/1e3:null),h&&(r=!0)}let c=g.ui.open;if(c&&c.t!==c.goal){let h=Math.min(.25,(o-(c.last||o))/1e3);c.t+=Math.sign(c.goal-c.t)*Math.min(Math.abs(c.goal-c.t),h/.9),c.handle.set(c.t),c.fan&&(c.fan.canopyGroup.position.y=-c.t*.16),r=!0,c.t===0&&c.goal===0&&sl()}c&&(c.last=o);let u=!!(g.ui.open||g.routes.cut);document.querySelector(".view3d").classList.toggle("inspecting",u);let d=g.ui.open&&g.model.get(g.ui.open.id)?.kind;if(g.torch.intensity=u?d==="main-db"||d==="sub-db"?.9:2.2:0,u){g.torch.position.copy(e.camera.position);let h=new _(0,0,-1).applyQuaternion(e.camera.quaternion);g.torch.target.position.copy(e.camera.position).addScaledVector(h,1),g.torch.target.updateMatrixWorld()}r&&(e.dirty=!0),requestAnimationFrame(el)}function Id(){let o=0;for(let t of g.model.data.points)g.ui.snapshot.points[t.id]&&(o+={fan:60,socket6:100,socket16:1e3,"geyser-outlet":1e3,downlight:8}[t.kind]||0);return o}function Pd(o){if(g.shell&&(g.shell.parent?.remove(g.shell),g.shell.geometry.dispose(),g.shell=null),!o?.geometry?.attributes?.normal)return;let t=o.geometry.clone(),e=t.attributes.position,n=t.attributes.normal;t.computeBoundingSphere();let i=Math.min(.004,Math.max(7e-4,t.boundingSphere.radius*.04));for(let r=0;r<e.count;r++)e.setXYZ(r,e.getX(r)+n.getX(r)*i,e.getY(r)+n.getY(r)*i,e.getZ(r)+n.getZ(r)*i);let s=new D(t,new ce({color:"#f0a63a",side:hi,transparent:!0,opacity:.95,depthWrite:!1,toneMapped:!1}));s.renderOrder=30,s.userData={overlay:!0},o.add(s),g.shell=s,g.viewer.dirty=!0}function Lt(o,t=null,{quiet:e=!1,noLabel:n=!1,mesh:i=null}={}){let s=g.model,r=o?s.get(o):null;if(g.ui.selection=r?{ref:o,anchor:t}:null,Pd(r?i:null),!r){g.labels.clearSelection(),Nn(),Kt();return}let a=s.circuitOfObject(r);a&&a!==g.ui.circuitId&&!g.ui.trace&&Un(a,{quiet:!0});let l=oo(s,g.sim,r),c=t||nl(r);c&&g.ui.labels&&!n?g.labels.select(c,l.title,l.rows.slice(0,6)):g.labels.clearSelection(),Nn(),Kt(),e||Ht(`${l.type}: ${l.title}`)}function nl(o){let t=g.model;if(o._type==="enclosures")return it(o.mount.face);if(o._type==="points")return it(o.position);if(o._type==="boxes")return it(o.mount?o.mount.face:o.position);if(o._type==="terminals")return t.terminalWorld(o.id);if(o._type==="devices"&&o.enclosureId){let e=t.get(o.enclosureId);return t.local(e,[o.x??0,o.y??0,-.01])}if(o._type==="conduits"){let e=o.reveal?.[0];return e?it(e.a).lerp(it(e.b),.5):it(o.points[Math.floor(o.points.length/2)])}return o._type==="conductors"?t.terminalWorld(o.to):null}function Nn(){let t=g.ui.selection&&g.model.get(g.ui.selection.ref)||(g.ui.circuitId?g.model.circuit(g.ui.circuitId):null),e="";t?._type==="enclosures"&&t.kind!=="meter"&&(e+=`<button class="primary" data-act="open" data-ref="${tt(t.id)}">${g.ui.open?.id===t.id||g.ui.open?.id===t.db?"Close cover":"Open cover"}</button>`),t?._type==="points"&&(t.kind==="fan"||t.kind==="downlight")&&(e+=`<button class="primary" data-act="openpoint" data-ref="${tt(t.id)}">${g.ui.open?.id===t.boxId?"Close":t.kind==="fan"?"Lower the canopy":"Inspect point box"}</button>`);let n=t&&g.model.circuitOfObject(t);n&&!g.ui.trace&&(e+=`<button class="tool" data-act="trace" data-ref="${tt(n)}">Follow ${tt(n)} from the meter</button>`),Qa(g.model,g.sim,t,e)}function Un(o,{quiet:t=!1}={}){g.ui.circuitId=o,g.ui.planView=null,g.routes.show(o),ro(g.model,g.ui),Ds(g.model,g.sim,{encId:g.ui.open?.id||tl(),circuitId:o}),ao(g.model,g.sim,o),Kt(),g.ui.selection||Nn(),!t&&o&&Ht(`${g.model.circuit(o).label}. Cyan marks its concealed route on ceilings and walls; walls still hide other rooms.`)}var co=new ui;function il(o,t){let n=dt("home-canvas").getBoundingClientRect(),i=new O((o-n.left)/n.width*2-1,-(t-n.top)/n.height*2+1);co.setFromCamera(i,g.viewer.camera);let s=u=>{for(let d=u;d;d=d.parent)if(!d.visible)return u.userData?.proxy;return!0},r=co.intersectObjects(g.pickables.filter(s),!1);if(!r.length)return null;let a=g.viewer,l=a.mode==="dollhouse"||a.mode==="plan"?a.floor*Dn+1.22:1/0,c=co.intersectObjects(a.meshes.filter(u=>u.visible),!1).find(u=>u.point.y<l&&!Ld(u.point));for(let u of r)if(!(u.point.y>l+.001))return c&&c.distance<u.distance-.015&&!u.object.userData?.overlay?null:u;return null}function Ld(o){let t=g.apertures.box;if(!t)return!1;let e=o.clone().sub(t.centre);return t.axes.every((n,i)=>Math.abs(e.dot(n))<=t.half[i]+.003)}function Dd(o){let t=il(o.clientX,o.clientY);if(!t)return;let e=t.object.userData,n=g.model;switch(e.kind){case"switch":{g.sim.toggleSwitch(e.ref);let i=n.get(e.ref);Me(),Lt(i.deviceId,t.point,{quiet:!0});let s=i.points.map(r=>n.get(r));Ht(`${i.label}: ${g.sim.switchClosed(e.ref)?"ON":"OFF"} \u2014 only ${s.length>1?`these ${s.length} points change`:"this point changes"}; its neutral is untouched.`);return}case"regulator":{let i=n.get(e.ref);g.sim.setRegulator(e.ref,(g.sim.regulatorStep(e.ref)+1)%(i.steps+1)),Me(),Lt(i.deviceId,t.point,{quiet:!0}),Ht(`Regulator step ${g.sim.regulatorStep(e.ref)} of ${i.steps}.`);return}case"plate":case"enclosure":{let i=n.get(e.ref);if(i?.kind==="meter"){Lt(i.id,t.point);return}let s=g.ui.open?.id,r=!!s&&[i.id,i.lwb,i.db].includes(s);if(e.door||!r){gi(i.id);return}Lt(i.id,t.point);return}case"device":{let i=n.get(e.ref);e.toggle&&i.operable&&(g.sim.toggleDevice(i.id),Me(),Ht(`${i.label}: ${g.sim.closed(i.id)?"closed (ON)":"open (OFF)"}.`)),Lt(e.ref,t.point,{mesh:t.object});return}case"fan-canopy":xi(e.ref);return;case"trace":Lt(e.ref,t.point);return;case"fan-lead":Lt(e.ref,t.point),Ht("Fan supply leads (manufacturer side). The fan's internal motor wiring is deliberately not shown.");return;default:e.ref&&Lt(e.ref,t.point,{mesh:t.object})}}function gi(o,{teleport:t=!0}={}){let e=g.model,n=e.get(o);if(n.kind==="loose-wire-box"&&(n=e.get(n.db)),g.ui.open?.id===n.id){ze();return}ze(!0),g.viewer.mode!=="walk"&&Fn("walk"),t&&Ud(n);let i=g.parts.get(n.id),s,r;if(n.kind==="main-db"||n.kind==="sub-db"){let a=e.get(n.lwb);s=$a(g,n,i,a,g.parts.get(a.id));let l=n.size.h+a.size.h,c=a.size.h/2;r=io(i.group,n.size.w,l,n.size.depth),r.centre.addScaledVector(r.axes[1],c)}else s=Xa(g,n,i),r=io(i.group,n.size.boxW,n.size.boxH,n.size.depth);i.group.updateMatrixWorld(!0),g.apertures.open(r),po(),g.ui.open={id:n.id,handle:s,t:0,goal:1},mo(s),Lt(n.id,null,{quiet:!0,noLabel:!0}),n.circuitIds?.[0]&&!g.ui.trace&&Un(n.circuitIds[0],{quiet:!0}),Ds(e,g.sim,{encId:n.id,circuitId:g.ui.circuitId}),Ht(`${n.label} opened (de-energised in reality). Numbered callouts name the parts; click any wire, terminal or device.`)}function xi(o){let t=g.model,e=t.get(o),n=e&&t.get(e.boxId);if(!n)return;if(g.ui.open?.id===n.id){ze();return}ze(!0),g.viewer.mode!=="walk"&&Fn("walk"),Fd(e);let i=qa(g,n),s=t.frame(n),r=new _().setFromMatrixPosition(s),a=[new _(1,0,0),new _(0,0,1),new _(0,1,0)],l=[n.size[0]/2+.012,n.size[1]/2+.012,(n.size[2]+.01)/2];r.y+=(n.size[2]-.006)/2,g.apertures.open({centre:r,axes:a,half:l}),po(),g.ui.open={id:n.id,handle:i,t:0,goal:1,fan:e.kind==="fan"?g.fans.get(o):null},mo(i),Lt(o,null,{quiet:!0}),Ht(e.kind==="fan"?"Canopy lowered: fan box with hook, insulator and the house-wiring connector. Click a conductor to identify it.":"Point box opened above the light fitting.")}function mo(o){let t=o.callouts.filter(e=>e.ref||e.text).map((e,n)=>({n:n+1,anchor:o.anchor(e),text:e.text,ref:e.ref,c:e}));g.ui.callouts=t,g.ui.labels&&g.labels.setCallouts(t,{onPick:e=>Lt(e)})}function ze(o=!1){let t=g.ui.open;if(!t)return;if(o){t.handle.set(0),t.fan&&(t.fan.canopyGroup.position.y=0),t.t=0,t.goal=0,sl();return}t.goal=0;let e=g.model.get(t.id);Ht(`${e?.label||"Cover"}: ${t.fan?"canopy raised":"cover closing"}. Click it again to reopen.`)}function sl(){let o=g.ui.open;if(!o)return;o.handle.dispose(),g.apertures.close(),g.labels.clearCallouts(),g.ui.callouts=null,g.ui.open=null;let t=new Set;g.root.traverse(e=>t.add(e)),g.pickables.splice(0,g.pickables.length,...g.pickables.filter(e=>t.has(e)||e.userData?.overlay)),Nn()}setInterval(()=>{let o=g.ui.open;if(o&&g.ui.callouts)for(let t of g.ui.callouts)t.anchor.copy(o.handle.anchor(t.c));g.labels&&g.labels.callouts.forEach((t,e)=>{g.ui.callouts?.[e]&&t.anchor.copy(g.ui.callouts[e].anchor)})},50);var Nd=new _;function rl(o=!1){let t=g.viewer,e=g.cullList;if(!t.walker||!e.length)return;let n=t.walker.eyePosition(Nd),i=o?e.length:Math.min(e.length,12);for(let s=0;s<i;s++){let r=e[g.cullAt++%e.length];r.seen=n.distanceTo(r.cull[0])<2||r.cull.some(a=>t.walker.sees(n,a,.06))}}function _i(o,t,e=58){let n=g.viewer;n.mode!=="walk"&&Fn("walk");let i=it([o[0],o[1],o[2]+.35]),s=it([o[0],o[1],o[2]+1.63]),a=it(t).clone().sub(s),l=Math.atan2(-a.x,-a.z),c=Math.atan2(a.y,Math.hypot(a.x,a.z));n.walker.teleport(i,l,Math.max(-1.2,Math.min(1.2,c))),rl(!0),n.walkFov=e,n.camera.fov=e,n.camera.updateProjectionMatrix(),n.hud?.setLocked?.(!0),n.dirty=!0}function Ud(o){let t=o.mount,e=g.model.room(o.roomId),n=o.floor*Dn,i=o.kind==="main-db"||o.kind==="sub-db"?.95:.55,s=(g.model.data.traces[o.circuitIds?.[0]]||[]).find(c=>c.refs.includes(o.id)&&c.view.foot),r=[t.face[0]+t.normal[0]*i,t.face[1]+t.normal[1]*i,n];(!e||!uo(e,r)||s)&&(r=s?.view.foot&&!uo(e,r)?s.view.foot:r);let a=[-t.normal[1],t.normal[0]],l=o.kind.endsWith("db")?[t.face[0],t.face[1],t.face[2]+.08]:[t.face[0]-a[0]*.1,t.face[1]-a[1]*.1,t.face[2]-.05];_i(r,l,o.kind.endsWith("db")?46:34)}function Fd(o){let t=g.model.room(o.roomId),e=o.floor*Dn,[n,i]=o.position,s=null;for(let r of[.9,1.2,.6,1.5])for(let a=0;a<8&&!s;a++){let l=a/8*Math.PI*2,c=[n+Math.cos(l)*r,i+Math.sin(l)*r,e];uo(t,c)&&(s=c)}_i(s||[n,i-.9,e],[n,i,o.position[2]-.05],o.kind==="fan"?30:36)}function uo(o,t){if(!o)return!1;let e=o.polygon,n=!1;for(let i=0,s=e.length-1;i<e.length;s=i++){let[r,a]=e[i],[l,c]=e[s];a>t[1]!=c>t[1]&&t[0]<(l-r)*(t[1]-a)/(c-a)+r&&(n=!n)}return n}function ho(o){let t=g.model.data.traces[o];t&&(Un(o,{quiet:!0}),g.ui.trace={cid:o,steps:t,i:0},dt("stepbar").classList.add("active"),document.querySelector(".view3d").classList.add("tracing"),an(0))}function an(o){let t=g.ui.trace;if(!t)return;t.i=Math.max(0,Math.min(t.steps.length-1,o));let e=t.steps[t.i];ze(!0),g.routes.closeCut(),g.routes.show(t.cid,{emphasise:e.refs});let n=g.model,i=e.refs.map(c=>n.get(c)).find(c=>c?._type==="enclosures"),s=[...e.refs].reverse().map(c=>n.get(c)).find(c=>c?._type==="conduits"),r=e.refs.map(c=>n.get(c)).find(c=>c?._type==="points");e.view.foot&&_i(e.view.foot,e.focus,i?46:s?40:52);let a=null;if(i&&i.kind!=="meter")gi(i.id,{teleport:!e.view.foot});else if(s){let c=g.routes.openCut(s.id,e.roomId,it(e.focus));if(c){let u=c.A,d=c.B,h=new Qe(u,d).closestPointToPoint(it(e.focus),!0,new _);g.labels.setCallouts([{n:e.n,anchor:h,text:"Opened chase: conduit cut lengthwise to show its conductors",ref:s.id}],{onPick:f=>Lt(f)}),a=h}}else r&&(r.kind==="fan"||r.kind==="downlight")&&xi(r.id);let l=e.refs[e.refs.length-1];Lt(l,l===s?.id?a:null,{quiet:!0}),dt("step-text").innerHTML=`<b>Step ${e.n} of ${t.steps.length} \xB7 ${tt(e.title)}</b><br>${tt(e.text)}`,lo(t.steps,t.i),Kt(),Ht(`Route ${t.cid}: step ${e.n} of ${t.steps.length}.`)}function fo(){g.ui.trace=null,ze(!0),g.routes.closeCut(),g.labels.clearCallouts(),dt("stepbar").classList.remove("active"),document.querySelector(".view3d").classList.remove("tracing"),lo(null),g.ui.circuitId&&g.routes.show(g.ui.circuitId),Kt()}function Kt(){let o=g.ui.layout,t=g.viewer?.mode==="walk"?g.viewer.levelOf(g.viewer.walker.position.y):g.ui.floor;if(g.ui.planFloor=Math.max(0,Math.min(1,t)),o==="3d")return;let e=g.ui.trace,n=e?e.steps[e.i]:null;dt("plan-body").innerHTML=Ja(g.model.data,{floor:g.ui.planFloor,selection:g.ui.selection,circuitId:g.ui.circuitId,traceStep:n,snapshot:g.ui.snapshot,view:g.ui.planView}),dt("plan-title").textContent=`${g.ui.planFloor?"First":"Ground"}-floor wiring plan`;let i=g.ui.circuitId&&g.model.circuit(g.ui.circuitId);dt("plan-circuit").textContent=i?i.label:"Select a circuit or symbol"}function Fn(o){let t=g.viewer;o!=="walk"&&(ze(!0),g.routes.closeCut()),t.setMode(o),o!=="walk"&&t.setFloor(g.ui.floor);for(let e of document.querySelectorAll("[data-mode]"))e.setAttribute("aria-pressed",String(e.dataset.mode===o));dt("view-chip").textContent=o==="walk"?"WALK \xB7 click a board to open it \xB7 drag to look \xB7 arrows/WASD to move":o==="dollhouse"?"CUTAWAY \xB7 walls cut at 1.22 m \xB7 fittings above the cut are hidden":"EXTERIOR",Kt()}function ol(o){g.ui.floor=o;for(let t of document.querySelectorAll("[data-floor]"))t.setAttribute("aria-pressed",String(Number(t.dataset.floor)===o));if(g.viewer.mode==="walk"){let t=g.model.data.rooms.find(e=>e.floor===o&&(o===0?e.id==="g-living":e.id==="u-lounge"))||g.model.data.rooms.find(e=>e.floor===o);_i([t.label[0],t.label[1],o*Dn],[t.label[0]+1,t.label[1],o*Dn+1.4])}else g.viewer.setFloor(o);Kt()}function al(o){g.ui.layout=o;let t=dt("viewport");t.classList.toggle("split",o==="split"),t.classList.toggle("plan-only",o==="plan");for(let e of document.querySelectorAll("[data-layout]"))e.setAttribute("aria-pressed",String(e.dataset.layout===o));Kt(),g.viewer.resized=!0,g.viewer.dirty=!0}function Bd(){let o=dt("home-canvas"),t=null;o.addEventListener("pointerdown",i=>{t=[i.clientX,i.clientY,performance.now()]}),o.addEventListener("pointerup",i=>{!t||Math.hypot(i.clientX-t[0],i.clientY-t[1])>5||Dd(i)});for(let i of document.querySelectorAll("[data-mode]"))i.addEventListener("click",()=>Fn(i.dataset.mode));for(let i of document.querySelectorAll("[data-floor]"))i.addEventListener("click",()=>ol(Number(i.dataset.floor)));for(let i of document.querySelectorAll("[data-layout]"))i.addEventListener("click",()=>al(i.dataset.layout));dt("labels-toggle").addEventListener("click",()=>{g.ui.labels=!g.ui.labels,dt("labels-toggle").setAttribute("aria-pressed",String(g.ui.labels)),g.ui.labels?g.ui.open&&mo(g.ui.open.handle):(g.labels.clearSelection(),g.labels.clearCallouts())}),dt("circuits").addEventListener("click",i=>{let s=i.target.closest("[data-circuit]")?.dataset.circuit;s&&(g.ui.selection=null,g.labels.clearSelection(),Un(s),Nn())}),dt("trace-start").addEventListener("click",()=>ho(g.ui.circuitId||g.model.data.circuits[0].id)),dt("trace-clear").addEventListener("click",()=>{fo(),Un(null),g.routes.clear(),Lt(null)}),dt("step-prev").addEventListener("click",()=>an(g.ui.trace.i-1)),dt("step-next").addEventListener("click",()=>an(g.ui.trace.i+1)),dt("step-exit").addEventListener("click",fo),dt("steps").addEventListener("click",i=>{let s=i.target.closest("[data-step]")?.dataset.step;s!=null&&an(Number(s))}),dt("insp-actions").addEventListener("click",i=>{let s=i.target.closest("[data-act]");s&&(s.dataset.act==="open"&&gi(s.dataset.ref),s.dataset.act==="openpoint"&&xi(s.dataset.ref),s.dataset.act==="trace"&&ho(s.dataset.ref))}),dt("controls").addEventListener("click",i=>{let s=i.target.closest("button");if(s){if(s.dataset.switch&&(g.sim.toggleSwitch(s.dataset.switch),Me()),s.dataset.reg&&(g.sim.setRegulator(s.dataset.reg,g.sim.regulatorStep(s.dataset.reg)+Number(s.dataset.step)),Me()),s.dataset.device){g.sim.toggleDevice(s.dataset.device),Me();let r=g.model.get(s.dataset.device);Ht(`${r.label}: ${g.sim.closed(r.id)?"ON":"OFF"}. Downstream circuits update in the plan and in 3D.`)}if(s.dataset.fault&&g.ui.circuitId){let r=g.sim.injectFault(g.ui.circuitId,s.dataset.fault);Me();let a=r?.device&&g.model.get(r.device);Ht(a?`${s.dataset.fault==="leakage"?"Earth-leakage":"Overload"} demonstration on ${g.ui.circuitId}: the ${a.label} trips. ${s.dataset.fault==="leakage"?"Every circuit behind this RCCB loses supply \u2014 a reason designers sometimes split RCDs.":"Only this circuit loses supply."} Reset it with its toggle.`:"This circuit is not supplied, so there is nothing to trip.")}}}),dt("plan-body").addEventListener("click",i=>{if(performance.now()-(g.ui.planPanned||0)<250)return;let s=i.target.closest("[data-ref]")?.getAttribute("data-ref");if(s){Lt(s);return}let r=i.target.closest("[data-room]")?.getAttribute("data-room"),a=r&&g.model.room(r);a?.boardId&&Lt(a.boardId)});let e=()=>dt("plan-body").querySelector("svg");dt("plan-body").addEventListener("wheel",i=>{let s=e();if(!s)return;i.preventDefault();let r=s.getAttribute("data-vb").split(" ").map(Number),a=s.getBoundingClientRect(),l=Math.min(a.width/r[2],a.height/r[3]),c=(a.width-r[2]*l)/2,u=(a.height-r[3]*l)/2,d=r[0]+(i.clientX-a.left-c)/l,h=r[1]+(i.clientY-a.top-u)/l,f=Math.exp(i.deltaY*.0015),p=Math.max(2.5,Math.min(30,r[2]*f)),m=r[3]*(p/r[2]);g.ui.planView=[d-(d-r[0])*(p/r[2]),h-(h-r[1])*(m/r[3]),p,m],Kt()},{passive:!1});let n=null;dt("plan-body").addEventListener("pointerdown",i=>{let s=e();s&&(n={x:i.clientX,y:i.clientY,vb:s.getAttribute("data-vb").split(" ").map(Number),moved:!1})}),window.addEventListener("pointermove",i=>{if(!n)return;let s=e();if(!s)return;let r=s.getBoundingClientRect(),a=Math.min(r.width/n.vb[2],r.height/n.vb[3]),l=(i.clientX-n.x)/a,c=(i.clientY-n.y)/a;Math.hypot(i.clientX-n.x,i.clientY-n.y)>4&&(n.moved=!0),n.moved&&(g.ui.planView=[n.vb[0]-l,n.vb[1]-c,n.vb[2],n.vb[3]],Kt())}),window.addEventListener("pointerup",()=>{n?.moved&&(g.ui.planPanned=performance.now()),n=null}),dt("plan-body").addEventListener("dblclick",i=>{let s=i.target.closest("[data-ref]")?.getAttribute("data-ref"),r=s&&g.model.get(s);if(!r){g.ui.planView=null,Kt();return}r._type==="enclosures"&&r.kind!=="meter"?gi(r.id):r._type==="points"&&(r.kind==="fan"||r.kind==="downlight")&&xi(r.id)}),window.addEventListener("keydown",i=>{!g.ui.trace||i.target.closest("input,select,textarea")||((i.key==="]"||i.key==="PageDown")&&an(g.ui.trace.i+1),(i.key==="["||i.key==="PageUp")&&an(g.ui.trace.i-1))})}function Od(){return{app:g,select:Lt,openEnclosure:gi,openPoint:xi,closeOpen:()=>ze(!0),setCircuit:Un,startTrace:ho,goStep:an,endTrace:fo,setMode:Fn,setFloor:ol,setLayout:al,teleport:_i,toggleSwitch:o=>{g.sim.toggleSwitch(o),Me()},snapshot:()=>g.sim.snapshot(),pickAt:(o,t)=>{let e=il(o,t);return e?{...e.object.userData,point:e.point.toArray()}:null},project:o=>{let t=g.model.get(o),e=t&&nl(t);if(!e)return null;let n=e.clone().project(g.viewer.camera),i=dt("home-canvas").getBoundingClientRect();return[i.left+(n.x*.5+.5)*i.width,i.top+(-n.y*.5+.5)*i.height,n.z]}}}Ad().catch(o=>{console.error(o),Ht(`Could not start the electrical tour: ${o.message}`)});})();
