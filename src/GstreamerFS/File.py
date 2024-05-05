import os
import syslog
import fcntl

def flag2mode(flags):
    md = {os.O_RDONLY: 'r', os.O_WRONLY: 'w', os.O_RDWR: 'w+'}
    m = md[flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)]

    if flags | os.O_APPEND:
        m = m.replace('w', 'a', 1)

    return m

class File(object):

    def __init__(self, fuse, path, flags, *mode):
        self.fuse = fuse

        syslog.syslog('self: %s' % self)
        syslog.syslog('Fuse: %s' % fuse)
        syslog.syslog('path: %s' % path)

        if (fuse.files.has_key(path)):
            path = fuse.files[path]

        self.file = os.fdopen(os.open("." + path, flags, *mode),
                              flag2mode(flags))
        self.fd = self.file.fileno()

    def read(self, length, offset):
        syslog.syslog('Function read(%i, %i) called' % (length, offset))
        self.file.seek(offset)
        return self.file.read(length)

    def write(self, buf, offset):
        syslog.syslog('Function write() called')
        self.file.seek(offset)
        self.file.write(buf)
        return len(buf)

    def release(self, flags):
        syslog.syslog('Function release(%s) called' % (flags))
        self.file.close()

    def _fflush(self):
        syslog.syslog('Function fflush() called')
        if 'w' in self.file.mode or 'a' in self.file.mode:
            self.file.flush()

    def fsync(self, isfsyncfile):
        syslog.syslog('Function fsync(%b) called' % (isfsyncfile))
        self._fflush()
        if isfsyncfile and hasattr(os, 'fdatasync'):
            os.fdatasync(self.fd)
        else:
            os.fsync(self.fd)

    def flush(self):
        syslog.syslog('Function flush() called')
        self._fflush()
        # cf. xmp_flush() in fusexmp_fh.c
        os.close(os.dup(self.fd))

    def fgetattr(self):
        syslog.syslog('Function fgetattr() called')
        return os.fstat(self.fd)

    def ftruncate(self, len):
        syslog.syslog('Function ftruncate() called')
        self.file.truncate(len)

    def lock(self, cmd, owner, **kw):
        syslog.syslog('Function lock(%s, %s, %s) called' % (cmd, owner, kw))
        # The code here is much rather just a demonstration of the locking
        # API than something which actually was seen to be useful.

        # Advisory file locking is pretty messy in Unix, and the Python
        # interface to this doesn't make it better.
        # We can't do fcntl(2)/F_GETLK from Python in a platfrom independent
        # way. The following implementation *might* work under Linux.
        #
        # if cmd == fcntl.F_GETLK:
        #     import struct
        #
        #     lockdata = struct.pack('hhQQi', kw['l_type'], os.SEEK_SET,
        #                            kw['l_start'], kw['l_len'], kw['l_pid'])
        #     ld2 = fcntl.fcntl(self.fd, fcntl.F_GETLK, lockdata)
        #     flockfields = ('l_type', 'l_whence', 'l_start', 'l_len', 'l_pid')
        #     uld2 = struct.unpack('hhQQi', ld2)
        #     res = {}
        #     for i in xrange(len(uld2)):
        #          res[flockfields[i]] = uld2[i]
        #
        #     return fuse.Flock(**res)

        # Convert fcntl-ish lock parameters to Python's weird
        # lockf(3)/flock(2) medley locking API...
        op = { fcntl.F_UNLCK : fcntl.LOCK_UN,
               fcntl.F_RDLCK : fcntl.LOCK_SH,
               fcntl.F_WRLCK : fcntl.LOCK_EX }[kw['l_type']]
        if cmd == fcntl.F_GETLK:
            return -EOPNOTSUPP
        elif cmd == fcntl.F_SETLK:
            if op != fcntl.LOCK_UN:
                op |= fcntl.LOCK_NB
        elif cmd == fcntl.F_SETLKW:
            pass
        else:
            return -EINVAL

        fcntl.lockf(self.fd, op, kw['l_start'], kw['l_len'])