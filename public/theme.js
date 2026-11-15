(function () {
  function start() {
    if (!document.querySelector('link[href="/theme.css"]')) { var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = '/theme.css'; document.head.appendChild(l); }
    // ----- animated starfield with shooting stars -----
    var c = document.createElement('canvas');
    c.id = 'pxStars';
    document.body.prepend(c);
    var x = c.getContext('2d'), stars = [], shots = [];
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    function size() {
      c.width = innerWidth; c.height = innerHeight; stars = [];
      var n = Math.floor(c.width * c.height / 9000);
      for (var i = 0; i < n; i++) stars.push({ x: Math.random() * c.width, y: Math.random() * c.height, r: Math.random() * 1.6 + .3, s: Math.random() * 2 + .5, p: Math.random() * 6, d: Math.random() * .05 + .01 });
    }
    function frame(t) {
      x.clearRect(0, 0, c.width, c.height);
      stars.forEach(function (s) {
        var a = .35 + .65 * Math.abs(Math.sin(t / 1000 * s.s + s.p));
        x.fillStyle = 'rgba(255,255,255,' + a.toFixed(2) + ')';
        x.beginPath(); x.arc(s.x, s.y, s.r, 0, 6.2832); x.fill();
        if (!reduce) { s.x -= s.d; if (s.x < 0) s.x = c.width; }
      });
      if (!reduce && Math.random() < .008) shots.push({ x: Math.random() * c.width, y: Math.random() * c.height * .5, vx: -8 - Math.random() * 5, vy: 4 + Math.random() * 3, l: 1 });
      shots = shots.filter(function (s) {
        x.strokeStyle = 'rgba(180,230,255,' + s.l + ')'; x.lineWidth = 2;
        x.beginPath(); x.moveTo(s.x, s.y); x.lineTo(s.x - s.vx * 5, s.y - s.vy * 5); x.stroke();
        s.x += s.vx; s.y += s.vy; s.l -= .02; return s.l > 0;
      });
      if (!reduce) requestAnimationFrame(frame);
    }
    size(); addEventListener('resize', size); requestAnimationFrame(frame);

    // ----- shared navigation -----
    var links = [
      ['/index.html#explorer', 'Sky Explorer'], ['/index.html#moving', 'Moving Objects'],
      ['/simulator.html', 'Planet X Simulator'], ['/tracker.html', 'Satellite Tracker'],
      ['/spaceweather.html', 'Space Weather'], ['/index.html#about', 'About']
    ];
    document.querySelectorAll('nav').forEach(function (n) { n.remove(); });
    var nav = document.createElement('nav');
    nav.className = 'pxnav';
    links.forEach(function (l, i) {
      var a = document.createElement('a');
      a.href = l[0]; a.textContent = l[1]; a.className = 'n' + (i + 1);
      if (l[0].indexOf('#') < 0 && location.pathname === l[0]) a.classList.add('active');
      nav.appendChild(a);
    });
    document.body.prepend(nav);

    // ----- AI assistant (reads its answers from index.html) -----
    if (document.getElementById('pxBtn')) return;
    fetch('/index.html').then(function (r) { return r.text(); }).then(function (html) {
      var part = html.split('// ---------- PROJECT ASSISTANT ----------')[1];
      if (!part) throw new Error('assistant code not found in index.html');
      var code = part.split('</script>')[0];
      var wrap = document.createElement('div');
      wrap.innerHTML =
        '<div id="pxBubble">Ask me! 👋</div>' +
        '<button id="pxBtn" title="Ask the Planet X assistant">💬 Ask AI Assistant</button>' +
        '<div id="pxBox"><div id="pxHead">🤖 Planet X Assistant</div><div id="pxMsgs"></div><div id="pxChips"></div>' +
        '<div id="pxForm"><input id="pxInput" placeholder="Ask about any module..." autocomplete="off"><button id="pxSend">Send</button></div></div>';
      while (wrap.firstChild) document.body.appendChild(wrap.firstChild);
      new Function(code)();
    }).catch(function (e) { console.error('Assistant failed:', e); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();

