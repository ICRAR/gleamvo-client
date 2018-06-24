
"""
GLEAM VO client / API

Dependency: pip install -U astropy

Usage example
====
import gleam_client
gleam_client.vo_get(50.67, -37.02, 1.0, freq=['072-080', '080-088'],
                    proj_opt='SIN', download_dir='/tmp')
====

Author: chen.wu@icrar.org
"""
import os, warnings
try:
    from urllib2 import urlopen, quote, HTTPError
    python_ver = 2
except:
    from urllib.request import urlopen, quote, HTTPError
    from io import StringIO, BytesIO
    python_ver = 3
from astropy.io.votable import parse_single_table

PROJ_OPTS = ['ZEA', 'ZEA_regrid', 'SIN']
VO_URL = "http://{0}/gleam_postage/q/siap.xml?FORMAT=ALL&VERB=2"\
      "&NTERSECT=OVERLAPS&"

class GleamClientException(Exception):
    pass

def create_filename(ra, dec, ang_size, freq, error=False):
    """
    You can write your own create_filename function however you like
    Here is a dummy example
    """
    if (error):
        return "error_{0}_{1}_{2}_{3}.html".format(ra, dec, ang_size, freq)
    else:
        return "{0}_{1}_{2}_{3}.fits".format(ra, dec, ang_size, freq)

def download_file(url, ra, dec, ang_size, freq, download_dir,
                  file_name_func=None, clobber=True):
    """

    """
    if (file_name_func is None):
        file_name_func = create_filename
    filename = file_name_func(ra, dec, ang_size, freq)
    fulnm = download_dir + "/" + filename
    if (os.path.exists(fulnm) and not clobber):
        print("File '%s' exists already" % fulnm)
        return
    try:
        u = urlopen(url, timeout=200)
    except HTTPError as hpe:
        if (500 == hpe.code):
            err_msg = None
            try:
                err_msg = hpe.fp.read()
                if (err_msg):
                    filename = file_name_func(ra, dec, ang_size, freq, error=True)
                    fulnm = download_dir + "/" + filename
                    with open(fulnm, 'wb') as f:
                        f.write(err_msg)
                    print("Error info at '{0}'".format(fulnm))
                    return
                else:
                    raise hpe
            except:
                raise hpe
        else:
            raise hpe

    if (u.headers['content-type'] == 'image/fits'):
        # we know for sure this is a fits image file
        # filename = "{0}_{1}_{2}.fits".format(ra, dec, freq)
        derror = False
    else:
        filename = file_name_func(ra, dec, ang_size, freq, error=True)
        derror = True

    if (3 == python_ver):
        block_sz = 4096
    else:
        block_sz = u.fp.bufsize
    fulnm = download_dir + "/" + filename
    with open(fulnm, 'wb') as f:
        while True:
            buff = u.read(block_sz)
            if not buff:
                break

            f.write(buff)
        if (derror):
            msg = "Error info at '{0}'".format(fulnm)
        else:
            msg = "File '{0}' downloaded".format(fulnm)
        print(msg)

def vo_get(ra, dec, ang_size, proj_opt='ZEA',
                   download_dir=None,
                   vo_host='gleam-vo.icrar.org',
                   freq=[], clobber=True, file_name_func=None,
                   alter_cmd=None, **kwargs):
    """
    ra, dec,
    ang_size:	    Position and angular size in degrees (float)

    download_dir:	Directory where images will be saved to (String).
			        Leaving it None (default) will not download any images

    proj_opt:   	Legitimit values (String):
                	'ZEA'   (default)
                	'ZEA_regrid'
                	'SIN'

    freq:       	A list of frequencies, e.g. ['223-231' '216-223']
                	An empty list means ALL

    clobber:		Overwrite existing images? (Boolean)

    file_name_func:
                	An optional function to create file name as you like.
                	Leaving it None will use the default "create_filename()"
    """
    if (ang_size > 5.0):
        raise GleamClientException("Angular size %.1f > 5.0 (degrees)"\
         % ang_size)

    if (download_dir and (not os.path.exists(download_dir))):
        raise GleamClientException("Invalid download dir: {0}"\
              .format(download_dir))

    if (not proj_opt in PROJ_OPTS):
        raise GleamClientException("Invalid projection: '{0}'."\
              " Should be one of {1}"\
              .format(proj_opt, PROJ_OPTS))

    url = VO_URL.format(vo_host)
    pos_p = 'POS=%s' % quote('{0},{1}'.format(ra, dec))
    proj_opt_p = 'proj_opt=%s' % proj_opt
    size_p = 'SIZE=%f' % (float(ang_size))
    url += '&'.join([pos_p, proj_opt_p, size_p])
    #print url
    u = urlopen(url, timeout=200)
    warnings.simplefilter("ignore")
    if (2 == python_ver):
        try:
            tbl = parse_single_table(u.fp).array
            #print(tbl)
        except IndexError as ierr:
            raise GleamClientException('No results in the VO query: %s' % str(ierr))
    elif (3 == python_ver):
        buf = []
        while True:
            buff = u.read(1024)
            if not buff:
                break
            buf.append(buff.decode("utf-8"))
        vo_table = ''.join(buf)
        #print(vo_table)
        fp = BytesIO(vo_table.encode('utf-8'))
        tbl = parse_single_table(fp).array
        #print(tbl)
    else:
        raise Exception('Unknown Python version %d' % python_ver)
    warnings.simplefilter("default")
    ignore_freq = len(freq) == 0
    c = 0
    if (len(kwargs) > 0):
        tail = '&'.join(['{0}={1}'.format(k, v) for k, v in kwargs.items()])
    else:
        tail = None
    for row in tbl:
        r_freq = row[0]
        r_url = row[1]
        if (3 == python_ver):
            r_freq = r_freq.decode("utf-8")
            r_url = r_url.decode("utf-8")
        if (ignore_freq or r_freq in freq):
            if (tail):
                r_url += '&%s' % tail
            if (alter_cmd is not None and len(alter_cmd) > 0):
                r_url = r_url.replace('GLEAMCUTOUT', alter_cmd)
            if (download_dir):
                download_file(r_url, ra, dec, ang_size, r_freq,
                              download_dir, clobber=clobber,
                              file_name_func=file_name_func)
            else:
                print(r_freq, r_url)
            c += 1
    if (c == 0):
        warnings.warn("No results from the VO query")

def usage_examples():
    """
    Three examples to cutout Fornax A

    """
    ra = 50.67
    dec = -37.20
    ang_size = 1.0
    freq_low = ['072-080', '080-088']
    projection = 'SIN'
    dl_dir = '/tmp'

    # example 1 - just to see what is going to be downloaded (low frequencies)
    vo_get(ra, dec, ang_size, proj_opt=projection, freq=freq_low)

    # example 2 - now really get them
    vo_get(ra, dec, ang_size, proj_opt=projection, freq=freq_low, download_dir=dl_dir)

    # example 3 - download all frequencies (Not specifying freq means ALL freqs)
    # vo_get(ra, dec, ang_size, proj_opt=projection, download_dir=dl_dir)

if __name__ == '__main__':
    usage_examples()
