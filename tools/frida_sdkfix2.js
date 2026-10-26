// Frida: force ewan superSDK init success. Hooks onFail/onSuccess on every
// loaded supersdk class (by name), turning onFail into onSuccess.
Java.perform(function () {
  function L(m) { console.log('[DSH] ' + m); }

  function hookAll() {
    var names = [];
    try {
      Java.enumerateLoadedClassesSync().forEach(function (n) {
        if (/supersdk|ewan\.sdk|SuperSDK/i.test(n)) names.push(n);
      });
    } catch (e) { L('enum err ' + e); }
    L('supersdk classes: ' + names.length);
    names.forEach(function (n) {
      var c;
      try { c = Java.use(n); } catch (e) { return; }
      ['onFail', 'onSuccess'].forEach(function (m) {
        var ovs;
        try { ovs = c[m].overloads; } catch (e) { return; }
        for (var i = 0; i < ovs.length; i++) {
          (function (ov, mm, cls) {
            ov.implementation = function () {
              var args = Array.prototype.slice.call(arguments).join(',');
              L(mm + ' @' + cls + '(' + args + ')');
              if (mm === 'onFail') {
                try { return this.onSuccess(); } catch (e) { L('  force-success err: ' + e); }
              }
              return ov.apply(this, arguments);
            };
          })(ovs[i], m, n);
        }
        L('hooked ' + m + ' @' + n);
      });
    });
    L('hooking done');
  }

  setTimeout(hookAll, 12000);
  setTimeout(hookAll, 25000);
  L('sdkfix armed');
});
