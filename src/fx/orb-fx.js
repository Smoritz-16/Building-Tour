(function() {
 'use strict';
 var BASE = {
  speed: 1,
  radius: .72,
  zoom: .3,
  warp: 3,
  ridgeAmt: .5,
  sharp: 2.2,
  shade: .3,
  sheen: .36,
  gloss: .28,
  glassOpacity: .42,
  exposure: 1,
  style: 0
 };
 function P(o) {
  var r = {}, k;
  for (k in BASE) r[k] = BASE[k];
  for (k in o) r[k] = o[k];
  return r;
 }
 var ORBS = {
  siri: P({
   name: 'Siri Wave',
   speed: .82,
   zoom: .36,
   warp: 3.2,
   ridgeAmt: .5,
   sharp: 2.2,
   shade: .12,
   sheen: .28,
   gloss: .24,
   glassOpacity: .44,
   exposure: 2,
   colors: [ '#FFD86B', '#82F4FF', '#FF7BD5', '#8E6CFF' ],
   shellMid: '#9BF4FF',
   shellEdge: '#C5A9FF',
   canvas: '#030409',
   glow: '#956CFF'
  }),
  voiceWave: P({
   name: 'Voice Membrane',
   speed: .95,
   radius: .7,
   zoom: .36,
   warp: 2.6,
   ridgeAmt: .46,
   shade: .08,
   sheen: .22,
   gloss: .36,
   glassOpacity: .48,
   exposure: 1.35,
   colors: [ '#09030E', '#CE2CCB', '#FF5C71', '#7B53FF' ],
   shellMid: '#E48BFF',
   shellEdge: '#FF7890',
   canvas: '#020105',
   glow: '#CE2CCB'
  }),
  particleRibbon: P({
   name: 'Particle Ribbons',
   style: 1,
   speed: .72,
   radius: .66,
   shade: .12,
   sheen: .28,
   gloss: .24,
   glassOpacity: .44,
   exposure: 1.48,
   colors: [ '#63F1FF', '#4A9DFF', '#8566FF', '#F15DE1' ],
   shellMid: '#9BF4FF',
   shellEdge: '#C5A9FF',
   canvas: '#010208',
   glow: '#765CFF'
  }),
  blueDrop: P({
   name: 'Crystal Drop',
   speed: .9,
   radius: .74,
   zoom: .48,
   warp: 2.65,
   ridgeAmt: .42,
   sharp: 2.4,
   shade: .16,
   sheen: .22,
   gloss: .42,
   glassOpacity: .66,
   exposure: 1.24,
   colors: [ '#020B1D', '#0756B8', '#1EC8FF', '#DDFBFF' ],
   shellMid: '#4FD7FF',
   shellEdge: '#466DFF',
   canvas: '#010207',
   glow: '#168DFF'
  }),
  violetEmber: P({
   name: 'Violet Ember',
   speed: 1.12,
   radius: .72,
   zoom: .58,
   warp: 4.7,
   ridgeAmt: .73,
   sharp: 3.3,
   shade: .18,
   sheen: .2,
   gloss: .34,
   glassOpacity: .62,
   exposure: 1.28,
   colors: [ '#100016', '#4A0E8F', '#A52EFF', '#F1A7FF' ],
   shellMid: '#C257FF',
   shellEdge: '#6C2DFF',
   canvas: '#030006',
   glow: '#A52EFF'
  }),
  refractiveBlob: P({
   name: 'Refractive Gel',
   speed: .76,
   radius: .73,
   zoom: .46,
   warp: 3.65,
   ridgeAmt: .58,
   sharp: 2.7,
   shade: .14,
   sheen: .14,
   gloss: .52,
   glassOpacity: .82,
   exposure: 1.2,
   colors: [ '#1B102B', '#7056A8', '#BFA5F5', '#F1E8FF' ],
   shellMid: '#D9C7FF',
   shellEdge: '#B59AE8',
   canvas: '#050208',
   glow: '#B18CFF'
  }),
  chromaticMetal: P({
   name: 'Chromatic Metal',
   style: 2,
   speed: 1.12,
   radius: .72,
   shade: .1,
   sheen: .14,
   gloss: .46,
   glassOpacity: .54,
   exposure: 1.08,
   colors: [ '#FBFCFB', '#7F8683', '#D6DAD8', '#33373A' ],
   shellMid: '#6EDCFF',
   shellEdge: '#FF806D',
   canvas: '#050606',
   glow: '#BDEFFF'
  }),
  aurora: P({
   name: 'Aurora Veil',
   speed: 3,
   zoom: .4,
   warp: 4.2,
   ridgeAmt: .62,
   sharp: 2.1,
   shade: .18,
   exposure: 1.18,
   colors: [ '#030816', '#20F0B6', '#32A8FF', '#A34BFF' ],
   shellMid: '#32A8FF',
   shellEdge: '#20F0B6',
   canvas: '#010207',
   glow: '#20F0B6'
  }),
  frost: P({
   name: 'Frost Flow',
   speed: 2.22,
   zoom: .36,
   warp: 3.7,
   ridgeAmt: .45,
   sharp: 2.05,
   shade: .3,
   sheen: .34,
   gloss: .28,
   glassOpacity: .42,
   exposure: 1,
   colors: [ '#F7FBFF', '#D6E8F7', '#A8C8F0', '#6F9EE8' ],
   shellMid: '#D6E8F7',
   shellEdge: '#6F9EE8',
   canvas: '#000000',
   glow: '#6F9EE8'
  }),
  chrome: P({
   name: 'Liquid Chrome',
   speed: 2,
   zoom: .36,
   warp: 3.8,
   ridgeAmt: .44,
   sharp: 5.2,
   shade: .58,
   exposure: 1.08,
   colors: [ '#FFFFFF', '#B9C0CA', '#343A43', '#030405' ],
   shellMid: '#B9C0CA',
   shellEdge: '#FFFFFF',
   canvas: '#050608',
   glow: '#FFFFFF'
  }),
  opal: P({
   name: 'Iridescent Opal',
   speed: 1.5,
   zoom: .3,
   warp: 2.8,
   ridgeAmt: .36,
   sharp: 2,
   shade: .1,
   sheen: .3,
   gloss: .26,
   glassOpacity: .38,
   exposure: 1.12,
   colors: [ '#FFF6E8', '#6EF2CF', '#FF91D8', '#756BFF' ],
   shellMid: '#CDE5FF',
   shellEdge: '#D9C8FF',
   canvas: '#07080D',
   glow: '#9E8CFF'
  }),
  spectrum: P({
   name: 'Prismatic Field',
   speed: 1.8,
   zoom: .46,
   warp: 4.4,
   ridgeAmt: .72,
   shade: .06,
   sheen: .26,
   gloss: .24,
   glassOpacity: .4,
   exposure: 1.5,
   colors: [ '#FFFFFF', '#1677FF', '#F249A0', '#35E6B2' ],
   shellMid: '#66E8FF',
   shellEdge: '#D26CFF',
   canvas: '#03040A',
   glow: '#1677FF'
  }),
  plasma: P({
   name: 'Neural Plasma',
   speed: 1.32,
   zoom: .55,
   warp: 5.4,
   ridgeAmt: .78,
   sharp: 4.2,
   shade: .16,
   exposure: 1.25,
   colors: [ '#06020E', '#0099FF', '#258BFF', '#1375FF' ],
   shellMid: '#1951C2',
   shellEdge: '#00E9FF',
   canvas: '#020105',
   glow: '#0099FF'
  })
 };
 var VS = 'attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}';
 var FS = [ 'precision highp float;', 'uniform vec2 res;uniform float t,radius,zoom,warp,ridgeAmt,sharp,shade,sheen,gloss,glassOp,expo,style,transparent;', 'uniform vec3 cA,cB,cC,cD,shellMid,shellEdge,canvasCol,glowCol;', 'float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}', 'float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}', 'float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<5;i++){v+=a*n(p);p=mat2(1.6,1.2,-1.2,1.6)*p;a*=.5;}return v;}', 'vec3 pal(float x){x=clamp(x,0.,1.)*3.;if(x<1.)return mix(cA,cB,x);if(x<2.)return mix(cB,cC,x-1.);return mix(cC,cD,x-2.);}', 'vec3 fluid(vec2 p){', '  vec2 q=p*(1.5+zoom*4.);', '  float f;', '  if(style>1.5){vec2 r=mat2(.42,-.91,.91,.42)*q;r.x*=.35;f=fbm(r*2.+vec2(t*.3,0.));f=.5+.5*sin(f*12.+r.y*3.+t);}', '  else if(style>.5){vec3 acc=vec3(0.);for(int i=0;i<4;i++){float fi=float(i);float y=sin(q.x*1.3+t*(.6+fi*.2)+fi*1.7)*.55+(fi-1.5)*.25;float d=abs(q.y-y);float g=smoothstep(.12,0.,d)*(.55+.45*n(q*9.+t*2.))+exp(-d*18.)*.35;acc+=pal(fi/3.)*g;}return acc*1.3;}', '  else{vec2 w=vec2(fbm(q+t*.15),fbm(q+vec2(5.2,1.3)-t*.12));f=fbm(q+warp*.6*w);}', '  float ridge=pow(1.-abs(sin(f*6.2832)),sharp)*ridgeAmt;', '  vec3 c=pal(f*1.15-.05)+ridge*.5*pal(.95);', '  return c;}', 'void main(){', '  vec2 p=(gl_FragCoord.xy-.5*res)/min(res.x,res.y)*2.;', '  float r=length(p)/radius;', '  float px=2./min(res.x,res.y)/radius;', '  float inside=smoothstep(1.,1.-px*1.5,r);', '  float glow=exp(-max(r-1.,0.)*6.)*.35*(1.-inside);', '  vec3 bg=transparent>.5?vec3(0.):canvasCol;', '  float rr=min(r,1.);', '  float refr=glassOp*.35*pow(rr,3.);', '  vec2 dir=p/max(length(p),1e-4);', '  vec3 col=vec3(fluid(p/radius-dir*refr*1.1).r,fluid(p/radius-dir*refr).g,fluid(p/radius-dir*refr*.9).b);', '  col*=1.-shade*rr*rr;', '  col=1.-exp(-col*expo*1.15);', '  float rim=smoothstep(.72,1.,rr);', '  col=mix(col,col+shellMid*.5,rim*glassOp*.5);', '  col+=shellEdge*pow(rim,4.)*glassOp*.8;', '  vec2 k=p/radius-vec2(-.38,.42);', '  col+=vec3(1.)*exp(-dot(k,k)*14.)*gloss*1.2;', '  col+=vec3(1.)*smoothstep(.02,0.,abs(rr-.93))*sheen*.35*(.5+.5*dir.y);', '  vec3 outc=mix(bg,col,inside)+glowCol*glow;', '  float alpha=transparent>.5?max(inside,glow):1.;', '  gl_FragColor=vec4(outc,alpha);', '}' ].join(' ');
 function hex(c) {
  var v = parseInt(c.slice(1), 16);
  return [ (v >> 16 & 255) / 255, (v >> 8 & 255) / 255, (v & 255) / 255 ];
 }
 function OrbFX(canvas, opts) {
  opts = opts || {};
  var d = canvas.dataset, self = this;
  this.canvas = canvas;
  this.p = ORBS[opts.orb || d.orb] || ORBS.siri;
  this.mult = +(opts.speed || d.speed || 1);
  this.transparent = (opts.bg || d.bg) === 'none';
  var gl = canvas.getContext('webgl', {
   premultipliedAlpha: false,
   alpha: true,
   antialias: true
  });
  if (!gl) {
   this.fallback();
   return;
  }
  this.gl = gl;
  function sh(type, src) {
   var s = gl.createShader(type);
   gl.shaderSource(s, src);
   gl.compileShader(s);
   if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
   return s;
  }
  var pr = gl.createProgram();
  gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS));
  gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS));
  gl.linkProgram(pr);
  gl.useProgram(pr);
  this.pr = pr;
  var b = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, b);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([ -1, -1, 1, -1, -1, 1, 1, 1 ]), gl.STATIC_DRAW);
  var loc = gl.getAttribLocation(pr, 'a');
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  this.u = {};
  var names = [ 'res', 't', 'radius', 'zoom', 'warp', 'ridgeAmt', 'sharp', 'shade', 'sheen', 'gloss', 'glassOp', 'expo', 'style', 'transparent', 'cA', 'cB', 'cC', 'cD', 'shellMid', 'shellEdge', 'canvasCol', 'glowCol' ];
  for (var i = 0; i < names.length; i++) this.u[names[i]] = gl.getUniformLocation(pr, names[i]);
  this.reduced = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  this.t = 0;
  this.last = 0;
  this.resize();
  if (typeof ResizeObserver === 'function') new ResizeObserver(function() {
   self.resize();
  }).observe(canvas);
  this.frame = function(now) {
   var dt = self.last ? Math.min(.1, (now - self.last) / 1e3) : 0;
   self.last = now;
   if (!self.reduced) self.t += dt * self.p.speed * self.mult * .35;
   self.draw();
   if (!self.reduced) self.raf = requestAnimationFrame(self.frame);
  };
  this.raf = requestAnimationFrame(this.frame);
 }
 OrbFX.prototype.resize = function() {
  var r = this.canvas.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1);
  this.canvas.width = Math.max(1, Math.round(r.width * dpr));
  this.canvas.height = Math.max(1, Math.round(r.height * dpr));
  if (this.gl) {
   this.gl.viewport(0, 0, this.canvas.width, this.canvas.height);
   if (this.reduced) this.draw();
  }
 };
 OrbFX.prototype.draw = function() {
  var gl = this.gl, u = this.u, p = this.p;
  gl.uniform2f(u.res, this.canvas.width, this.canvas.height);
  gl.uniform1f(u.t, this.t + 3.7);
  gl.uniform1f(u.radius, p.radius);
  gl.uniform1f(u.zoom, p.zoom);
  gl.uniform1f(u.warp, p.warp);
  gl.uniform1f(u.ridgeAmt, p.ridgeAmt);
  gl.uniform1f(u.sharp, p.sharp);
  gl.uniform1f(u.shade, p.shade);
  gl.uniform1f(u.sheen, p.sheen);
  gl.uniform1f(u.gloss, p.gloss);
  gl.uniform1f(u.glassOp, p.glassOpacity);
  gl.uniform1f(u.expo, p.exposure);
  gl.uniform1f(u.style, p.style);
  gl.uniform1f(u.transparent, this.transparent ? 1 : 0);
  gl.uniform3fv(u.cA, hex(p.colors[0]));
  gl.uniform3fv(u.cB, hex(p.colors[1]));
  gl.uniform3fv(u.cC, hex(p.colors[2]));
  gl.uniform3fv(u.cD, hex(p.colors[3]));
  gl.uniform3fv(u.shellMid, hex(p.shellMid));
  gl.uniform3fv(u.shellEdge, hex(p.shellEdge));
  gl.uniform3fv(u.canvasCol, hex(p.canvas));
  gl.uniform3fv(u.glowCol, hex(p.glow));
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
 };
 OrbFX.prototype.set = function(opts) {
  if (opts.orb && ORBS[opts.orb]) this.p = ORBS[opts.orb];
  if (opts.speed) this.mult = +opts.speed;
  if (this.reduced) this.draw();
 };
 OrbFX.prototype.fallback = function() {
  var p = this.p, c = this.canvas;
  c.style.background = 'radial-gradient(circle at 35% 30%, ' + p.colors[3] + ', ' + p.colors[2] + ' 30%, ' + p.colors[1] + ' 55%, ' + p.colors[0] + ' 70%, ' + p.canvas + ' 71%)';
 };
 OrbFX.prototype.destroy = function() {
  cancelAnimationFrame(this.raf);
 };
 OrbFX.ORBS = ORBS;
 if (typeof window !== 'undefined') {
  window.OrbFX = OrbFX;
  var boot = function() {
   var els = document.querySelectorAll('canvas.orb-fx');
   for (var i = 0; i < els.length; i++) if (!els[i]._orbFx) els[i]._orbFx = new OrbFX(els[i]);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
 }
 if (typeof module !== 'undefined') module.exports = OrbFX;
})();