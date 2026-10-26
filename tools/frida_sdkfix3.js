// Frida: catch ewan superSDK init callbacks at class-load time (so we never miss
// them), log the failure reason, and force onFail -> onSuccess.
Java.perform(function () {
  function L(m) { console.log('[DSH] ' + m); }
  var hooked = {};

  function hookClass(c, name) {
    ['onFail', 'onSuccess'].forEach(function (m) {
      var ovs;
      try { ovs = c[m].overloads; } catch (e) { return; }
      for (var i = 0; i < ovs.length; i++) {
        (function (ov, mm, cls) {
          ov.implementation = function () {
            var args = Array.prototype.slice.call(arguments).join(' | ');
            L(mm + ' @' + cls + '  args=[' + args + ']');
            if (mm === 'onFail') {
              try {
                L('  -> forcing onSuccess');
                return this.onSuccess();
              } catch (e) { L('  force-success err: ' + e); }
            }
            return ov.apply(this, arguments);
          };
        })(ovs[i], m, name);
      }
    });
    L('hooked ' + name);
  }

  // 1) hook classes that are already loaded
  try {
    Java.enumerateLoadedClassesSync().forEach(function (n) {
      if (/^cn\.ewan\.supersdk\./.test(n)) { hooked[n] = 1; hookClass(Java.use(n), n); }
    });
  } catch (e) { L('enum err ' + e); }

  // 2) hook future class loads
  try {
    var CL = Java.use('java.lang.ClassLoader');
    CL.loadClass.overload('java.lang.String').implementation = function (n) {
      var c = this.loadClass(n);
      try {
        if (typeof n === 'string' && /^cn\.ewan\.supersdk\./.test(n) && !hooked[n]) {
          hooked[n] = 1;
          hookClass(Java.use(n), n);
        }
      } catch (e) { L('loadClass hook err: ' + e); }
      return c;
    };
    L('ClassLoader.loadClass hooked');
  } catch (e) { L('ClassLoader hook failed: ' + e); }

  L('sdkfix3 armed');
});
