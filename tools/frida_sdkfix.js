// Frida: force the ewan superSDK init to succeed (onFail -> onSuccess), so the game
// stops showing "初始化失败,请检查网络" and proceeds to the version check / login.
Java.perform(function () {
  function L(m) { console.log('[DSH] ' + m); }
  var hooked = {};

  function hookClass(n) {
    if (hooked[n]) return;
    hooked[n] = 1;
    try {
      var c = Java.use(n);
      if (c.onFail && c.onSuccess) {
        try {
          c.onSuccess.overload().implementation = function () {
            L('onSuccess  @' + n);
            return this.onSuccess();
          };
        } catch (e) { L('onSuccess hook err @' + n + ' : ' + e); }
        try {
          c.onFail.overload('int', 'java.lang.String').implementation = function (a, b) {
            L('onFail @' + n + ' (' + a + ', ' + b + ')  -> forcing onSuccess');
            try { return this.onSuccess(); } catch (e) { L('  force err: ' + e); }
          };
          L('hooked onFail(int,String) @' + n);
        } catch (e) {
          try {
            c.onFail.overload().implementation = function () {
              L('onFail() @' + n + ' -> forcing onSuccess');
              try { return this.onSuccess(); } catch (e2) { L('  force err: ' + e2); }
            };
            L('hooked onFail() @' + n);
          } catch (e2) { L('onFail hook err @' + n + ' : ' + e2); }
        }
      }
    } catch (e) { }
  }

  function scan() {
    try {
      Java.enumerateLoadedClasses({
        onMatch: function (n) {
          if (/ewan|supersdk|SuperSDK|cwmob/i.test(n)) {
            if (!hooked[n]) {
              var ms = '';
              try {
                var c = Java.use(n);
                var arr = c.class.getDeclaredMethods();
                for (var i = 0; i < arr.length; i++) ms += arr[i].getName() + ',';
              } catch (e) { }
              if (ms.indexOf('onFail') >= 0 || ms.indexOf('onSuccess') >= 0) {
                L('candidate ' + n + ' :: ' + ms);
                hookClass(n);
              }
            }
          }
        },
        onComplete: function () { }
      });
    } catch (e) { }
  }

  scan();
  setInterval(scan, 4000);
  L('SDK init bypass scanner started');
});
