from crypto.aes import AESdecryptCBC
from hashlib import sha1
from struct import unpack
import os

MBDB_SIGNATURE = 'mbdb\x05\x00'

MASK_SYMBOLIC_LINK = 0xa000
MASK_REGULAR_FILE = 0x8000
MASK_DIRECTORY = 0x4000

def warn(msg):
    print "WARNING: %s" % msg
    
class MBFileRecord(object):
    def __init__(self, mbdb):
        self.domain = self._decode_string(mbdb)
        if self.domain is None:
            warn("Domain name missing from record")

        self.path = self._decode_string(mbdb)
        if self.path is None:
            warn("Relative path missing from record")

        self.target= self._decode_string(mbdb) # for symbolic links

        self.digest = self._decode_string(mbdb)
        self.encryption_key = self._decode_data(mbdb)

        data = mbdb.read(40) # metadata, fixed size

        self.mode, = unpack('>H', data[0:2])
        if not(self.is_regular_file() or self.is_symbolic_link() or self.is_directory()):
            print self.mode
            warn("File type mising from record mode")

        if self.is_symbolic_link() and self.target is None:
            warn("Target required for symblolic links")

        self.inode_number = unpack('>Q', data[2:10])
        self.user_id, = unpack('>I', data[10:14])
        self.group_id = unpack('>I', data[14:18])
        self.last_modification_time, = unpack('>i', data[18:22])
        self.last_status_change_time, = unpack('>i', data[22:26])
        self.birth_time, = unpack('>i', data[26:30])
        self.size, = unpack('>q', data[30:38])

        if self.size != 0 and not self.is_regular_file():
            warn("Non-zero size for a record which is not a regular file")

        self.protection_class = ord(data[38])

        num_attributes = ord(data[39])
        if num_attributes == 0:
            self.extended_attributes = None
        else:
            self.extended_attributes = {}
            for i in xrange(num_attributes):
                k = self._decode_string(mbdb)
                v = self._decode_data(mbdb)
                self.extended_attributes[k] = v

    def _decode_string(self, s):
        s_len, = unpack('>H', s.read(2))
        if s_len == 0xffff:
            return None
        return s.read(s_len)

    def _decode_data(self, s):
        return self._decode_string(s)

    def type(self):
        return self.mode & 0xf000

    def is_symbolic_link(self):
        return self.type() == MASK_SYMBOLIC_LINK

    def is_regular_file(self):
        return self.type() == MASK_REGULAR_FILE

    def is_directory(self):
        return self.type() == MASK_DIRECTORY

class MBDB(object):
    def __init__(self, path):
        self.files = {}
        self.backup_path = path
        self.keybag = None
        # open the database
        mbdb = file(path + '/Manifest.mbdb', 'rb')

        # skip signature
        signature = mbdb.read(len(MBDB_SIGNATURE))
        if signature != MBDB_SIGNATURE:
            raise Exception("Bad mbdb signature")
        try:
            while True:                
                rec = MBFileRecord(mbdb)
                fn = rec.domain + "-" + rec.path
                sb = sha1(fn).digest().encode('hex')
                if len(sb) % 2 == 1:
                    sb = '0'+sb  
                self.files[sb] = rec
        except:
            mbdb.close()

    def get_file_by_name(self, filename):
        for (k, v) in self.files.iteritems():
            if v.path == filename:
                return (k, v)
        return None
    
    def extract_backup(self, output_path):
        for record in self.files.values():
            # create directories if they do not exist
            # makedirs throw an exception, my code is ugly =)
            if record.is_directory():
                try:
                    os.makedirs(output_path + '/' + record.path)
                except:
                    pass

        for (filename, record) in self.files.items():
            # skip directories
            if record.is_directory():
                continue
            self.extract_file(filename, record, output_path)
    
    def extract_file(self, filename, record, output_path):
        # adjust output file name
        if record.is_symbolic_link():
            out_file = record.target
        else:
            out_file = record.path
        
        file_data = self.read_file(filename, record)
        # write output file
        if file_data:
            print("Writing %s" % out_file)
            f = file(output_path + '/' + out_file, 'wb')
            f.write(file_data)
            f.close()

    def read_file(self, filename, record):
        # read backup file
        try:
            f = file(self.backup_path + '/' + filename, 'rb')
            file_data = f.read()
            f.close()
        except(IOError):
            warn("File %s (%s) has not been found" % (filename, record.path))
            return

        if record.encryption_key is not None and self.keybag: # file is encrypted!
            key = self.keybag.unwrapKeyForClass(record.protection_class, record.encryption_key[4:])
            if not key:
                warn("Cannot unwrap key")
                return
            file_data = AESdecryptCBC(file_data, key)
            padding = file_data[record.size:]
            if len(padding) > 16 or padding != chr(len(padding)) * len(padding):
                warn("Incorrect padding for file %s" % record.path)
            file_data = file_data[:record.size]
        return file_data

