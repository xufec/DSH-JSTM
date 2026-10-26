// Frida: resolve the dead game/SDK domains to our server, and make the SDK's
// init HTTP requests answer successfully.
Java.perform(function () {
  function L(m) { console.log('[DSH] ' + m); }
  var IP = '10.16.153.137';
  var PATS = /ewan\.cn|cwmob\.cn|123cw\.cn|shiyuegame\.com|jstm/i;

  // ---- 1) DNS override ----
  try {
    var IA = Java.use('java.net.InetAddress');
    IA.getAllByName.overload('java.lang.String').implementation = function (h) {
      if (PATS.test(h)) {
        L('DNS getAllByName ' + h + ' -> ' + IP);
        return Java.array('java.net.InetAddress', [IA.getByName(IP)]);
      }
      return this.getAllByName(h);
    };
    IA.getByName.overload('java.lang.String').implementation = function (h) {
      if (PATS.test(h)) {
        L('DNS getByName ' + h + ' -> ' + IP);
        return IA.getByName(IP);
      }
      return this.getByName(h);
    };
    L('DNS override installed');
  } catch (e) { L('DNS hook failed: ' + e); }

  // ---- 2) fake HTTP success for SDK endpoints ----
  var FAKE = '{"code":0,"message":"ok","msg":"ok","result":1,"data":{},"status":0,"ret":0}';
  function toBytes(s) { var b = []; for (var i = 0; i < s.length; i++) b.push(s.charCodeAt(i) & 0xff); return Java.array('byte', b); }
  function isTarget(u) { return /superv|superdata|cwmob|ewan\.cn|123cw|jstm/i.test(u); }
  ['com.android.okhttp.internal.huc.HttpURLConnectionImpl',
   'com.android.okhttp.internal.huc.HttpsURLConnectionImpl'].forEach(function (cls) {
    try {
      var C = Java.use(cls);
      C.getResponseCode.implementation = function () {
        var u = ''; try { u = this.getURL().toString(); } catch (e) {}
        if (isTarget(u)) { L('fake 200 <- ' + u); return 200; }
        return this.getResponseCode();
      };
      C.getInputStream.implementation = function () {
        var u = ''; try { u = this.getURL().toString(); } catch (e) {}
        if (isTarget(u)) { L('fake body <- ' + u); return Java.use('java.io.ByteArrayInputStream').$new(toBytes(FAKE)); }
        return this.getInputStream();
      };
      L('intercepted ' + cls);
    } catch (e) {}
  });

  // ---- 3) log listener signatures and force success ----
  var hooked = {};
  function sig(o) { try { return String(o); } catch (e) { return '?'; } }
  function hookClass(name) {
    var c; try { c = Java.use(name); } catch (e) { return; }
    try { c.onSuccess.overloads.forEach(function (o) { L('SIG ' + name + '.onSuccess ' + sig(o)); }); } catch (e) {}
    try { c.onFail.overloads.forEach(function (o) { L('SIG ' + name + '.onFail ' + sig(o)); }); } catch (e) {}
    ['onFail'].forEach(function (m) {
      var ovs; try { ovs = c[m].overloads; } catch (e) { return; }
      for (var i = 0; i < ovs.length; i++) {
        (function (ov, cls) {
          ov.implementation = function () {
            var args = Array.prototype.slice.call(arguments);
            L('onFail @' + cls + ' [' + args.join(' | ') + ']');
            return ov.apply(this, arguments);
          };
        })(ovs[i], name);
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
  L('dnsfix armed');
});
