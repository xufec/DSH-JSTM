// Frida: find the owner of the blocking "初始化失败,请检查网络" dialog.
//
// The app does not progress under frida spawn (ARM translation + anti-debug),
// so this is loaded by ATTACHING a few seconds after a normal launch -- the
// dialog appears ~12 s in, so the hooks are in place before it is built.
//
// Run with the frida CLI (qjs runtime), which exposes the global `Java`.
Java.perform(function () {
  function log(m) { console.log('[DSH] ' + m); }

  function stack() {
    try {
      var Throwable = Java.use('java.lang.Throwable');
      var Log = Java.use('android.util.Log');
      return Log.getStackTraceString(Throwable.$new('dsh-trace'));
    } catch (e) { return 'stack err: ' + e; }
  }

  var WANT = ['初始化失败', '请检查网络', '重新连接', '退出游戏', '提示'];
  function interesting(s) {
    if (s === null || s === undefined) return false;
    s = String(s);
    for (var i = 0; i < WANT.length; i++) {
      if (s.indexOf(WANT[i]) >= 0) return true;
    }
    return false;
  }

  var seen = {};
  var counts = { setText: 0, show: 0, msg: 0, title: 0 };

  setInterval(function () {
    log('heartbeat setText=' + counts.setText + ' dialogShow=' + counts.show
        + ' setMessage=' + counts.msg + ' setTitle=' + counts.title);
  }, 8000);

  // --- AlertDialog.Builder path ---
  var Builder = Java.use('android.app.AlertDialog$Builder');
  Builder.setMessage.overload('java.lang.CharSequence').implementation = function (m) {
    counts.msg++;
    log('setMessage(CharSequence) = ' + m + '\n' + stack());
    return this.setMessage(m);
  };
  Builder.setMessage.overload('int').implementation = function (id) {
    counts.msg++;
    log('setMessage(int 0x' + id.toString(16) + ')\n' + stack());
    return this.setMessage(id);
  };
  Builder.setTitle.overload('java.lang.CharSequence').implementation = function (t) {
    counts.title++;
    log('setTitle = ' + t + '\n' + stack());
    return this.setTitle(t);
  };
  Builder.setPositiveButton.overload('java.lang.CharSequence', 'android.content.DialogInterface$OnClickListener').implementation = function (t, l) {
    log('setPositiveButton = ' + t + '\n' + stack());
    return this.setPositiveButton(t, l);
  };
  Builder.setNegativeButton.overload('java.lang.CharSequence', 'android.content.DialogInterface$OnClickListener').implementation = function (t, l) {
    log('setNegativeButton = ' + t + '\n' + stack());
    return this.setNegativeButton(t, l);
  };

  // --- generic paths ---
  var Dialog = Java.use('android.app.Dialog');
  Dialog.show.implementation = function () {
    counts.show++;
    var cn = this.getClass().getName();
    if (!seen['show:' + cn]) {
      seen['show:' + cn] = 1;
      log('Dialog.show() class=' + cn + '\n' + stack());
    }
    return this.show();
  };

  var TextView = Java.use('android.widget.TextView');
  TextView.setText.overload('java.lang.CharSequence').implementation = function (t) {
    counts.setText++;
    if (interesting(t) && !seen['tv:' + t]) {
      seen['tv:' + t] = 1;
      log('TextView(' + this.getClass().getName() + ').setText = ' + t + '\n' + stack());
    }
    return this.setText(t);
  };

  log('hooks installed');
});
