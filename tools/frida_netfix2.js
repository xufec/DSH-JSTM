// Frida: intercept the SDK's HTTP at the concrete Android classes
// (com.android.okhttp.internal.huc.*), and force init listeners to succeed.
Java.perform(function () {
  function L(m) { console.log('[DSH] ' + m); }
  var FAKE = '{"code":0,"message":"ok","msg":"ok","result":1,"data":{},"status":0,"ret":0}';

  function toBytes(s) {
    var b = [];
    for (var i = 0; i < s.length; i++) b.push(s.charCodeAt(i) & 0xff);
    return Java.array('byte', b);
  }

  function isTarget(u) { return /superv|superdata|cwmob|ewan\.cn|123cw/i.test(u); }

  function intercept(cls) {
    try {
      var C = Java.use(cls);
      try {
        C.getResponseCode.implementation = function () {
          var u = ''; try { u = this.getURL().toString(); } catch (e) {}
          if (isTarget(u)) { L('fake 200 <- ' + u); return 200; }
          return this.getResponseCode();
        };
      } catch (e) {}
      try {
        C.getInputStream.implementation = function () {
          var u = ''; try { u = this.getURL().toString(); } catch (e) {}
          if (isTarget(u)) {
            L('fake body <- ' + u);
            return Java.use('java.io.ByteArrayInputStream').$new(toBytes(FAKE));
          }
          return this.getInputStream();
        };
      } catch (e) {}
      try {
        C.getContentLength.implementation = function () {
          var u = ''; try { u = this.getURL().toString(); } catch (e) {}
          if (isTarget(u)) return FAKE.length;
          return this.getContentLength();
        };
      } catch (e) {}
      L('intercepted ' + cls);
    } catch (e) { L('intercept ' + cls + ' failed: ' + e); }
  }

  ['com.android.okhttp.internal.huc.HttpURLConnectionImpl',
   'com.android.okhttp.internal.huc.HttpsURLConnectionImpl',
   'java.net.HttpURLConnection',
   'javax.net.ssl.HttpsURLConnection'].forEach(intercept);

  var hooked = {};
  function hookClass(name) {
    var c; try { c = Java.use(name); } catch (e) { return; }
    ['onFail', 'onSuccess'].forEach(function (m) {
      var ovs; try { ovs = c[m].overloads; } catch (e) { return; }
      for (var i = 0; i < ovs.length; i++) {
        (function (ov, mm, cls) {
          ov.implementation = function () {
            var args = Array.prototype.slice.call(arguments).join(' | ');
            L('CALLBACK ' + mm + ' @' + cls + ' [' + args + ']');
            if (mm === 'onFail') { try { L('  -> onSuccess'); return this.onSuccess(); } catch (e) { L('  err ' + e); } }
            return ov.apply(this, arguments);
          };
        })(ovs[i], m, name);
      }
    });
  }
  function poll() {
    try {
      Java.enumerateLoadedClassesSync().forEach(function (n) {
        if (!hooked[n] && /^cn\.ewan\.supersdk\./.test(n)) { hooked[n] = 1; hookClass(n); }
      });
    } catch (e) {}
  }
  poll();
  var t = setInterval(poll, 300);
  setTimeout(function () { clearInterval(t); }, 120000);
  L('netfix2 armed');
});
