// Frida: safe polling hooks on ewan superSDK init listeners (no loadClass hooking,
// which deadlocks). Forces onFail -> onSuccess.
Java.perform(function () {
  function L(m) { console.log('[DSH] ' + m); }
  var hooked = {};

  function hookClass(name) {
    var c;
    try { c = Java.use(name); } catch (e) { return false; }
    var any = false;
    ['onFail', 'onSuccess'].forEach(function (m) {
      var ovs;
      try { ovs = c[m].overloads; } catch (e) { return; }
      if (ovs.length) any = true;
      for (var i = 0; i < ovs.length; i++) {
        (function (ov, mm, cls) {
          ov.implementation = function () {
            var args = Array.prototype.slice.call(arguments).join(' | ');
            L(mm + ' @' + cls + ' args=[' + args + ']');
            if (mm === 'onFail') {
              try { L('  -> forcing onSuccess'); return this.onSuccess(); }
              catch (e) { L('  force err: ' + e); }
            }
            return ov.apply(this, arguments);
          };
        })(ovs[i], m, name);
      }
    });
    if (any) L('hooked ' + name);
    return any;
  }

  function poll() {
    try {
      Java.enumerateLoadedClassesSync().forEach(function (n) {
        if (hooked[n]) return;
        if (/^cn\.ewan\.supersdk\./.test(n)) {
          hooked[n] = 1;
          hookClass(n);
        }
      });
    } catch (e) { L('poll err: ' + e); }
  }

  poll();
  var t = setInterval(poll, 250);
  setTimeout(function () { clearInterval(t); L('polling stopped'); }, 120000);
  L('sdkfix4 polling started');
});
