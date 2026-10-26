#!/system/bin/sh
# Dump thread states + wchan for a pid, then a native backtrace.
PID=${1:-12048}
echo "=== threads of $PID ==="
for t in /proc/$PID/task/*; do
  tid=$(basename "$t")
  n=$(cat "$t/comm" 2>/dev/null)
  s=$(awk '{print $3}' "$t/stat" 2>/dev/null)
  w=$(cat "$t/wchan" 2>/dev/null)
  echo "$tid $n state=$s wchan=$w"
done
echo "=== debuggerd -b $PID (native backtraces) ==="
debuggerd -b "$PID" 2>&1 | head -120
