#!/usr/bin/env python3
"""LuaJIT bytecode dump layout SOLVER for the game's .luac files.

Files: magic 1B 4C 4A, byte[3]=0x01 (version), byte[4]=0x02 (flags=STRIP).
Unknown: exact prototype-header field order, count width, and whether CHILD
prototypes are serialized flattened (children first, CHILD = stack pop) or
inline (CHILD = recursively embedded proto).

We brute-force candidates over a corpus and keep the ones that parse every file
to exact EOF with zero trailing bytes.
"""
import sys, zipfile

KGC_CHILD, KGC_TAB, KGC_I64, KGC_U64, KGC_COMPLEX, KGC_STR = 0,1,2,3,4,5
KTAB_NIL, KTAB_FALSE, KTAB_TRUE, KTAB_INT, KTAB_NUM, KTAB_STR = 0,1,2,3,4,5
MAXDEPTH = 60

class ParseError(Exception): pass

class Parser:
    def __init__(self, data, order, width, childmode):
        self.d = data
        self.p = 0
        self.order = order    # 8 labels: f np fs uv kn kgc bc dbg
        self.width = width    # 'byte' | 'uleb'
        self.childmode = childmode  # 'flat' | 'inline'
        self.nstr = 0
        self.ntab = 0
        self.nproto = 0

    def u8(self):
        if self.p >= len(self.d): raise ParseError('eof u8')
        v = self.d[self.p]; self.p += 1; return v

    def uleb(self):
        v = 0; sh = 0
        while True:
            b = self.u8()
            v |= (b & 0x7f) << sh
            if not (b & 0x80): break
            sh += 7
            if sh > 42: raise ParseError('uleb long')
        return v

    def u16(self):
        if self.p + 2 > len(self.d): raise ParseError('eof u16')
        v = self.d[self.p] | (self.d[self.p+1] << 8); self.p += 2
        return v

    def u32(self):
        if self.p + 4 > len(self.d): raise ParseError('eof u32')
        v = int.from_bytes(self.d[self.p:self.p+4], 'little'); self.p += 4
        return v

    def strraw(self):
        n = self.u8()
        if self.p + n > len(self.d): raise ParseError('eof str')
        self.p += n
        self.nstr += 1

    def uleb_33(self):
        first = self.u8()
        isnum = first & 1
        v = first >> 1
        if v >= 0x40:
            sh = -1
            v &= 0x3f
            while True:
                b = self.u8()
                sh += 7
                v |= (b & 0x7f) << sh
                if not (b & 0x80): break
                if sh > 40: raise ParseError('uleb33 long')
        if isnum:
            self.uleb()   # hi32 of double
        return v

    def ktabk(self):
        t = self.uleb()
        if t == KTAB_STR: self.strraw()
        elif t == KTAB_INT: self.uleb()
        elif t == KTAB_NUM: self.uleb(); self.uleb()
        elif t in (KTAB_NIL, KTAB_FALSE, KTAB_TRUE): pass
        else: raise ParseError('bad ktabk %d' % t)

    def ktab(self):
        narr = self.uleb(); nhash = self.uleb()
        self.ntab += 1
        if narr > 0x10000 or nhash > 0x10000: raise ParseError('ktab huge')
        for _ in range(narr): self.ktabk()
        for _ in range(nhash): self.ktabk(); self.ktabk()

    def proto(self, depth=0):
        if depth > MAXDEPTH: raise ParseError('depth')
        self.nproto += 1
        cnt = {}
        for lab in self.order:
            if lab in ('kn', 'kgc', 'bc', 'dbg'):
                cnt[lab] = self.uleb() if self.width == 'uleb' else self.u8()
            else:
                cnt[lab] = self.u8()
        if cnt.get('dbg'):
            self.uleb(); self.uleb()   # firstline, numline
        for _ in range(cnt.get('bc', 0)):
            self.u32()
        for _ in range(cnt.get('uv', 0)):
            self.u16()
        for _ in range(cnt.get('kgc', 0)):
            t = self.uleb()
            if t == KGC_STR:
                self.strraw()
            elif t == KGC_TAB:
                self.ktab()
            elif t == KGC_CHILD:
                if self.childmode == 'inline':
                    self.proto(depth + 1)
                # 'flat': child already consumed at top level; nothing to read
            elif t in (KGC_I64, KGC_U64):
                self.uleb(); self.uleb()
            elif t == KGC_COMPLEX:
                self.uleb(); self.uleb(); self.uleb(); self.uleb()
            else:
                raise ParseError('bad kgc %d' % t)
        for _ in range(cnt.get('kn', 0)):
            self.uleb_33()

    def run(self):
        if self.childmode == 'flat':
            while True:
                if self.p >= len(self.d): raise ParseError('no term')
                if self.d[self.p] == 0:
                    self.p += 1
                    break
                self.proto()
        else:
            while True:
                if self.p >= len(self.d): raise ParseError('no term')
                if self.d[self.p] == 0:
                    self.p += 1
                    break
                self.proto()
        if self.p != len(self.d):
            raise ParseError('trail %d' % (len(self.d) - self.p))

def OK(data, order, width, childmode):
    p = Parser(data, order, width, childmode)
    try:
        p.run()
        return True
    except (ParseError, IndexError, ValueError):
        return False

def build_orders():
    import itertools
    orders = []
    head = ['f', 'np', 'fs', 'uv']
    for perm in itertools.permutations(head):
        for cnt in itertools.permutations(['kn', 'kgc', 'bc', 'dbg']):
            orders.append(perm + cnt)
    return orders

def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 250
    z = zipfile.ZipFile(apk)
    names = [n for n in z.namelist() if n.endswith('.luac')]
    # spread sample across sizes
    if limit and limit < len(names):
        step = len(names) // limit
        names = names[::step][:limit]
    data = [z.read(n) for n in names]
    data = [d for d in data if d[:3] == b'\x1bLJ']
    print('corpus:', len(data), 'files')
    results = []
    for order in build_orders():
        for width in ('uleb', 'byte'):
            for cm in ('flat', 'inline'):
                ok = sum(1 for d in data if OK(d, order, width, cm))
                if ok > 0:
                    results.append((ok, width, cm, order))
    results.sort(key=lambda r: -r[0])
    best = results[0][0] if results else 0
    print('best score:', best, '/', len(data))
    shown = 0
    for ok, width, cm, order in results:
        if ok < best and shown > 30:
            break
        print('%-5d %-5s %-6s %s' % (ok, width, cm, order))
        shown += 1
        if ok < best and shown > 200:
            break

if __name__ == '__main__':
    main()