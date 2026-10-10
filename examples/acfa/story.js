'use strict';
const W=1920,H=1080,$=x=>document.getElementById(x),canvas=$('gl'),gl=canvas.getContext('webgl',{alpha:true,antialias:true,preserveDrawingBuffer:true}),ctx=$('overlay').getContext('2d');
if(!gl)throw Error('WebGL is required for this data film.');
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x)),mix=(a,b,t)=>a+(b-a)*t,smooth=x=>{x=clamp(x);return x*x*(3-2*x)},fade=(t,a,b)=>smooth((t-a)/(b-a)),lerp=(a,b,t)=>a.map((v,i)=>mix(v,b[i],t)),norm=a=>{let n=Math.hypot(...a);return a.map(x=>x/n)},cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
function fit(){const r=Math.min(innerWidth/W,innerHeight/H);$('stage').style.transform=`scale(${r})`;$('stage').style.left=(innerWidth-W*r)/2+'px';$('stage').style.top=(innerHeight-H*r)/2+'px'}fit();addEventListener('resize',fit);if(new URLSearchParams(location.search).has('capture'))document.body.classList.add('capture');
const vert=`precision highp float;attribute vec3 aPosition;attribute vec3 aColor;uniform mat4 uModel;uniform mat4 uView;uniform mat4 uProj;uniform float uSize;uniform float uAlpha;uniform float uTint;uniform vec3 uColor;varying vec4 vColor;void main(){gl_Position=uProj*uView*uModel*vec4(aPosition,1.0);gl_PointSize=uSize;vColor=vec4(mix(aColor,uColor,uTint),uAlpha);}`;
const frag=`precision mediump float;varying vec4 vColor;void main(){float r=length(gl_PointCoord-vec2(.5));if(r>.5)discard;gl_FragColor=vec4(vColor.rgb,vColor.a*(1.0-smoothstep(.32,.5,r)));}`;
function shader(type,source){let s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vert));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,frag));gl.linkProgram(program);gl.useProgram(program);
const U=Object.fromEntries(['Model','View','Proj','Size','Alpha','Tint','Color'].map(x=>[x,gl.getUniformLocation(program,'u'+x)])),AP=gl.getAttribLocation(program,'aPosition'),AC=gl.getAttribLocation(program,'aColor');
const ID=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]),colors=[[.29,.87,.76],[1,.65,.29],[.34,.7,.96]];
let M,poses,points,reference,matrices,V,Q,vp,imgRef,imgStar;
function trans(p,m){return [m[0]*p[0]+m[4]*p[1]+m[8]*p[2]+m[12],m[1]*p[0]+m[5]*p[1]+m[9]*p[2]+m[13],m[2]*p[0]+m[6]*p[1]+m[10]*p[2]+m[14]]}
function buffer(a){let b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,a,gl.STATIC_DRAW);return b}
function bind(b){gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.enableVertexAttribArray(AP);gl.vertexAttribPointer(AP,3,gl.FLOAT,false,24,0);gl.enableVertexAttribArray(AC);gl.vertexAttribPointer(AC,3,gl.FLOAT,false,24,12)}
function lookAt(eye,target){let z=norm(eye.map((x,i)=>x-target[i])),x=norm(cross([0,0,1],z)),y=cross(z,x);return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1])}
function camera(rect,center,h,az=-58,el=27){vp=rect;gl.viewport(rect.x,H-rect.y-rect.h,rect.w,rect.h);const w=h*rect.w/rect.h;a: {}const r=Math.PI/180;let eye=center.map((v,i)=>v+240*[Math.cos(el*r)*Math.cos(az*r),Math.cos(el*r)*Math.sin(az*r),Math.sin(el*r)][i]);V=lookAt(eye,center);Q=new Float32Array([2/w,0,0,0,0,2/h,0,0,0,0,-2/1000,0,0,0,-1,1]);gl.uniformMatrix4fv(U.View,false,V);gl.uniformMatrix4fv(U.Proj,false,Q)}
function project(p){const v=trans(p,V);return [vp.x+(Q[0]*v[0]+1)*vp.w/2,vp.y+(1-Q[5]*v[1])*vp.h/2]}
function line(a,b,c,alpha=1,width=2){a=project(a);b=project(b);ctx.save();ctx.globalAlpha=alpha;ctx.strokeStyle=c;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();ctx.restore()}
function dot3(p,c,r=4,alpha=1,square=false){const q=project(p);ctx.save();ctx.globalAlpha=alpha;ctx.fillStyle=c;if(square)ctx.fillRect(q[0]-r,q[1]-r,2*r,2*r);else{ctx.beginPath();ctx.arc(...q,r,0,Math.PI*2);ctx.fill()}ctx.restore()}
function label(s,x,y,c='#edf6fa',size=34,align='left'){ctx.save();ctx.font=`${size>=44?'700 ':''}${size}px Lato`;ctx.textAlign=align;ctx.fillStyle=c;ctx.fillText(s,x,y);ctx.restore()}
function tagged(p,s,c,dx=0,dy=0){const a=project(p);let x=clamp(a[0]+dx,90,1520),y=clamp(a[1]+dy,300,820);ctx.font='700 31px Lato';const w=ctx.measureText(s).width;ctx.fillStyle='#0a1724e8';ctx.fillRect(x-12,y-35,w+24,48);label(s,x,y,c,31)}
function state(name,u){let g=M.stages[name],i=Math.round(clamp(u)*(g.count-1));return {name,index:Math.min(i,g.count-1),offset:(g.offset+Math.min(i,g.count-1))*M.chunkCount*16}}
function use(st){matrices=[];for(let k=0;k<M.chunkCount;k++)matrices.push(poses.subarray(st.offset+k*16,st.offset+(k+1)*16))}
function drawCloud(k,alpha,tint,color,size){const c=M.chunks[k];gl.uniformMatrix4fv(U.Model,false,matrices[k]);gl.uniform1f(U.Alpha,alpha);gl.uniform1f(U.Tint,tint);gl.uniform3fv(U.Color,color);gl.uniform1f(U.Size,size);gl.drawArrays(gl.POINTS,c.offset,c.count)}
function draw(active=[60,61,62],ref=0,rgb=0,context=.025){
 gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);bind(points);gl.depthMask(false);
 for(let k=0;k<M.chunkCount;k++)if(!active.includes(k))drawCloud(k,context,0,[.4,.6,.7],1.7);
 gl.depthMask(true);active.forEach((k,i)=>drawCloud(k,.98,mix(.7,0,rgb),active.length===1?[1,.61,.26]:colors[i%3],3.0));
 if(ref){bind(reference);gl.uniformMatrix4fv(U.Model,false,ID);gl.uniform1f(U.Alpha,ref*.85);gl.uniform1f(U.Tint,mix(.65,0,rgb));gl.uniform3fv(U.Color,[.28,.69,.99]);gl.uniform1f(U.Size,2.2);gl.depthMask(false);gl.drawArrays(gl.POINTS,0,M.spiritCount);gl.depthMask(true)}
}
function pairs(d,c,alpha=1){for(let i=0;i<d.a.length;i++){let a=trans(d.a[i],matrices[d.i]),b=d.j===undefined?d.b[i]:trans(d.b[i],matrices[d.j]);line(a,b,c,alpha*.8,2);dot3(a,c,4.4,alpha);dot3(b,c,4.4,alpha)}}
function gps(all=true,alpha=1,selected=[60,61,62]){
 for(const g of M.gpsGroups.filter(g=>selected.includes(g.k))){const ids=all?g.local.map((_,i)=>i):[0];for(const i of ids){const a=trans(g.local[i],matrices[g.k]),b=g.gps[i];line(a,b,'#ffd073',alpha*.8,2.1);dot3(a,'#d8ebf5',4,alpha);dot3(b,'#ffd073',5,alpha,true)}
  for(let i=1;i<g.gps.length;i++)line(g.gps[i-1],g.gps[i],'#ffd073',alpha*.3,1.4);
 }
}
function graph(many=false,showGPS=true){const x=1465,y=695,dx=145;ctx.save();ctx.fillStyle='#091522d9';ctx.fillRect(1330,505,510,278);label('Chunk graph',1360,549,'#edf6fa',30);
 for(let j=0;j<3;j++){let px=x+(j-1)*dx;if(j<2){ctx.strokeStyle='#65dfc4';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(px+29,y);ctx.lineTo(px+dx-29,y);ctx.stroke();ctx.fillStyle='#65dfc4';ctx.fillRect(px+dx/2-5,y-5,10,10)}ctx.strokeStyle='#65dfc4';ctx.lineWidth=2;ctx.beginPath();ctx.arc(px,y,29,0,Math.PI*2);ctx.stroke();label('T'+(60+j),px,y+8,'#edf6fa',23,'center');
 const count=showGPS?(many?3:1):0;for(let h=0;h<count;h++){let gx=px+(h-(count-1)/2)*29,gy=y-88;ctx.strokeStyle='#ffd073';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(gx,gy);ctx.lineTo(px,y-30);ctx.stroke();ctx.fillStyle='#ffd073';ctx.fillRect(gx-5,gy-5,10,10)}
 }label(!showGPS?'Shared-image overlap factors':many?'Frame-associated GPS':'One GPS anchor per chunk',1360,759,'#ffd073',24);ctx.restore()}
function matchCards(progress){
 const a={x:102,y:320,w:730,h:410},b={x:1100,y:320,w:560,h:420};ctx.drawImage(imgRef,a.x,a.y,a.w,a.h);ctx.drawImage(imgStar,b.x,b.y,b.w,b.h);label('Spirit · overhead reference',a.x,a.y-23,'#72c8f4',33);label('Starling · exploring camera',b.x,b.y-23,'#f4aa67',33);
 const count=Math.min(6,Math.ceil(progress*6));for(let i=0;i<count;i++){const m=M.imageMatches[i];let p=[a.x+m.uv_reference[0]/584*a.w,a.y+m.uv_reference[1]/328*a.h],q=[b.x+m.uv_exploring[0]/512*b.w,b.y+m.uv_exploring[1]/384*b.h];ctx.strokeStyle='#ca9aff';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(...p);ctx.lineTo(...q);ctx.stroke();for(const r of [p,q]){ctx.fillStyle='#ca9aff';ctx.beginPath();ctx.arc(...r,5,0,Math.PI*2);ctx.fill()}}
 label('Ground beside the red tower · six real factor inputs shown',102,797,'#b5c6d4',30)
}

const scenes=[
[0,'A chunk is more than its anchor.','A local reconstruction owns cameras, surfaces and a scale.','The graph must place the chunk and correct its metric size.'],
[10,'Standard GPSFactor: a rigid chunk state.','GTSAM Pose3 optimizes rotation and translation. Chunk scale stays fixed.','GPS can move the chunk; it cannot resize the geometry inside it.'],
[20,'Solve with chunk scales held fixed.','Actual GTSAM GPSFactor solve · same initial ACFA reconstruction.','Local surface factors and GPS act on six variables per chunk.'],
[34,'The same place does not line up.','Earlier and return visits reconstruct displaced surfaces.','Revisit checks were not fitted: P90 disagreement is 28.32 m.'],
[42,'Expose scale to the optimizer.','Your custom GPS factor acts on a seven-variable Similarity3 state.','Every measured camera position depends on its chunk’s scale.'],
[52,'Solve with scale correction enabled.','Actual GTSAM solve using the custom Sim3GPSFactor position term.','Changing one chunk state moves and rescales its cameras and dense points.'],
[66,'Scale freedom changes the result.','Same ACFA region and view · standard rigid GPS versus custom Sim3 GPS.','Revisit P90 falls from 28.32 m to 10.60 m. GPS still leaves drift.'],
[84,'Control: give both the same GPS readings.','Identical camera observations, weights, surface factors and initialization.','Fixed scale: 28.52 m. Free scale: 10.60 m. Extra GPS samples are not enough.'],
[100,'The optimizer corrects the chunk sizes.','The local predictions stay fixed; their world transformations change.','Scale corrections range from 0.746× to 1.250× the initialized values.'],
[112,'Next, constrain the map with another robot.','Continue from this Sim3 GPS solution. Keep GPS and overlaps active.','The fixed Spirit map supplies surface evidence for the Starling map.'],
[122,'Match the same surfaces across robots.','Verified UFM matches link pixels in the two existing reconstructions.','Lift each pixel through its own map’s depth, calibration and pose.'],
[136,'Add direct reference surface factors.','Local point p belongs to Starling. World point q comes from Spirit.','Residual: Tₖ(p) − q. The reference map stays fixed.'],
[142,'Solve the Starling–Spirit alignment.','Fresh GTSAM continuation · the existing GPS and overlap factors remain.','Scale, rotation and translation jointly reconcile the shared surfaces.'],
[158,'The shared surfaces come into agreement.','Original RGB returns after the factor visualization.','Cross-reference development P90: 6.17 m → 0.32 m.'],
[170,'Scale-aware chunks. Shared metric geometry.','A common graph connects local reconstruction, GPS and reference maps.','The same corrected transforms support both camera poses and dense geometry.']
];
function revisit(alpha=1){pairs(M.revisit,'#ca9aff',alpha)}
function stepLabel(st){label('Accepted update '+st.index+' / '+(M.stages[st.name].count-1),100,303,'#b5c6d4',28)}
function scaleBadge(t,st){const u=M.diagnostics.sim3_frame.scale_ratios[61];ctx.fillStyle='#091522e8';ctx.fillRect(1310,335,525,215);label('Example: chunk 61',1340,383,'#b5c6d4',31);label('1.000×  →  '+u.toFixed(3)+'×',1340,450,'#65dfc4',47);label('relative to its initialized scale',1340,507,'#b5c6d4',27)}
window.render=async function(t){if(!M)return;t=clamp(t,0,180);const scene=scenes.filter(s=>s[0]<=t).at(-1);$('title').textContent=scene[1];$('sub').textContent=scene[2];$('insight').textContent=scene[3];$('panels').style.display=t>=66&&t<100?'block':'none';$('eyebrow').textContent=t>=112?'ACFA / CROSS-ROBOT CONTINUATION':t>=84&&t<100?'ACFA / MATCHED SCALE ABLATION':'ACFA / FIXED SCALE vs SCALE CORRECTION';
 gl.viewport(0,0,W,H);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);ctx.clearRect(0,0,W,H);let st;
 if(t>=66&&t<100){const matched=t>=84,ln=matched?'rigid_frame':'rigid_anchor';$('leftLabel').textContent=matched?'Pose3 · same camera GPS':'Pose3 + standard GPSFactor';$('rightLabel').textContent='Sim3 + custom GPS';const l=M.metrics[ln],r=M.metrics.sim3_frame;$('leftMetric').textContent='Revisit P90: '+l.revisit_disagreement.p90_m.toFixed(2)+' m';$('rightMetric').textContent='Revisit P90: '+r.revisit_disagreement.p90_m.toFixed(2)+' m';
  for(let i=0;i<2;i++){st=state(i?'sim3_frame':ln,1);use(st);camera({x:90+i*960,y:340,w:790,h:425},M.comparison_view.center,86,-58,35);draw([8,61],0,0,.009);revisit(.75)}
  label('Unused-overlap P90: '+l.unused_overlap.p90_m.toFixed(3)+' m',96,870,'#ffd073',28);label('Unused-overlap P90: '+r.unused_overlap.p90_m.toFixed(3)+' m',1056,870,'#65dfc4',28);
 }else if(t>=122&&t<136){st=state('sim3_reference',0);matchCards(fade(t,123,128));}
 else{
  const rect={x:0,y:245,w:1920,h:620};
  if(t<20)st=state('rigid_anchor',0);else if(t<34)st=state('rigid_anchor',(t-20)/14);else if(t<42)st=state('rigid_anchor',1);else if(t<52)st=state('sim3_frame',0);else if(t<66)st=state('sim3_frame',(t-52)/14);else if(t<112)st=state('sim3_frame',1);else if(t<142)st=state('sim3_reference',0);else if(t<158)st=state('sim3_reference',(t-142)/16);else st=state('sim3_reference',1);
  use(st);
  if(t>=112){let end=fade(t,168,180),center=lerp(M.tower_center.map((v,i)=>v+[1,0,-2][i]),[7,32,-22],end);camera(rect,center,mix(50,138,end),mix(-145,-36,end),mix(28,53,end));draw(end>.2?[]:[85],fade(t,112,116),fade(t,158,164),mix(.025,.95,end));if(t>=136&&t<161)pairs(M.anchor,'#72c8f4',1-fade(t,158,161));if(t>=142&&t<158)stepLabel(st);}
  else if((t>=20&&t<42)||(t>=52&&t<66)){camera(rect,M.comparison_view.center,90,-58,35);draw([8,61],0,0,.014);if(t>=34){revisit(1);label('Green: earlier visit    Orange: return visit',100,305,'#b5c6d4',28);label('Purple links are evaluation checks, not fitted factors.',100,828,'#ca9aff',29)}else{gps(t>=52,.65,[8,61]);stepLabel(st)}}
  else{camera(rect,[25,66,-24],78,-58,27);draw(t<8||t>=100?[61]:[60,61,62],0,0,t<8?0:.02);if(t>=5&&t<10)for(const x of M.seams)pairs(x,'#65dfc4',fade(t,5,8));if(t>=10&&t<20){gps(false,fade(t,10,13));graph(false)}if(t>=42&&t<52){gps(true,fade(t,42,45));graph(true)}if(t>=100){scaleBadge(t,st);gps(true,.7,[61])}}
 }
 const phase=t<42?0:t<112?1:2;document.querySelectorAll('.step').forEach((s,i)=>s.classList.toggle('active',i===phase));const moving=(t>=20&&t<34)||(t>=52&&t<66)||(t>=142&&t<158);
 $('provenance').textContent=t>=112?'Fresh continuation · GPS + overlaps retained':moving?'Recorded accepted GTSAM states · no geometry interpolation':t>=66&&t<100?'Same point identities and view · position-only GPS comparison':'Fixed initial ACFA geometry · Pose3 versus Similarity3';$('progress').style.width=t/180*100+'%';$('seek').value=t;$('clock').textContent=`${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,'0')} / 3:00`;gl.finish();window.currentStoryState={t,stage:st.name,index:st.index,scene:scene[1],illustrative:false};return window.currentStoryState;
};
let playing=false,start=0,paused=0;function tick(time){if(playing){let t=paused+(time-start)/1000;if(t>=180){t=180;playing=false;$('play').textContent='▶'}window.render(t)}requestAnimationFrame(tick)}$('play').onclick=()=>{playing=!playing;if(playing){paused=Number($('seek').value);if(paused>=180)paused=0;start=performance.now()}else paused=Number($('seek').value);$('play').textContent=playing?'❚❚':'▶'};$('seek').oninput=()=>{playing=false;paused=Number($('seek').value);$('play').textContent='▶';window.render(paused)};
function getImage(src){return new Promise((resolve,reject)=>{let im=new Image();im.onload=()=>resolve(im);im.onerror=reject;im.src=src})}
(async()=>{try{const [m,c,r,p,ir,is]=await Promise.all([fetch('assets/story.json').then(r=>r.json()),fetch('assets/chunks.bin').then(r=>r.arrayBuffer()),fetch('assets/spirit.bin').then(r=>r.arrayBuffer()),fetch('assets/poses.bin').then(r=>r.arrayBuffer()),getImage('assets/reference_216.png'),getImage('assets/exploring_1710.png')]);M=m;points=buffer(new Float32Array(c));reference=buffer(new Float32Array(r));poses=new Float32Array(p);imgRef=ir;imgStar=is;await document.fonts.ready;$('loading').remove();await window.render(0);window.storyReady=true;requestAnimationFrame(tick)}catch(e){$('loading').textContent=e.stack;window.storyError=e.stack;console.error(e)}})();
