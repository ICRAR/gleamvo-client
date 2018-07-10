"""
GLEAM4Jy VO client / API

Work with both Python 2 and Python 3

Dependency: pip install -U astropy

Usage example
====
import gleam_4jy_client
gleam_4jy_client.vo_get('23:22:03 -24:10:44', download_dir='/tmp')
====
Any issues, please contact: chen.wu@icrar.org
"""
import os, warnings
try:
    from urllib2 import urlopen, quote, HTTPError
    python_ver = 2
except:
    from urllib.request import urlopen, quote, HTTPError
    from io import StringIO, BytesIO
    python_ver = 3

from gleam_client import GleamClientException
from astropy.io.votable import parse_single_table

g_url = "http://mwa-web.icrar.org/gleam_4jy/q/siap.xml?FORMAT=ALL&VERB=2"\
      "&NTERSECT=OVERLAPS&"

ngas_url = 'http://store06.icrar.org:7777/RETRIEVE?file_id=%s'


def download_file(fid, download_dir):
    fulnm = '%s/%s' % (download_dir, fid)
    if (os.path.exists(fulnm) and not clobber):
        print("File '%s' exists already" % fulnm)
        return
    try:
        download_url = ngas_url % fid
        u = urlopen(download_url, timeout=200)
    except Exception as exp:
        print('Failed to download from %s: %s' % (download_url, str(exp)))
        return

    if (3 == python_ver):
        block_sz = 1024 * 256
    else:
        block_sz = u.fp.bufsize
    with open(fulnm, 'wb') as f:
        while True:
            buff = u.read(block_sz)
            if not buff:
                break

            f.write(buff)
    print("File %s saved to %s" % (fid, fulnm))

def vo_get(pos, sr=5.0, download_dir=None):
    """
    pos - Position string, i.e. '23:22:03 -24:10:44' or '23:22:03,-24:10:44'
    sr - search radius in arcmin, default here is 5 arcmin
    """
    if (download_dir and (not os.path.exists(download_dir))):
        raise GleamClientException("Invalid download dir: {0}"\
              .format(download_dir))

    url = '%s&POS=%s&sr=%s' % (g_url, quote(pos), quote(str(sr)))
    #print(url)
    u = urlopen(url, timeout=200)
    warnings.simplefilter("ignore")
    if (2 == python_ver):
        fp = u.fp
    elif (3 == python_ver):
        buf = []
        while True:
            buff = u.read(1024)
            if not buff:
                break
            buf.append(buff.decode("utf-8"))
        vo_table = ''.join(buf)
        fp = BytesIO(vo_table.encode('utf-8'))
    else:
        raise Exception('Unknown Python version %d' % python_ver)
    try:
        tbl = parse_single_table(fp).array
    except IndexError as ierr:
        raise GleamClientException('No results in the VO query: %s' % str(ierr))
    warnings.simplefilter("default")
    #print(tbl)
    for row in tbl:
        fid = row[-2]
        if (3 == python_ver):
            fid = fid.decode("utf-8")
        #print(fid)
        if (download_dir is not None):
            download_file(fid, download_dir)
        else:
            print('File %s' % fid)

# if __name__ == '__main__':
#     vo_get('23:22:03 -24:10:44', download_dir='/tmp')
#     vo_get('22:23:47 -02:01:39')
