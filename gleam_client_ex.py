"""

"""
from gleam_client import vo_get

rms = 1

def create_my_filename(ra, dec, ang_size, freq, error=False):
    """
    You can change this function to control the file name
    """
    suffix = '-rms' if rms == 1 else '-bkg'
    if (error):
        return "error_{0}_{1}_{2}_{3}.html".format(ra, dec, ang_size, 'white' + suffix)
    else:
        return "{0}_{1}_{2}_{3}.fits".format(ra, dec, ang_size, 'white' + suffix)

def usage_examples():
    """
    An example to cutout bkg and rms of Fornax from IDR-6
    """
    #  DO NOT CHANGE these two parameters
    freq_low = ['170-231'] # you will get 'white' one
    vo_host = 'mwa-web.icrar.org' # currently our ICRAR server supports this

    # feel free to change the following
    ra = 50.67
    dec = -37.20
    ang_size = 1.0
    projection = 'SIN'
    dl_dir = '/tmp'
    global rms

    rms = 1 # set flag to get rms file
    vo_get(ra, dec, ang_size, proj_opt=projection, freq=freq_low,
           download_dir=dl_dir, alter_cmd='GLEAMCUTOUTEX',
           vo_host=vo_host, rms=rms, file_name_func=create_my_filename)

    rms = 0 # set flag to get the bkg file
    vo_get(ra, dec, ang_size, proj_opt=projection, freq=freq_low,
           download_dir=dl_dir, alter_cmd='GLEAMCUTOUTEX',
           vo_host=vo_host, rms=rms, file_name_func=create_my_filename)


if __name__=='__main__':
    usage_examples()
