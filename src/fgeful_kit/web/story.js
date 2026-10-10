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

// Scene timing selects recorded states; it never interpolates measured geometry.
function fitText(element, maximum, minimum) {
  element.style.fontSize = maximum + 'px';
  let size = maximum;
  while (element.scrollWidth > element.clientWidth + 1 && size > minimum) {
    size -= 1;
    element.style.fontSize = size + 'px';
  }
}
window.render = async function(t) {
  if (!M) return;
  t = clamp(t, 0, M.duration);
  const index = M.scenes.findLastIndex(s => s.start <= t);
  const scene = M.scenes[index];
  const end = M.scenes[index + 1]?.start ?? M.duration;
  const progress = clamp((t - scene.start) / (end - scene.start));
  $('title').textContent = scene.title;
  $('sub').textContent = scene.subtitle || '';
  $('insight').textContent = scene.insight || '';
  $('eyebrow').textContent = M.provenance.kind === 'synthetic' ? 'SYNTHETIC / TEACHING EXAMPLE' : 'RECORDED / DATA EXPLAINER';
  fitText($('title'), 72, 40);
  fitText($('sub'), 34, 23);
  fitText($('insight'), 34, 23);
  $('panels').style.display = 'none';
  $('steps').style.display = 'none';
  $('provenance').textContent = M.provenance.kind === 'synthetic' ? 'Synthetic geometry and scripted states' : 'Recorded states · no geometry interpolation';
  gl.viewport(0, 0, W, H);
  gl.clearColor(0, 0, 0, 0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  ctx.clearRect(0, 0, W, H);
  const selected = [];
  scene.panels.forEach((panel, n) => {
    const st = state(panel.stage, panel.progress ?? progress);
    selected.push({stage: st.name, index: st.index});
    use(st);
    const two = scene.panels.length === 2;
    const rect = {x: two ? 76 + n * 920 : 76, y: 340, w: two ? 848 : 1768, h: 500};
    const view = panel.view || M.view;
    camera(rect, view.center, view.height, view.az ?? -58, view.el ?? 30);
    ctx.save();
    ctx.beginPath(); ctx.rect(rect.x, rect.y, rect.w, rect.h); ctx.clip();
    gl.enable(gl.SCISSOR_TEST);
    gl.scissor(rect.x, H - rect.y - rect.h, rect.w, rect.h);
    draw(panel.active || M.chunks.map((_, i) => i), panel.reference ? 1 : 0, panel.rgb ? 1 : 0, .04);
    for (const link of M.links || []) {
      if (link.stages && !link.stages.includes(st.name)) continue;
      pairs(link, link.color || '#ca9aff', .85);
    }
    if (panel.gps !== false) gps(true, .65, (M.gpsGroups || []).map(g => g.k));
    ctx.restore();
    gl.disable(gl.SCISSOR_TEST);
    label(panel.label || panel.stage, rect.x + 12, 302, n ? '#65dfc4' : '#ffd073', 31);
    label(`Recorded index ${st.index} / ${M.stages[st.name].count - 1}`, rect.x + 12, 880, '#b5c6d4', 25);
  });
  $('progress').style.width = t / M.duration * 100 + '%';
  $('seek').value = t;
  $('clock').textContent = `${t.toFixed(1)} / ${M.duration.toFixed(1)} s`;
  gl.finish();
  window.currentStoryState = {t, scene: index, kind: M.provenance.kind, panels: selected};
  return window.currentStoryState;
};
let playing = false, start = 0, paused = 0;
function tick(time) {
  if (playing) {
    const t = Math.min(M.duration, paused + (time - start) / 1000);
    window.render(t);
    if (t >= M.duration) { playing = false; $('play').textContent = '▶'; }
  }
  requestAnimationFrame(tick);
}
$('play').onclick = () => {
  playing = !playing;
  paused = Number($('seek').value);
  if (playing) { if (paused >= M.duration) paused = 0; start = performance.now(); }
  $('play').textContent = playing ? '❚❚' : '▶';
};
$('seek').oninput = () => { playing = false; $('play').textContent = '▶'; window.render(Number($('seek').value)); };
async function get(path, json=false) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Cannot load ${path}: ${response.status}`);
  return json ? response.json() : response.arrayBuffer();
}
(async () => {
  try {
    const [m, c, r, p] = await Promise.all([
      get('assets/story.json', true), get('assets/chunks.bin'), get('assets/spirit.bin'), get('assets/poses.bin')
    ]);
    M = m; poses = new Float32Array(p); points = buffer(new Float32Array(c)); reference = buffer(new Float32Array(r));
    document.title = M.title;
    $('seek').max = M.duration;
    await document.fonts.ready;
    $('loading').remove();
    await window.render(0);
    window.storyReady = true;
    requestAnimationFrame(tick);
  } catch (error) {
    window.storyError = error.stack || String(error);
    if ($('loading')) $('loading').textContent = window.storyError;
    console.error(error);
  }
})();
