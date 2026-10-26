// Frida script: log every HTTP/TCP connection attempt of the game client.
// Usage:
//   frida -U -f com.shiyue.dldl.ewan.baidu2 -l tools/frida_http.js -o tools/frida_out.txt
Java.perform(function () {
  function log(s) { console.log('[DSH] ' + s); }
  log('script loaded');

  try {
    var URL = Java.use('java.net.URL');
    URL.openConnection.overload().implementation = function () {
      log('URL.openConnection  ' + this.toString());
      return this.openConnection();
    };
  } catch (e) { log('hook URL failed: ' + e); }

  try {
    var HUC = Java.use('java.net.HttpURLConnection');
    HUC.connect.implementation = function () {
      log('HttpURLConnection.connect  ' + this.getURL().toString());
      return this.connect();
    };
    HUC.getResponseCode.implementation = function () {
      var u = '?';
      try { u = this.getURL().toString(); } catch (e) {}
      try {
        var c = this.getResponseCode();
        log('responseCode=' + c + '  ' + u);
        return c;
      } catch (e) {
        log('getResponseCode THREW for ' + u + ' : ' + e);
        throw e;
      }
    };
  } catch (e) { log('hook HttpURLConnection failed: ' + e); }

  try {
    var Sock = Java.use('java.net.Socket');
    Sock.connect.overload('java.net.SocketAddress', 'int').implementation = function (addr, t) {
      log('Socket.connect  ' + addr.toString() + '  timeout=' + t);
      return this.connect(addr, t);
    };
  } catch (e) { log('hook Socket failed: ' + e); }

  try {
    var HttpClient = Java.use('org.apache.http.impl.client.AbstractHttpClient');
    log('apache http client present');
  } catch (e) { /* not used */ }

  log('hooks installed');
});
