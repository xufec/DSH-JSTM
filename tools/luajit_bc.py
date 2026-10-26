#!/usr/bin/env python3
"""LuaJIT 2.0 bytecode dump parser (game client .luac reader).

Format (from LuaJIT v2.0 src/lj_bcdump.h):

  dump   = header proto+ 0U
  header = ESC 'L' 'J' versionB flagsU [namelenU nameB*]
  proto  = lengthU pdata
  pdata  = phead bcinstrW* uvdataH* kgc* knum* [debugB*]
  phead  = flagsB numparamsB framesizeB numuvB numkgcU numknU numbcU
           [debuglenU [firstlineU numlineU]]
  kgc    = kgctypeU { ktab | (loU hiU) | (rloU rhiU iloU ihiU) | strB* }
  knum   = intU0 | (loU1 hiU)
  ktab   = narrU nhashU karray* khash*
  ktabk  = ktabtypeU { intU | (loU hiU) | strB* }

Notes discovered empirically for this client's files (version byte 0x01,
flags 0x02 = BCDUMP_F_STRIP):
  * string constants are stored as uleb(len + 5) followed by raw bytes,
    i.e. the type tag and the length are folded into one uleb.  Same for
    constant-table strings (ktabtype base = KTAB_STR = 5).
  * prototypes are serialized in post-order: children appear BEFORE the
    parent that references them; a kgc entry with tag CHILD(0) consumes no
    bytes and refers to the most recently read prototype.
"""
import struct

KGC_CHILD, KGC_TAB, KGC_I64, KGC_U64, KGC_COMPLEX, KGC_STR = 0, 1, 2, 3, 4, 5
KTAB_NIL, KTAB_FALSE, KTAB_TRUE, KTAB_INT, KTAB_NUM, KTAB_STR = 0, 1, 2, 3, 4, 5

# prototype flags (lj_obj.h)
PROTO_CHILD    = 0x01
PROTO_VARARG   = 0x02
PROTO_FFI      = 0x04
PROTO_NOJIT    = 0x08
PROTO_ILOOP    = 0x10
PROTO_FIXUP_RETURN = 0x20
PROTO_CLCOUNT  = 0x20
PROTO_BITOP    = 0x80

BCDUMP_F_BE = 0x01
BCDUMP_F_STRIP = 0x02
BCDUMP_F_FFI = 0x04


class BCError(Exception):
    pass


class TableConst:
    __slots__ = ('array', 'hash')

    def __init__(self, array, hashpairs):
        self.array = array
        self.hash = hashpairs

    def __repr__(self):
        return 'TableConst(array=%r, hash=%r)' % (self.array, self.hash)


class ChildRef:
    """Reference to another prototype in the same dump (post-order index)."""
    __slots__ = ('index',)

    def __init__(self, index):
        self.index = index

    def __repr__(self):
        return 'ChildRef(#%d)' % self.index


class Proto:
    def __init__(self):
        self.index = -1
        self.flags = 0
        self.numparams = 0
        self.framesize = 0
        self.numuv = 0
        self.kgc = []
        self.knum = []
        self.bc = []
        self.uv = []
        self.debuglen = 0
        self.firstline = 0
        self.numline = 0
        self.length = 0

    @property
    def strings(self):
        return [c for c in self.kgc if isinstance(c, str)]

    @property
    def tables(self):
        return [c for c in self.kgc if isinstance(c, TableConst)]

    @property
    def children(self):
        return [c for c in self.kgc if isinstance(c, ChildRef)]

    def __repr__(self):
        return '<Proto len=%d bc=%d uv=%d kgc=%d kn=%d params=%d framesize=%d>' % (
            self.length, len(self.bc), self.numuv, len(self.kgc), len(self.knum),
            self.numparams, self.framesize)


class Reader:
    def __init__(self, data):
        self.d = data
        self.p = 0
        self.flags = 0
        self.version = 0
        self.protos = []
        self.name = None
        # LuaJIT pushes every prototype read onto a VM stack; a kgc CHILD
        # constant pops one (LIFO) to resolve the nested-function reference.
        self.stack = []

    # ---- primitives ----
    def u8(self):
        if self.p >= len(self.d):
            raise BCError('unexpected EOF (u8 at %d)' % self.p)
        v = self.d[self.p]
        self.p += 1
        return v

    def u16(self):
        if self.p + 2 > len(self.d):
            raise BCError('unexpected EOF (u16)')
        v = self.d[self.p] | (self.d[self.p + 1] << 8)
        self.p += 2
        return v

    def u32(self):
        if self.p + 4 > len(self.d):
            raise BCError('unexpected EOF (u32)')
        v = struct.unpack_from('<I', self.d, self.p)[0]
        self.p += 4
        return v

    def uleb(self):
        v = 0
        sh = 0
        while True:
            b = self.u8()
            v |= (b & 0x7f) << sh
            if not (b & 0x80):
                return v
            sh += 7
            if sh > 42:
                raise BCError('uleb too long')

    def bytes_(self, n):
        if self.p + n > len(self.d):
            raise BCError('unexpected EOF (bytes %d)' % n)
        b = self.d[self.p:self.p + n]
        self.p += n
        return b

    def uleb_33(self):
        """bcread_uleb128_33: low bit of first byte = isnum flag."""
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
                if not (b & 0x80):
                    break
                if sh > 40:
                    raise BCError('uleb33 too long')
        if isnum:
            hi = self.uleb()
            return struct.unpack('<d', struct.pack('<II', v & 0xffffffff, hi & 0xffffffff))[0]
        return v & 0xffffffff if v < 0x80000000 else v - 0x100000000

    # ---- structures ----
    def ktabk(self):
        tag = self.uleb()
        if tag >= KTAB_STR:            # folded string: tag = len + 5
            n = tag - KTAB_STR
            return self.bytes_(n).decode('utf-8', 'replace')
        if tag == KTAB_NIL:
            return None
        if tag == KTAB_FALSE:
            return False
        if tag == KTAB_TRUE:
            return True
        if tag == KTAB_INT:
            v = self.uleb()
            return v - 0x100000000 if v >= 0x80000000 else v
        if tag == KTAB_NUM:
            lo = self.uleb()
            hi = self.uleb()
            return struct.unpack('<d', struct.pack('<II', lo & 0xffffffff, hi & 0xffffffff))[0]
        raise BCError('bad ktabk tag %d at %d' % (tag, self.p))

    def ktab(self):
        narr = self.uleb()
        nhash = self.uleb()
        if narr > 0x200000 or nhash > 0x200000:
            raise BCError('ktab too large (%d/%d)' % (narr, nhash))
        arr = [self.ktabk() for _ in range(narr)]
        h = []
        for _ in range(nhash):
            k = self.ktabk()
            v = self.ktabk()
            h.append((k, v))
        return TableConst(arr, h)

    def proto(self):
        pt = Proto()
        start = self.p
        pt.flags = self.u8()
        pt.numparams = self.u8()
        pt.framesize = self.u8()
        pt.numuv = self.u8()
        numkgc = self.uleb()
        numkn = self.uleb()
        numbc = self.uleb()
        if self.version >= 2:
            numbc += 1          # 2.1 injects a synthetic BC[0]
        if not (self.flags & BCDUMP_F_STRIP):
            pt.debuglen = self.uleb()
            if pt.debuglen:
                pt.firstline = self.uleb()
                pt.numline = self.uleb()
        for _ in range(numbc):
            pt.bc.append(self.u32())
        for _ in range(pt.numuv):
            pt.uv.append(self.u16())
        for _ in range(numkgc):
            tag = self.uleb()
            if tag >= KGC_STR:                      # folded string
                n = tag - KGC_STR
                pt.kgc.append(self.bytes_(n).decode('utf-8', 'replace'))
            elif tag == KGC_CHILD:
                if not self.stack:
                    raise BCError('CHILD reference with empty proto stack')
                child = self.stack.pop()          # LIFO, as LuaJIT's reader does
                pt.kgc.append(ChildRef(child.index))
            elif tag == KGC_TAB:
                pt.kgc.append(self.ktab())
            elif tag in (KGC_I64, KGC_U64):
                lo = self.uleb()
                hi = self.uleb()
                v = (hi << 32) | (lo & 0xffffffff)
                if tag == KGC_I64 and v >= 0x8000000000000000:
                    v -= 0x10000000000000000
                pt.kgc.append(v)
            elif tag == KGC_COMPLEX:
                lo = self.uleb(); hi = self.uleb()
                rlo = self.uleb(); rhi = self.uleb()
                pt.kgc.append(complex(0, 0))  # placeholder; complex consts unused here
            else:
                raise BCError('bad kgc tag %d at %d' % (tag, self.p))
        for _ in range(numkn):
            pt.knum.append(self.uleb_33())
        if pt.debuglen:
            self.bytes_(pt.debuglen)
        pt.length = self.p - start
        return pt

    def parse(self):
        if self.d[:3] != b'\x1bLJ':
            raise BCError('not a LuaJIT dump')
        self.p = 3
        self.version = self.u8()
        if self.version not in (1, 2):
            raise BCError('unsupported dump version %d' % self.version)
        self.flags = self.uleb()
        if not (self.flags & BCDUMP_F_STRIP):
            namelen = self.uleb()
            self.name = self.bytes_(namelen).decode('utf-8', 'replace')
        # 2.1: every proto is length-prefixed; for 2.0 the lengthU is present
        # in the grammar comment as well and verified empirically on this client.
        while True:
            if self.p >= len(self.d):
                raise BCError('missing end-of-dump terminator')
            if self.d[self.p] == 0:
                self.p += 1
                break
            plen = self.uleb()
            body_start = self.p
            pt = self.proto()
            if self.p - body_start != plen:
                raise BCError('proto length mismatch: header says %d, read %d'
                              % (plen, self.p - body_start))
            pt.index = len(self.protos)
            self.protos.append(pt)
            self.stack.append(pt)
        if self.p != len(self.d):
            raise BCError('%d trailing bytes' % (len(self.d) - self.p))
        return self.protos

    @property
    def root(self):
        return self.protos[-1] if self.protos else None


def parse_bytes(data):
    r = Reader(data)
    r.parse()
    return r


def parse_file(path):
    with open(path, 'rb') as f:
        return parse_bytes(f.read())


if __name__ == '__main__':
    import sys
    r = parse_file(sys.argv[1])
    print('version=%d flags=0x%02x name=%r protos=%d'
          % (r.version, r.flags, r.name, len(r.protos)))
    for i, pt in enumerate(r.protos):
        print('[%02d] %r' % (i, pt))
        for c in pt.kgc[:12]:
            print('      kgc:', repr(c)[:100])
        if pt.knum[:8]:
            print('      knum:', pt.knum[:8])