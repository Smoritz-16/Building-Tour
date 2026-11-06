(function() {
 'use strict';
 function U() {
  return String.fromCharCode.apply(null, arguments);
 }
 var CHARSETS = {
  standard: ' .:-=+*#%@',
  blocks: ' .:' + U(9617, 9618, 9619, 9608) + '',
  dots: ' .' + U(183) + ':' + U(8226) + '',
  binary: ' 01',
  donut: ' .,-~:;=!*#$@',
  photo: " .'" + '`^",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$',
  bars: ' ' + U(9601, 9602, 9603, 9604, 9605, 9606, 9607, 9608) + '',
  shade: ' ' + U(9617, 9618, 9619, 9608) + '',
  braille: ' ' + U(10241, 10243, 10247, 10311, 10319, 10335, 10367, 10495) + '',
  stars: ' .' + U(183) + '*' + U(10022, 9733) + '',
  circles: ' .' + U(183, 8728, 9675, 9679) + ''
 };
 var MATRIX_GLYPHS = '' + U(65393, 65394, 65395, 65396, 65397, 65398, 65399, 65400, 65401, 65402, 65403, 65404, 65405, 65406, 65407, 65408, 65409, 65410, 65411, 65412, 65413, 65414, 65415, 65416, 65417, 65418, 65419, 65420, 65421, 65422) + '0123456789<>=*+-/' + U(92) + '|:;ABCDEFGHKLMNPRSTUXYZ';
 var COLOURS = {
  phosphor: {
   bg: '#05080a',
   ink: [ 57, 255, 122 ]
  },
  amber: {
   bg: '#0a0600',
   ink: [ 255, 176, 38 ]
  },
  paper: {
   bg: '#e4e6e0',
   ink: [ 18, 40, 24 ],
   paper: true
  },
  spectrum: {
   bg: '#05060a',
   stops: [ [ 60, 8, 90 ], [ 40, 60, 220 ], [ 20, 210, 200 ], [ 120, 230, 40 ], [ 255, 210, 20 ], [ 255, 70, 40 ] ]
  },
  fire: {
   bg: '#05030a',
   stops: [ [ 6, 2, 8 ], [ 120, 12, 6 ], [ 210, 40, 6 ], [ 255, 120, 16 ], [ 255, 210, 70 ], [ 255, 255, 235 ] ]
  },
  ice: {
   bg: '#03060c',
   stops: [ [ 2, 4, 12 ], [ 10, 30, 90 ], [ 20, 90, 200 ], [ 40, 170, 235 ], [ 150, 225, 250 ], [ 245, 252, 255 ] ]
  },
  neon: {
   bg: '#06030a',
   stops: [ [ 10, 4, 14 ], [ 210, 30, 190 ], [ 150, 30, 210 ], [ 40, 140, 235 ], [ 40, 232, 228 ], [ 156, 247, 46 ] ]
  }
 };
 var LOOKS = {
  Neo: {
   e: 'matrix',
   k: 'phosphor',
   sp: 120,
   ce: 12
  },
  Solaris: {
   e: 'donut',
   c: 'donut',
   k: 'amber',
   sp: 90,
   ce: 11
  },
  Blueprint: {
   e: 'plasma',
   c: 'blocks',
   k: 'paper',
   sp: 80,
   ce: 12
  },
  Mono: {
   e: 'donut',
   c: 'standard',
   k: 'paper',
   sp: 70,
   ce: 10
  },
  Signal: {
   e: 'plasma',
   c: 'binary',
   k: 'phosphor',
   sp: 140,
   ce: 10
  },
  Ember: {
   e: 'matrix',
   c: 'standard',
   k: 'amber',
   sp: 100,
   ce: 12
  },
  Inferno: {
   c: 'standard',
   k: 'fire',
   sp: 160,
   ce: 11
  },
  Drift: {
   c: 'standard',
   k: 'spectrum',
   sp: 55,
   ce: 10
  },
  Aurora: {
   c: 'blocks',
   k: 'ice',
   sp: 80,
   ce: 12
  },
  Voltage: {
   c: 'photo',
   k: 'neon',
   sp: 170,
   ce: 10
  },
  Noir: {
   c: 'standard',
   k: 'paper',
   sp: 50,
   ce: 11
  }
 };
 function clamp01(v) {
  return v < 0 ? 0 : v > 1 ? 1 : v;
 }
 function gradient(stops, l) {
  var n = stops.length - 1, x = clamp01(l) * n, i = Math.min(n - 1, Math.floor(x)), f = x - i;
  var a = stops[i], b = stops[i + 1];
  return [ Math.round(a[0] + (b[0] - a[0]) * f), Math.round(a[1] + (b[1] - a[1]) * f), Math.round(a[2] + (b[2] - a[2]) * f) ];
 }
 function glyph(ramp, l) {
  var idx = Math.round(clamp01(l) * (ramp.length - 1));
  return ramp.charAt(idx);
 }
 var ENGINES = {
  plasma: function(st, t) {
   for (var y = 0; y < st.rows; y++) for (var x = 0; x < st.cols; x++) {
    var u = x / st.cols * 6, v = y / st.rows * 6;
    var s = Math.sin(u + t) + Math.sin(v * 1.3 - t * .8) + Math.sin((u + v) * .7 + t * .6) + Math.sin(Math.sqrt((u - 3) * (u - 3) + (v - 3) * (v - 3)) * 1.5 - t);
    st.lum[y * st.cols + x] = (s + 4) / 8;
   }
  },
  donut: function(st, t) {
   var cols = st.cols, rows = st.rows, lum = st.lum, z = st.zbuf;
   lum.fill(0);
   z.fill(0);
   var A = t * .8, B = t * .4, cA = Math.cos(A), sA = Math.sin(A), cB = Math.cos(B), sB = Math.sin(B);
   var K1 = Math.min(cols, rows * 2) * .35 * 5 / 3;
   for (var th = 0; th < 6.283; th += .07) {
    var ct = Math.cos(th), stt = Math.sin(th);
    for (var ph = 0; ph < 6.283; ph += .02) {
     var cp = Math.cos(ph), sp = Math.sin(ph);
     var cx = 2 + ct, cy = stt;
     var x = cx * (cB * cp + sA * sB * sp) - cy * cA * sB;
     var y = cx * (sB * cp - sA * cB * sp) + cy * cA * cB;
     var zz = 5 + cA * cx * sp + cy * sA, ooz = 1 / zz;
     var xp = Math.floor(cols / 2 + K1 * ooz * x);
     var yp = Math.floor(rows / 2 - K1 * ooz * y * .5);
     if (xp < 0 || xp >= cols || yp < 0 || yp >= rows) continue;
     var L = cp * ct * sB - cA * ct * sp - sA * stt + cB * (cA * stt - ct * sA * sp);
     var i = yp * cols + xp;
     if (ooz > z[i]) {
      z[i] = ooz;
      lum[i] = L > 0 ? Math.min(1, .15 + L / 1.5) : .08;
     }
    }
   }
  },
  matrix: function(st, t, dt) {
   var cols = st.cols, rows = st.rows;
   if (!st.drops || st.drops.length !== cols) {
    st.drops = [];
    for (var c = 0; c < cols; c++) st.drops.push(Math.random() * rows);
    st.trail = new Float32Array(cols * rows);
    st.chars = [];
    for (var k = 0; k < cols * rows; k++) st.chars.push(MATRIX_GLYPHS.charAt(Math.random() * MATRIX_GLYPHS.length | 0));
   }
   for (var j = 0; j < st.trail.length; j++) st.trail[j] *= Math.pow(.88, dt * 60);
   for (var x = 0; x < cols; x++) {
    st.drops[x] += dt * 18 * (.6 + x * 7919 % 10 / 20);
    if (st.drops[x] > rows + 10) st.drops[x] = -Math.random() * 20;
    var yy = Math.floor(st.drops[x]);
    if (yy >= 0 && yy < rows) {
     st.trail[yy * cols + x] = 1;
     if (Math.random() < .3) st.chars[yy * cols + x] = MATRIX_GLYPHS.charAt(Math.random() * MATRIX_GLYPHS.length | 0);
    }
   }
   st.lum.set(st.trail);
  },
  fire: function(st, t, dt) {
   var cols = st.cols, rows = st.rows;
   if (!st.heat || st.heat.length !== cols * rows) st.heat = new Float32Array(cols * rows);
   var h = st.heat;
   for (var x = 0; x < cols; x++) h[(rows - 1) * cols + x] = .7 + Math.random() * .3;
   for (var y = 0; y < rows - 1; y++) for (var x2 = 0; x2 < cols; x2++) {
    var src = Math.min(cols - 1, Math.max(0, x2 + (Math.random() * 3 | 0) - 1));
    var v = h[(y + 1) * cols + src] - Math.random() * (1.8 / rows);
    h[y * cols + x2] = v < 0 ? 0 : v;
   }
   st.lum.set(h);
  },
  image: function(st) {
   if (!st.imgData) {
    st.lum.fill(0);
    return;
   }
   st.lum.set(st.imgData);
  }
 };
 function AsciiFX(canvas, opts) {
  opts = opts || {};
  var d = canvas.dataset;
  var look = LOOKS[opts.look || d.look] || {};
  this.canvas = canvas;
  this.ctx = canvas.getContext('2d');
  this.engine = opts.engine || d.engine || look.e || (d.image || opts.image ? 'image' : 'plasma');
  this.charset = opts.charset || d.charset || look.c || 'standard';
  this.colour = opts.colour || d.colour || look.k || 'phosphor';
  this.speed = +(opts.speed || d.speed || look.sp || 100);
  this.cell = +(opts.cell || d.cell || look.ce || 12);
  this.contrast = +(opts.contrast || d.contrast || 100);
  this.transparent = (opts.bg || d.bg) === 'none';
  this.st = {};
  this.t = 0;
  this.reduced = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var self = this, img = opts.image || d.image;
  if (img) this.loadImage(img);
  this.resize();
  if (typeof ResizeObserver === 'function') new ResizeObserver(function() {
   self.resize();
  }).observe(canvas);
  this.last = 0;
  this.frame = function(now) {
   var dt = self.last ? Math.min(.1, (now - self.last) / 1e3) : 1 / 60;
   self.last = now;
   if (!self.reduced) self.t += dt * self.speed / 100;
   self.render(dt);
   if (!self.reduced) self.raf = requestAnimationFrame(self.frame);
  };
  this.raf = requestAnimationFrame(this.frame);
 }
 AsciiFX.prototype.resize = function() {
  var r = this.canvas.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  this.w = Math.max(1, r.width);
  this.h = Math.max(1, r.height);
  this.canvas.width = Math.round(this.w * dpr);
  this.canvas.height = Math.round(this.h * dpr);
  this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  var st = this.st;
  st.cw = this.cell * .6;
  st.ch = this.cell;
  st.cols = Math.max(1, Math.floor(this.w / st.cw));
  st.rows = Math.max(1, Math.floor(this.h / st.ch));
  st.lum = new Float32Array(st.cols * st.rows);
  st.zbuf = new Float32Array(st.cols * st.rows);
  st.drops = null;
  st.heat = null;
  if (this.img) this.sampleImage();
  if (this.reduced) this.render(0);
 };
 AsciiFX.prototype.loadImage = function(src) {
  var self = this, im = new Image;
  im.crossOrigin = 'anonymous';
  im.onload = function() {
   self.img = im;
   self.sampleImage();
   if (self.reduced) self.render(0);
  };
  im.src = src;
 };
 AsciiFX.prototype.sampleImage = function() {
  var st = this.st, c = document.createElement('canvas');
  c.width = st.cols;
  c.height = st.rows;
  var x = c.getContext('2d'), im = this.img;
  var s = Math.max(this.w / im.width, this.h / im.height);
  var w = im.width * s / st.cw, h = im.height * s / st.ch;
  x.drawImage(im, (st.cols - w) / 2, (st.rows - h) / 2, w, h);
  var px = x.getImageData(0, 0, st.cols, st.rows).data, out = new Float32Array(st.cols * st.rows);
  for (var i = 0; i < out.length; i++) out[i] = (.2126 * px[i * 4] + .7152 * px[i * 4 + 1] + .0722 * px[i * 4 + 2]) / 255;
  st.imgData = out;
 };
 AsciiFX.prototype.render = function(dt) {
  var st = this.st, ctx = this.ctx, pal = COLOURS[this.colour] || COLOURS.phosphor;
  var ramp = CHARSETS[this.charset] || CHARSETS.standard, gamma = 100 / this.contrast;
  (ENGINES[this.engine] || ENGINES.plasma)(st, this.t, dt || 1 / 60);
  if (this.transparent) ctx.clearRect(0, 0, this.w, this.h); else {
   ctx.fillStyle = pal.bg;
   ctx.fillRect(0, 0, this.w, this.h);
  }
  ctx.font = st.ch + 'px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';
  ctx.textBaseline = 'top';
  var isMatrix = this.engine === 'matrix', lastCol = '';
  for (var y = 0; y < st.rows; y++) for (var x = 0; x < st.cols; x++) {
   var i = y * st.cols + x, l = Math.pow(clamp01(st.lum[i]), gamma);
   if (pal.paper && this.engine === 'image') l = 1 - l;
   if (l < .02) continue;
   var ch = isMatrix ? st.chars[i] : glyph(ramp, l);
   if (ch === ' ') continue;
   var rgb = pal.stops ? gradient(pal.stops, l) : pal.ink;
   var a = pal.stops ? 1 : .25 + .75 * l;
   var col = 'rgba(' + rgb[0] + ',' + rgb[1] + ',' + rgb[2] + ',' + a.toFixed(2) + ')';
   if (col !== lastCol) {
    ctx.fillStyle = col;
    lastCol = col;
   }
   ctx.fillText(ch, x * st.cw, y * st.ch);
  }
 };
 AsciiFX.prototype.set = function(opts) {
  var look = LOOKS[opts.look] || {};
  if (look.e || opts.engine) this.engine = opts.engine || look.e;
  if (look.c || opts.charset) this.charset = opts.charset || look.c;
  if (look.k || opts.colour) this.colour = opts.colour || look.k;
  if (look.sp || opts.speed) this.speed = +(opts.speed || look.sp);
  if (look.ce || opts.cell) {
   this.cell = +(opts.cell || look.ce);
   this.resize();
  }
  if (opts.contrast) this.contrast = +opts.contrast;
  if (this.reduced) this.render(0);
 };
 AsciiFX.prototype.destroy = function() {
  cancelAnimationFrame(this.raf);
 };
 AsciiFX.CHARSETS = CHARSETS;
 AsciiFX.COLOURS = COLOURS;
 AsciiFX.LOOKS = LOOKS;
 AsciiFX._gradient = gradient;
 AsciiFX._glyph = glyph;
 AsciiFX._ENGINES = ENGINES;
 if (typeof window !== 'undefined') {
  window.AsciiFX = AsciiFX;
  var boot = function() {
   var els = document.querySelectorAll('canvas.ascii-fx');
   for (var i = 0; i < els.length; i++) if (!els[i]._asciiFx) els[i]._asciiFx = new AsciiFX(els[i]);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
 }
 if (typeof module !== 'undefined') module.exports = AsciiFX;
})();