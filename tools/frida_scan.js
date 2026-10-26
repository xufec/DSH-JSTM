// Frida: periodically enumerate SDK classes, and auto-dismiss dialogs.
Java.perform(function () {
  function L(m) { console.log('[DSH] ' + m); }
  var pats = /ewan|supersdk|SuperSDK|cwmob|ThirdSdk/i;
  var known = {};

  function logClass(n) {
    var ms = [];
    try {
      var c = Java.use(n);
      var arr = c.class.getDeclaredMethods();
      for (var i = 0; i < arr.length; i++) ms.push(arr[i].getName());
    } catch (e) { ms.push('(err ' + e + ')'); }
    L('CLASS ' + n + ' :: ' + ms.join(','));
  }

  function scan() {
    try {
      Java.enumerateLoadedClasses({
        onMatch: function (n) { if (pats.test(n) && !known[n]) { known[n] = 1; logClass(n); } },
        onComplete: function () { }
      });
    } catch (e) { L('scan err: ' + e); }
  }

  // auto-dismiss any dialog that appears
  try {
    var D = Java.use('android.app.Dialog');
    D.show.implementation = function () {
      var cls = this.getClass().getName();
      L('Dialog.show ' + cls);
      var self = this;
      setTimeout(function () {
        try { self.dismiss(); L('dismissed ' + cls); } catch (e) { L('dismiss err ' + e); }
      }, 2500);
      return this.show();
    };
    L('Dialog.show hooked');
  } catch (e) { L('hook Dialog failed: ' + e); }

  scan();
  setInterval(scan, 5000);
  L('scanner started');
});
