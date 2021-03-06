#! /usr/bin/env python
# S.Rodney 2014.02.27

import os
import pyfits
# import exceptions

from stsci import tools
from drizzlepac import tweakreg, astrodrizzle
import stwcs


def RunTweakReg( fltfilestr='*fl?.fits', refcat=None, refim=None, 
                 wcsname='SNDRIZZLE', 
                 rfluxmax=None, rfluxmin=None, searchrad=1.0,
                 peakmin=None, peakmax=None, threshold=4.0,
                 fitgeometry='rscale',
                 interactive=False, clobber=False, debug=False ):
    if debug : import pdb; pdb.set_trace()

    #convert the input list into a useable list of images for astrodrizzle
    if type( fltfilestr ) == str :
        fltlist=tools.parseinput.parseinput(fltfilestr)[0]
    else : 
        fltlist = fltfilestr
        fltfilestr = ','.join( fltlist ).strip(',')

    # pre-clean any existing WCS header info
    # clearAltWCS( fltlist )       

    hdr1 = pyfits.getheader( fltlist[0] )
    instrument = hdr1['INSTRUME']
    detector   = hdr1['DETECTOR']
    camera = instrument + '-' + detector
    if camera == 'ACS-WFC' : 
        conv_width = 3.5
    elif camera == 'WFC3-UVIS' : 
        conv_width = 3.5
    elif camera == 'WFC3-IR' : 
        conv_width = 2.5
    else : 
        conv_width = 2.5

    # check first if the WCS wcsname already exists in the first flt image
    wcsnamelist = [ hdr1[k] for k in hdr1.keys() if k.startswith('WCSNAME') ]
    if wcsname in wcsnamelist and not clobber :
        print(
            "WCSNAME %s already exists in %s"%(wcsname,fltlist[0]) +
            "so I'm skipping over this tweakreg step." +
            "Re-run with clobber=True if you really want it done." )
        return( wcsname )

    if interactive : 
        while True : 
            print( "sndrizzle.register:  Running a tweakreg loop interactively.")
            tweakreg.TweakReg(fltfilestr, updatehdr=False, wcsname='TWEAK', 
                              see2dplot=True, residplot='both', 
                              fitgeometry=fitgeometry, refcat=refcat, refimage=refim,
                              refxcol=1, refycol=2, refxyunits='degrees', 
                              rfluxcol=3, rfluxunits='mag',
                              rfluxmax=rfluxmax, rfluxmin=rfluxmin,
                              searchrad=searchrad, conv_width=conv_width, threshold=threshold, 
                              separation=0.0, tolerance=1.5, minobj=10,
                              clean=(not debug) )
            print( "==============================\n sndrizzle.register:\n")
            userin = raw_input("Adopt these tweakreg settings? y/[n]").lower()
            if userin.startswith('y'): 
                print("OK. Proceeding to update headers.")
                break
            print("Current tweakreg/imagefind parameters:")
            printfloat("   rfluxmin = %.1f  # min mag for refcat sources", rfluxmin)
            printfloat("   rfluxmax = %.1f  # max mag for refcat sources", rfluxmax)
            printfloat("   searchrad  = %.1f  # matching search radius (arcsec)", searchrad )
            printfloat("   peakmin    = %.1f  # min peak flux for good sources", peakmin )
            printfloat("   peakmax    = %.1f  # max peak flux for good sources", peakmax )
            printfloat("   threshold  = %.1f  # detection threshold in sigma ", threshold )
            printfloat("   fitgeometry= %s  # fitting geometry [shift,rscale] ", fitgeometry )
            print('Adjust parameters using "parname = value" syntax.') 
            print('Enter "run" to re-run tweakreg with new parameters.') 
            while True : 
                userin = raw_input("   ").lower()
                if userin.startswith('run') : break
                try : 
                    parname = userin.split('=')[0].strip()
                    value = userin.split('=')[1].strip()
                except : 
                    print('Must use the "parname = value" syntax. Try again') 
                    continue
                if parname=='rfluxmin' : rfluxmin=float( value )
                elif parname=='rfluxmax' : rfluxmax=float( value )
                elif parname=='searchrad' : searchrad=float( value )
                elif parname=='peakmin' : peakmin=float( value )
                elif parname=='peakmax' : peakmax=float( value )
                elif parname=='threshold' : threshold=float( value )
                elif parname=='fitgeometry' : fitgeometry=value

    print( "==============================\n sndrizzle.register:\n")
    print( "  Final tweakreg run for updating headers.")
    tweakreg.TweakReg(fltfilestr, updatehdr=True, wcsname=wcsname,
                      see2dplot=False, residplot='No plot', 
                      fitgeometry=fitgeometry, refcat=refcat, refimage=refim,
                      refxcol=1, refycol=2, refxyunits='degrees', 
                      rfluxcol=3, rfluxunits='mag',
                      rfluxmax=rfluxmax, rfluxmin=rfluxmin,
                      searchrad=searchrad, conv_width=conv_width, threshold=threshold, 
                      separation=0.0, tolerance=1.5, minobj=10,
                      clean=(not debug) )
    return( wcsname )



def intraVisit( fltlist, peakmin=None, peakmax=None, threshold=4.0,
                interactive=False, clobber=False, debug=False ):
    """ 
    Run tweakreg on a list of flt images belonging to the same visit, 
    updating their WCS for alignment with the WCS of the first in the list. 

    When interactive is True, the user will be presented with the
    tweakreg plots (2d histogram, residuals, etc) to review, and will
    be given the opportunity to adjust the tweakreg parameters and
    re-run.
    """
    if debug : import pdb; pdb.set_trace() 
    wcsname = RunTweakReg(
        fltlist, refcat=None, wcsname='INTRAVIS', searchrad=1.0,
        peakmin=peakmin, peakmax=peakmax, fitgeometry='shift',
        threshold=threshold, interactive=interactive,  clobber=clobber )
    return( wcsname )


def toFirstim( fltlist, searchrad=1.0,
               peakmin=None, peakmax=None, threshold=4.0,
               interactive=False, clobber=False, debug=False ):
    """ 
    Run tweakreg on a list of flt images, updating their WCS for
    alignment with the WCS of the first file in the list.

    When interactive is True, the user will be presented with the
    tweakreg plots (2d histogram, residuals, etc) to review, and will
    be given the opportunity to adjust the tweakreg parameters and
    re-run.
    """
    if debug : import pdb; pdb.set_trace() 
    firstimfile = os.path.basename(fltlist[0])
    wcsname = RunTweakReg(
        fltlist, refcat=None, wcsname='FIRSTIM:%s'%firstimfile,
        searchrad=searchrad, peakmin=peakmin, peakmax=peakmax,
        threshold=threshold, interactive=interactive,
        clobber=clobber, debug=debug )
    return( wcsname )



def toRefim( filelist, refim, refcat=None,
             rfluxmax=27, rfluxmin=18, searchrad=1.0,
             peakmin=None, peakmax=None, threshold=4.0,
             interactive=False, clobber=False, debug=False ):
    """Run tweakreg on a list of flt or drz images to bring them into
    alignment with the given reference image, refim.  Optionally a
    refcat can be provided to define the absolute astrometric system
    and narrow down the list of allowed sources for matching.

    refim must be a CR-cleaned, drizzled image product.
    
    refcat must be a catalog with RA,DEC,MAG in columns 1,2,3.

    When interactive is True, the user will be presented with the
    tweakreg plots (2d histogram, residuals, etc) to review, and will
    be given the opportunity to adjust the tweakreg parameters and
    re-run.

    """
    if debug : import pdb; pdb.set_trace()
    
    wcsname = RunTweakReg(
        filelist, refim=refim, refcat=refcat,
        wcsname='REFIM:%s'%os.path.basename(refim),
        rfluxmax=rfluxmax, rfluxmin=rfluxmin, searchrad=searchrad,
        peakmin=peakmin, peakmax=peakmax, threshold=threshold,
        interactive=interactive, clobber=clobber, debug=debug )
    return( wcsname )


def clearAltWCS( fltlist ) : 
    """ pre-clean any alternate wcs solutions from flt headers"""
    from drizzlepac import wcs_functions
    from drizzlepac.imageObject import imageObject

    for fltfile in fltlist : 
        hdulist = pyfits.open( fltfile, mode='update' )
        extlist = range( len(hdulist) )
        extlist = []
        for ext in range( len(hdulist) ) : 
            if 'WCSNAME' in hdulist[ext].header : extlist.append( ext )
            stwcs.wcsutil.restoreWCS( hdulist, ext, wcskey='O' )
        if len(extlist) : 
            wcs_functions.removeAllAltWCS(hdulist, extlist)
        hdulist.flush()
        hdulist.close()


def printfloat( fmtstr, value ):
    """ Print a float value using the given format string, handling
    None and NaN values appropriately
    """
    try :
        print( fmtstr % value ) 
    except : 
        pct = fmtstr.find('%')
        f = pct + fmtstr[pct:].find('f') + 1
        if value == None : 
            print( fmtstr[:pct] + ' None ' + fmtstr[f:] )
        elif value == float('nan') :
            print( fmtstr[:pct] + ' NaN ' + fmtstr[f:] )
        else : 
            print( fmtstr[:pct] + ' ??? ' + fmtstr[f:] )


def mkSourceCatalog( imfile, computesig=True, skysigma=0,
                     threshold=4.0, peakmin=None, peakmax=None ) :
    import pywcs
    from drizzlepac import catalogs

    image = pyfits.open( imfile )
    hdr = image[0].header
    data = image[0].data

    instrument = hdr['INSTRUME']
    detector   = hdr['DETECTOR']
    camera = instrument + '-' + detector
    if camera == 'ACS-WFC' : 
        conv_width = 3.5
    elif camera == 'WFC3-UVIS' : 
        conv_width = 3.5
    elif camera == 'WFC3-IR' : 
        conv_width = 2.5
    else : 
        conv_width = 2.5


    # PROBLEM :
    err = """
AttributeError: 'WCS' object has no attribute 'extname'
> /usr/local/Ureka/python/lib/python2.7/site-packages/drizzlepac/catalogs.py(268)__init__()
    267         Catalog.__init__(self,wcs,catalog_source,**kwargs)
--> 268         if self.wcs.extname == ('',None): self.wcs.extname = (0)
    269         self.source = pyfits.getdata(self.wcs.filename,ext=self.wcs.extname)
    """

    wcs = pywcs.WCS( hdr )
    wcs = pywcs.WCS( header=hdr, fobj=image )

    imcat = catalogs.generateCatalog(wcs, mode='automatic',catalog=None, computesig=computesig, skysigma=skysigma, threshold=threshold, peakmin=peakmin, peakmax=peakmax, conv_width=conv_width )
    return( imcat )


