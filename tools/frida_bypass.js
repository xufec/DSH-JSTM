// Frida: find out who shows the "初始化失败,请检查网络" dialog, and log SDK init.
Java.perform(function () {
  function L(m) { console.log('[DSH] ' + m); }
  L('script loaded (frida ' + Frida.version + ')');

  function stack() {
    try {
      var Ex = Java.use('java.lang.Exception').$new();
      var s = Java.use('android.util.Log').getStackTraceString(Ex);
      return s.split('\n').slice(0, 14).join('\n');
    } catch (e) { return '(no stack: ' + e + ')'; }
  }

  try {
    var AlertDialog = Java.use('android.app.AlertDialog');
    AlertDialog.show.implementation = function () {
      L('=== AlertDialog.show called ===');
      L(stack());
      return this.show();
    };
  } catch (e) { L('hook AlertDialog failed: ' + e); }

  try {
    var Dialog = Java.use('android.app.Dialog');
    Dialog.show.implementation = function () {
      L('=== Dialog.show (' + this.getClass().getName() + ') ===');
      return this.show();
    };
  } catch (e) { L('hook Dialog failed: ' + e); }

  try {
    var Toast = Java.use('android.widget.Toast');
    Toast.show.implementation = function () {
      try { L('Toast.show: ' + this.getText()); } catch (e) { L('Toast.show (no text)'); }
      return this.show();
    };
  } catch (e) { L('hook Toast failed: ' + e); }

  try {
    var TextView = Java.use('android.widget.TextView');
    // log when the specific dialog text gets set
    TextView.setText.overload('java.lang.CharSequence').implementation = function (cs) {
      var s = cs ? cs.toString() : '';
      if (s.indexOf('初始化失败') >= 0 || s.indexOf('请检查网络') >= 0 || s.indexOf('连接') >= 0) {
        L('TextView.setText: ' + s + '  @' + this.getClass().getName());
      }
      return this.setText(cs);
    };
  } catch (e) { L('hook TextView failed: ' + e); }

  L('hooks installed');
});
