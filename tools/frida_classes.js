// Frida: enumerate SDK-related Java classes and probe init-related methods.
Java.perform(function () {
  function L(m) { console.log('[DSH] ' + m); }
  var pats = /ewan|supersdk|SuperSDK|cwmob|shiyue|ThirdSdk|thirdparty/i;
  var seen = [];
  Java.enumerateLoadedClasses({
    onMatch: function (n) { if (pats.test(n)) seen.push(n); },
    onComplete: function () {
      L('matched classes: ' + seen.length);
      seen.sort().forEach(function (n) {
        var methods = [];
        try {
          var c = Java.use(n);
          var ms = c.class.getDeclaredMethods();
          for (var i = 0; i < ms.length && methods.length < 12; i++) {
            var nm = ms[i].getName();
            if (/init|Init|login|Login|callback|Callback|fail|Fail|result|Result|success|Success/i.test(nm)) methods.push(nm);
          }
        } catch (e) {}
        L(n + '  ::  ' + methods.join(', '));
      });
      L('enumeration done');
    }
  });
});
