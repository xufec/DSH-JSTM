// Frida: make the dead ewan superSDK init endpoints answer successfully at the
// Java network layer, and force init listeners to succeed.
Java.perform(function () {
  function L(m) { console.log('[DSH] ' + m); }

  var FAKE = '{"code":0,"message":"ok","msg":"ok","result":1,"data":{},"status":0}';

  function toBytes(s) {
    var b = [];
    for (var i = 0; i < s.length; i++) b.push(s.charCodeAt(i) & 0xff);
    return Java.array('byte', b);
  }

  function intercept(clsName) {
    try {
      var C = Java.use(clsName);
      C.getResponseCode.implementation = function () {
        var u = ''; try { u = this.getURL().toString(); } catch (e) {}
        if (/superv|superdata|cwmob|ewan\.cn/i.test(u)) { L('fake 200 <- ' + u); return 200; }
        return this.getResponseCode();
      };
      C.getInputStream.implementation = function () {
        var u = ''; try { u = this.getURL().toString(); } catch (e) {}
        if (/superv|superdata|cwmob|ewan\.cn/i.test(u)) {
          L('fake body <- ' + u);
          return Java.use('java.io.ByteArrayInputStream').$new(toBytes(FAKE));
        }
        return this.getInputStream();
      };
      C.getContentLength.implementation = function () { return FAKE.length; };
      L('intercepting ' + clsName);
    } catch (e) { L('intercept ' + clsName + ' failed: ' + e); }
  }

  intercept('java.net.HttpURLConnection');
  intercept('javax.net.ssl.HttpsURLConnection');

  // force init listeners to report success
  var hooked = {};
  function hookClass(name) {
    var c; try { c = Java.use(name); } catch (e) { return; }
    ['onFail', 'onSuccess'].forEach(function (m) {
      var ovs; try { ovs = c[m].overloads; } catch (e) { return; }
      for (var i = 0; i < ovs.length; i++) {
        (function (ov, mm, cls) {
          ov.implementation = function () {
            var args = Array.prototype.slice.call(arguments).join(' | ');
            L(mm + ' @' + cls + ' [' + args + ']');
            if (mm === 'onFail') { try { L('  -> onSuccess'); return this.onSuccess(); } catch (e) { L('  err ' + e); } }
            return ov.apply(this, arguments);
          };
        })(ovs[i], m, name);
      }
    });
    L('hooked ' + name);
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

  L('net-intercept armed');
});
