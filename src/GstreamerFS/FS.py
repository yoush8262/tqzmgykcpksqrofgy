import os.path
import os
from errno import *
from stat import *

import fuse
from fuse import Fuse
import syslog
import GstreamerFS

class FS(Fuse):

    def __init__(self, *args, **kw):

        Fuse.__init__(self, *args, **kw)

        # do stuff to set up your filesystem here, if you want
        #import thread
        #thread.start_new_thread(self.mythread, ())
        self.root = '/'
#        self.file_class = GstreamerFSFile
        self.files = {}

    def main(self, *args, **kwargs):
        fuse = self

        class FileClass(GstreamerFS.File):
            def __init__(self, *args, **kwargs):
                syslog.syslog('fuse: %s' % fuse)
                syslog.syslog('self: %s' % self)
                GstreamerFS.File.__init__(self, fuse, *args, **kwargs)

        self.file_class = FileClass
        return Fuse.main(self, *args, **kwargs)

#    def mythread(self):
#
#        """
#        The beauty of the FUSE python implementation is that with the python interp
#        running in foreground, you can have threads
#        """
#        print "mythread: started"
#        while 1:
#            time.sleep(120)
#            print "mythread: ticking"

    def getattr(self, path):
        syslog.syslog('Function getattr(%s) called' % (path))

#        syslog.syslog('Path: %s' % path)
#        syslog.syslog('self.files: %s' % self.files)

        if (self.files.has_key(path)):
#            syslog.syslog('self.files[%s] = %s' % (path, self.files[path]))
            path = self.files[path]

        return os.lstat("." + path)

    def readlink(self, path):
        syslog.syslog('Function readlink(%s) called' % (path))
        return os.readlink("." + path)

    def readdir(self, path, offset):
        syslog.syslog('Function readdir(%s, %s) called' % (path, offset))

        if os.path.isdir("." + path):
            yield fuse.Direntry('.')
            yield fuse.Direntry('..')

        #op volgorde van proberen: meer achteraan is liever niet
        extensions = ['.wav', '.flac', '.ogg', '.wma']
        for e in os.listdir("." + path):
            f = self.root + path + os.sep + e
            syslog.syslog('file: ' + f)

            if os.path.isfile(f):
                basename, extension = os.path.splitext(e)
                #Take into account that some files could be double:
                # e.g.: test.flac, test.ogg
                if extension.lower() in extensions:

                    syslog.syslog('Returning: ' + basename + '.mp3')
                    self.files[path + os.sep + basename + '.mp3'] = path + os.sep + e
                    yield fuse.Direntry(basename + '.mp3')
                    syslog.syslog('Transcode file: ' + f)
                    continue
                else:
                    yield fuse.Direntry(e)
                    continue
            else:
                yield fuse.Direntry(e)
                continue

    def unlink(self, path):
        os.unlink("." + path)

    def rmdir(self, path):
        os.rmdir("." + path)

    def symlink(self, path, path1):
        os.symlink(path, "." + path1)

    def rename(self, path, path1):
        os.rename("." + path, "." + path1)

    def link(self, path, path1):
        os.link("." + path, "." + path1)

    def chmod(self, path, mode):
        os.chmod("." + path, mode)

    def chown(self, path, user, group):
        os.chown("." + path, user, group)

    def truncate(self, path, len):
        syslog.syslog('Function truncate(%s, %s) called' % (path, len))
        f = open("." + path, "a")
        f.truncate(len)
        f.close()

    def mknod(self, path, mode, dev):
        os.mknod("." + path, mode, dev)

    def mkdir(self, path, mode):
        syslog.syslog('Function mkdir(%s, %s) called' % (path, mode))
        os.mkdir("." + path, mode)

    def utime(self, path, times):
        syslog.syslog('Function utime(%s, %s) called' % (path, times))
        os.utime("." + path, times)

#    The following utimens method would do the same as the above utime method.
#    We can't make it better though as the Python stdlib doesn't know of
#    subsecond preciseness in acces/modify times.
#
#    def utimens(self, path, ts_acc, ts_mod):
#      os.utime("." + path, (ts_acc.tv_sec, ts_mod.tv_sec))

    def access(self, path, mode):
        syslog.syslog('Function access(%s, %s) called' % (path, mode))

        syslog.syslog('Function getattr(%s) called' % (path))

#        syslog.syslog('Path: %s' % path)
#        syslog.syslog('self.files: %s' % self.files)

        if (self.files.has_key(path)):
#            syslog.syslog('self.files[%s] = %s' % (path, self.files[path]))
            path = self.files[path]

        if not os.access("." + path, mode):
            return -EACCES

#    This is how we could add stub extended attribute handlers...
#    (We can't have ones which aptly delegate requests to the underlying fs
#    because Python lacks a standard xattr interface.)
#
#    def getxattr(self, path, name, size):
#        val = name.swapcase() + '@' + path
#        if size == 0:
#            # We are asked for size of the value.
#            return len(val)
#        return val
#
#    def listxattr(self, path, size):
#        # We use the "user" namespace to please XFS utils
#        aa = ["user." + a for a in ("foo", "bar")]
#        if size == 0:
#            # We are asked for size of the attr list, ie. joint size of attrs
#            # plus null separators.
#            return len("".join(aa)) + len(aa)
#        return aa

    def statfs(self):
        """
        Should return an object with statvfs attributes (f_bsize, f_frsize...).
        Eg., the return value of os.statvfs() is such a thing (since py 2.2).
        If you are not reusing an existing statvfs object, start with
        fuse.StatVFS(), and define the attributes.

        To provide usable information (ie., you want sensible df(1)
        output, you are suggested to specify the following attributes:

            - f_bsize - preferred size of file blocks, in bytes
            - f_frsize - fundamental size of file blcoks, in bytes
                [if you have no idea, use the same as blocksize]
            - f_blocks - total number of blocks in the filesystem
            - f_bfree - number of free blocks
            - f_files - total number of file inodes
            - f_ffree - nunber of free file inodes
        """

        syslog.syslog('Function statfs() called')
        return os.statvfs(".")

    def fsinit(self):
        print "fsinit()..."
        os.chdir(self.root)