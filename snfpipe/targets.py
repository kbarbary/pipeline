
"""Parsing the HTML page for IAUC supernovae."""

import re
import string

from .utils import RADec, utc_to_jd

__all__ = ["IAUCTarget", "SNFTarget", "read_iauc_targets", "read_snf_targets"]


class IAUCTarget(object):
    def __init__(self, Galaxy, Mag, Name, Ra, Dec, Type, Iauc):
        self.Galaxy = Galaxy
        self.Mag = Mag
        self.Name = Name
        self.Ra = Ra
        self.Dec = Dec
        self.Type = Type
        self.Iauc = Iauc

    def __repr__(self):
        return ("IAUCTarget({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})"
                .format(self.Galaxy, self.Mag, self.Name, self.Ra,
                        self.Dec, self.Type, self.Iauc))


class SNFTarget(object):
    def __init__(self, Name, OName, Ra, Dec, VMag, Type, Kind, File, x, y):
        self.Name = Name
        self.OName = OName
        self.Ra = Ra
        self.Dec = Dec
        self.VMag = VMag
        self.Type = "Unknown"
        self.Kind = None
        self.File = None
        self.x = -1
        self.y = -1

    def __repr__(self):
        return ("SNFTarget({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, "
                "{!r}, {!r})"
                .format(self.Name, self.OName, self.Ra, self.Dec, self.VMag,
                        self.Type, self.Kind, self.File, self.x, self.y))


def read_iauc_line(l):

    #RP - welcome to regex hell
    m = re.search('(?P<sn>\d{4}[A-Z]?[a-z]{0,2})\s{2,3}'
                  # this may happen to be only whitespace
                  '(?P<galinfo>.+)'
                  # CBET / IAUC
                  '(?P<galref>[A-Z]{4}\s+\d{1,})\s+'
                  '(?P<ra>\d+\s+\d+\s+\d+(\.\d+)?)\s+'
                  '(?P<dec>[\+\-\_]?\s?\d+\s+(\d+\s+)?\d+(\.\d+)?)\s+'
                  '(?P<ref>([A-Z]{4}\s+\d{1,})\s+|\s+)'
                  '(?P<type>.+(?=\d{4}[A-Z]?[a-z]{0,2}))', l).group
    
    # test is the galaxy info is filled (ie. we can find a date)
    if re.search('(.+(?=\d{4}\s+\d{2}))', m('galinfo')) is not None:

        m2 = re.search('(?P<galaxy>.+)'
                       '(?P<date>\d{4}\s+\d{2}\s+\d{2})\s+'
                       '(?P<galra>\d{1,}\s+\d{1,}\.\d)\s+'
                       '(?P<galdec>\+?\-?\s?\d+\s+\d+)\s+'
                       '(?P<offmag>.+)', m('galinfo')).group

        galaxy = m2('galaxy').strip()
        try:
            mag = float(m2('offmag').strip().split()[-1])
        except (ValueError, IndexError):
            mag = 99.

    else:
        galaxy = m('galinfo').strip()[:16].strip()
        mag = 99.

    name = m('sn').strip()

    #make proper RA DEC for RaDec usage
    ra_str = ' '.join(m('ra').strip().split())
    dec_str = ' '.join(m('dec').strip().split()).replace('_','-')
    ra = RADec(ra_str, "RA").Deg()
    dec = RADec(dec_str, "DEC").Deg()

    type = m('type').strip()
    try:
        iauc = int(m('ref').strip().split()[-1])
    except (ValueError, IndexError):
        iauc = 0

    return IAUCTarget(galaxy, mag, name, ra, dec, type, iauc)


def validate_iauc_targets(targets):
    """Check that there are no weird entries in the IAUC list

    One should add tests here for improperly formatted IAUC entries.

    Parameters
    ----------
    targets: list of IAUCTarget instances
    """

    # are there SNe with exactly the same RA,Dec? (True if all locations are
    # unique)
    same_radec = (len([(tgt.Ra, tgt.Dec) for tgt in targets]) ==
                  len(set([(tgt.Ra, tgt.Dec) for tgt in targets])))
    if not same_radec:
        raise RuntimeError("two or more SNe with exactly the same RA, Dec")

    # are there SNe with a galaxy name starting with a digit?
    galaxy_name = len([tgt for tgt in targets
                       if tgt.Galaxy and tgt.Galaxy[0] in string.digits]) == 0
    if not galaxy_name:
        raise RuntimeError('there are galaxy names starting with a digit')


def read_iauc_targets(fname):
    """Parse IAUCTargets from HTML page"""

    html_doc = open(fname).read()

    html_doc = html_doc[html_doc.find('<pre>')+6 : html_doc.find('</pre>')]

    # remove HTML tags and get only SNe from >= 2000
    lines = [i for i in re.sub('<.+?>', '', html_doc).split('\n')
             if i and i[0] in string.digits and int(i[:4]) >= 2000]

    targets = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            targets.append(read_iauc_line(line))

    validate_iauc_targets(targets)

    return targets


def read_snf_target_line(words, kind):
    words = [word.strip() for word in words]

    if kind in ("StdStar", "DbleStar"):
        oname, ra_str, dec_str, file_, x_str, y_str, vmag, type_ = words[0:8]
        name = oname

    elif kind == "Candidate":
        name, oname, _, ra_str, dec_str, file_, x_str, y_str = words[0:8]
        if not name:
            name = oname
        if not oname:
            oname = None
        vmag = "100.0"
        type_ = "Unknown"

    else:
        raise ValueError("unknown kind: {}".format(kind))

    # parse RA, Dec to decimal
    ra = RADec(ra_str, "RA").Deg()
    dec = RADec(dec_str, "Dec").Deg()

    # parse x, y location
    try:
        x = float(x_str)
        y = float(y_str)
    except ValueError:
        x = -1
        y = -1

    return SNFTarget(name, oname, ra, dec, float(vmag), type_, kind, file_,
                     x, y)


def read_snf_targets(fname):
    """Read the FindingChart format file """

    f = open(fname)
    targets = []

    # loop on the file
    kind = ""
    for line in f.readlines():
        line = line.strip()
        if line.startswith("#"):
            kind = line.split()[1].strip()
        else:
            words = line.split('|')
            if len(words) > 4 and words[1].strip() != "^":
                    targets.append(read_snf_target_line(words[1:], kind))

    f.close()

    return targets


class Run(object):
    """
    Parameters
    ----------
    year : int
        2-digit year.
    day : int
        3-digit day.
    run : int
        3-digit run.
    nbexp : int
        Total number of associated exposures, same as len(exp)
    type_ : str
        Type of run. E.g., 'OBJECT', 'DARK', 'BIAS', 'ARC', etc
    script : str
        Online script name used to take this run
    option : str
        Option given to the script
    target : str
        Target name. [needed only for filling the object, not in DB]
    kind : str
        One of 'StdStar', 'Calib', 'SDSU'.
    date : float
        Julian Date of start of script execution


    Other Attributes
    ----------------
    idrun : str
        8-character string built from year, day, run: 'YYDDDRRR'
    quality : int
        Run quality flag: 0 unknoown, 1 Good (default), 2 Warning, 3 Error
    qualitys : str
        Run Quality string (gives detail on the quality flag):

        - PtE: changing pointing during the run: not used for dark , bias ..
        - MtE: unexpected moving target during a run
        - MpE: unexpected moving pointing  during a run
        - TmE: Light path status:  third mirror out

        Used for main shutter exposure only ..X =
        G (Good, default not written) ,W (Warning) , E (Error)   
    targetid : Target
        The Target associated to this run
        (for the moment only run with a pose fclass 17)
    exp : list of Exposure
        Associated Exposures.
    """

    def __init__(self, year, day, run, nbexp, target, kind, type_, date,
                 script, option, quality=1, qualitys="", targetid=None,
                 exp=None):
        self.year = year
        self.day = day
        self.run = run
        self.nbexp = nbexp
        self.target = target
        self.kind = kind
        self.type_ = type_
        self.date = date
        self.script = script
        self.option = option

        # attributes with defaults
        self.idrun = "%02d%03d%03d" % (self.year, self.day, self.run)
        self.quality = quality
        self.qualitys = qualitys
        self.targetid = targetid
        if exp is None:
            exp = []
        self.exp = exp

    def __repr__(self):
        return ("Run(year={!r}, day={!r}, run={!r}, nbexp={!r}, target={!r}, "
                "kind={!r}, type_={!r}, date={!r}, script={!r}, option={!r}, "
                "quality={!r}, qualitys={!r}, targetid={!r}, exp={!r}"
                .format(self.year, self.day, self.run, self.nbexp, self.target,
                        self.kind, self.type_, self.date, self.script,
                        self.option, self.quality, self.qualitys,
                        self.targetid, self.exp))


class Exposure(object):
    """Class build from the snifs_run records
     'IdExp'    : str(11)    , Patern unique for this exposure: YYDDDRRREVT
     'Event'    : int, 3 dig , event number
     'Run'      : Pointer    , Pointer on parent Run
     'Pose'     : List Point , List of Pointer On the associated pose(s)
     'Channel'  : byte ,1,2,4, Binary patern for B(4)R(2)P(1)
     'Date'     : Float, 7.6 , Julian date of the exposure
     'Fclass'   : Int, 3 dig , Fclass
     'OpenTime' : Float      , Main shutter Open time in second
     'MidTime'  : Float, 7.6 , Julian date for the Midle of the exposure
     'AltSun'   : Float,     , Sun Altitude angle at the midle of the exposure
     'AltMoon'  : Float      , Mon altitude at the middle of the exposure
     'MoonIllFrac': Float     , Mon illumination fraction at the middle of the exposure
     'ObjMoon'  : Float      , Angle Object <-> Moon at the midle of the exposure
     'MidAirMass': Float      , Air Mass at the midle of the exposure
     'MidHa'    : Float      , HA at the midle of the exposure
     'ParAng'   : Float      , Paralactic angle at the middle of the exposure
     'LunSky'   : Float      , LUNAR part of sky brightness, in V magnitudes per square arcsecond, mid expo
     'Ra'       : Float      , Ra in Deg eq. 2000 of the target
     'Dec'      : Float      , Dec in Deg eq. 2000 of the target
     'RaPoint'  : Float      , Ra in Deg eq. 2000 of where the telescope says to point ( with offset)
     'DecPoint' : Float      , Dec in Deg eq. 2000 of where the telescope says to point ( with offset)
     'DecTel'   : Float      , Dec , Raw Pointing of the telescope (no offset)
     'RaTel'    : Float      , Ra , Raw Pointing of the telescope (no offset)
     'Ha'       : Float      , HA in deg
     'Zd'       : Float      , Zenit distance in degree
     'AirMass'  : Float      , Airmass
     'Guide'    : 0/1/2/3    , 0 unguided , 1 guided (good) , 2 poor guiding , 3 bad guiding
     'GuideX'   : Float      ,     1-4096 x guide star ( 0 guided but information on location lost )
     'GuideY'   : Float      ,     1-4096 y guide star
     'SeeingInst': Float      , Instantaneous seeing (  average of Instantaneous Seing )
     'Seeing'   : Float      , Estimated Seeing from guiding ( Seing including guiding effect , if guided or spectro if not guided)
     'QuideF'   : Float      , Quality word to measure a flat guiding flux
     'QuideS'   : Float      , Quality word to measure the stability of the guiding over the exposure lenght
     'Interrupt': 0/1        , flag exposure interrupted before the end
     'Filter'   : str(20)    , Filter Name
     'FocusB'   : int, 4 dig , Current Focus for B channel
     'FocusR'   : int, 4 dig , Current Focus for R channel
     'FilterPos': int, 4 dig , Filter wheel position
     'FilterReq': int, 4 dig , Filter wheel position requested
     'FocusReqB': int, 4 dig , Focus Requested for B channel
     'FocusReqR': int, 4 dig , Focus Requested for R channel
     'LampDome' : int, 3 dig , Lamp dome intencity
     'LampConB' : int, 0/1   , Continuum B Lamp On (1) Off (0) 0
     'LampConR' : int, 0/1   , Continuum R lamp On (1) Off (0)
     'LampArcB' : int, 0/1   , Arc B Lamp On (1) Off (0)
     'LampArcR' : int, 0/1   , Arc R Lamp On (1) Off(0)
     'Pop'      : int, 0/1   , Pop On(1) off(0)
     'SnifsTemp': Float      , Snifs temperature
     'Pressure' : Float      , pressure im mb  from CFH meteo station
     'Humidity' : int        , humidity in % from CFH meteo station
     'Temp'     : Float      , temperature in deg from CFH meteo station
     'WindDir'  : int        , Wind direction from CFH meteo station
     'WindSpeed': Float      , Wind in kts from CFH meteo station
     'TelTemp'  : Float      , top telescope temperature
     'TelFocus' : Float      , Telescope current focus
     'TelHumidIn': Float      , Inside Humidity
     'TelHumidOut': Float      , Outside Humidity
     'TelWind'  : Float      , Wind speed
     'SnifsHumid': Float      , Humidity from SNIFS humidity probe
     'SnifsHTemp': Float      , Tmeperature from SNIFS humidity probe
     'LightFlu' : Float      , Fluoresent light status ( fraction of the time on during the exposure  )
     'LightInc' : Float      , Incandesent light status ( fraction of the time on during the exposure  )
     'Quality'  : Int, 1dig ( 0/1/2/3 )  , Event Quality flag
     'QualityS'  : str(40)  :  Evt Quality string (gives detail on the quality flag)
                    PcE      : Main shutter exposure (fclas = 17,12,52 ) without P channel ????
    """

    def __init__(self, words, run, event):
        if words[6] == 'init':
            raise ValueError("Expected to not find 'init' in 7th word")

        year = int(words[0])
        day = int(words[1])
        run_ = int(words[2])

        # check that run is consistent
        if run.year != year or run.day != day or run.run != run_:
            raise ValueError("run year/day/run does not match words")

        self.IdExp = "%02d%03d%03d%03d" % (year, day, run_, event)
        self.Event = event
        self.Quality = 1
        self.QualityS = ""

        # get the self.Channel # we can have up to 5 channel: R B P S T
        # So they will be from pos 6 to pos 11 at max
        i_max = 11
        self.Channel = 0
        for i in range(6, min(len(words), 11)):
            if len(words[i]) > 1:
                i_max = i
                break
            # analyse the channels found
            if words[i] == "P":
                self.Channel += 1
            elif words[i] == "R":
                self.Channel += 2
            elif words[i] == "B":
                self.Channel += 4

        # We fill the date , for B channel alone this could be usefull
        # for 2004 and 2005 data
        self.Date = utc_to_jd(re.search('==>(.*)',
                                        ' '.join(words[i_max:])).group(1))
        self.MidTime = self.Date

        # self.Date=None
        # self.MidTime=None
        self.Run = run_
        run.Exp.append(self)
        self.Pose  = []
        # Exposure type
        if run.Type == "ON":
            self.Fclass = 902
        elif run.Type == "OFF":
            self.Fclass = 903
        elif run.Type == "KILL":
            self.Fclass = 904
        else:
            self.Fclass = None

        # Extra info on exposure
        self.Guide=0
        self.GuideX=-1.
        self.GuideY=-1.
        self.SeeingInst=-1.
        self.Seeing=-1.
        self.GuideF=0.
        self.GuideS=0.
        self.Interrupt=0
        #
        self.OpenTime=None
        self.Ra=None
        self.Dec=None
        self.RaPoint=None
        self.DecPoint=None
        self.DecTel=None
        self.RaTel =None
        self.AirMass=None
        self.Ha=None
        self.Zd=None
        self.Azimuth=None
        self.Altitude=None
        # Skycalc parameter
        self.AltSun=None
        self.AltMoon=None
        self.MoonIllFrac=None
        self.ObjMoon=None
        self.MidAirMass=None
        self.MidHa=None
        self.ParAng=None
        self.LunSky=None
        # SNIFS state
        self.Filter="Unknown"
        self.LampConB=None
        self.LampConR=None
        self.LampArcB=None
        self.LampArcR=None
        self.LampDome=None
        self.SnifsTemp=None
        self.Pop=None
        self.FocusB=None
        self.FocusR=None
        self.FilterReq=None
        self.FilterPos=None
        self.FocusReqB=None
        self.FocusReqR=None
        # Telescope & Weather info
        self.Pressure=None
        self.Humidity=None
        self.Temp=None
        self.SnifsHumid=None
        self.SnifsHTemp=None
        self.LightFlu=None
        self.LightInc=None
        self.WindDir=None
        self.WindSpeed=None
        self.TelTemp =None
        self.TelFocus=None
        self.TelHumidIn=None
        self.TelHumidOut=None
        self.TelWind =None


def read_run_line(line):
    """Parse a Run from a line of a log file.

    Such lines should have 'init' as the 7th word.

    Parameters
    ----------
    line : str

    Returns
    -------
    run : Run
    """

    # Mapping from script to type_ for some scripts
    TYPES = {"do_object": "OBJECT",
             "do_photo": "PHOTO",
             "do_target": "OBJECT",
             "do_screen": "SCREEN",
             "do_fchart": "FCHART",
             "do_acqref": "ACQREF",
             "point_object": "ACQUISITION"}

    # Mapping from script to (target, kind, type_)
    TKT = {"visual_acq":    ("unknown",        "unknown", "ACQUISITION"),
           "visual_setup":  ("unknown",        "unknown", "ACQUISITION"),
           "imaging_setup": ("unknown",        "unknown", "ACQUISITION"),
           "grabit":        ("",               "grabit",  "ACQUISITION"),
           "take_guide":    ("",               "guide",   "GUIDE"),
           "do_dark":       ("no light",       "Calib",   "DARK"),
           "do_bias":       ("no light ",      "Calib",   "BIAS"),
           "do_arc":        ("internal light", "Calib",   "ARC"),
           "do_focus":      ("internal light", "Calib",   "FOCUSSPEC"),
           "ultrafocus":    ("unknown",        "Calib",   "FOCUSTELE"),
           "do_continuum":  ("internal light", "Calib",   "CONTINUUM"),
           "do_dome":       ("external light", "Calib",   "DOME"),
           "do_sky":        ("external light", "Calib",   "SKYFLAT"),
           "do_skyflat":    ("external light", "Calib",   "SKYFLAT"),
           "do_twilight":   ("external light", "Calib",   "SKYFLAT"),
           "lamp_respons":  ("internal light", "Calib",   "ARC"),
           "do_clean":      ("no light",       "SDSU",    "CLEAN"),
           "SNIFS_off":     ("no light",       "SDSU",    "OFF"),
           "SNIFS_kill":    ("no light",       "SDSU",    "KILL"),
           "SNIFS_on":      ("no light",       "SDSU",    "ON")}

    # Mapping from etype.lower() to (target, kind, type_),
    # only for script == "take_expo". Default to all "unknown" if key missing.
    TKT_TAKE_EXPO = {"arc":       ("internal light", "Calib",   "ARC"),
                     "continuum": ("internal light", "Calib",   "CONTINUUM"),
                     "flat":      ("internal light", "Calib",   "CONTINUUM"),
                     "dome":      ("external light", "Calib",   "DOME"),
                     "sky":       ("external light", "Calib",   "SKYFLAT"),
                     "object":    ("unknown",        "unknown", "unknown"),
                     "bias":      ("no light ",      "Calib",   "BIAS"),
                     "dark":      ("no light",       "Calib",   "DARK")}

    words = line.split()

    # check that the line is really a run
    if words[6] != 'init':
        raise ValueError("log file line {!r} doesn't look like a run"
                         .format(line))

    year = int(words[0])
    day = int(words[1])
    run = int(words[2])
    nbexp = int(words[4])

    # get script and option
    try:
        script = re.search('([^/]\w+)$', words[3]).group(1).strip()
    except AttributeError:
        script = words[3]

    try:
        option = re.search('[^(].*',
                           re.search('(?=\().*(?=\))', line).group(0)).group(0)
    except AttributeError:
        option = ""


    if script in TYPES:
        type_ = TYPES[script]

        # For this set of scripts, `target` and `kind` are parsed from
        # the options differently depending on the specific script.
        if script in ("do_object", "do_photo"):
            target_re = '-o (.*?)(?: -[a-zA-Z].*)?$'
            kind_re = '-d (.*?)(?: -[a-z] .*)?$'
        elif script in ("point_object", "do_fchart", "do_target", "do_screen",
                        "do_acqref"):
            target_re = '-o (.*?)(?: -[a-z].*)?$'
            kind_re = '-k (.*?)(?: -[a-z] .*)?$'
        else:
            raise RuntimeError("unknown script type")


        try:
            target = re.search(target_re, option).group(1).strip()
        except AttributeError:
            target = "unknown"
        try:
            kind = re.search(kind_re, option).group(1).strip())
        except AttributeError:
            kind = "unknown"
            
    elif script in TKT:
        target, kind, type_ = TKT[script]

    elif script == "take_expo":
        etype = re.search('-e (.*?)(?: -[a-z].*)?$',option).group(1).strip()
        if etype in TKT_TAKE_EXPO:
            target, kind, type_ = TKT_TAKE_EXPO[etype]
        else:
            target, kind, type_ = ("unknown", "unknown", "unknown")

    # Julian date of the exposure
    date = utc_to_jd(re.search('==>(.*)', line).group(1))

    return Run(year, day, run, nbexp, target, kind, type_, date, script,
               option)

def read_run_logfile(fname):
    """Parse a snifs_run_YY_DDD log file.

    Returns
    -------
    runs : list of Run
    exposures : list of Exposure
    """

    f = open(fname)
    runs = []
    exposures = []

    for line in f:
        line = line.strip()

        # check that the first thing on the line is a year like "08" or "14".
        # (This actually only checks that the first digit is either "0" or "1".)
        if re.search('^[01]',line) is None:
            continue

        words = line.split()

        if words[6] == 'init':
            # This is a new run
            runs.append(read_run_line(words))
            event_old = 1
            event_max = int(words[4])
        else:
            # NC 31-03-2015
            # The number of event is always set to 1 for do_scala
            # This will create 100 exposures, and some of them
            # will have no associated pose, but they will be removed
            # later in FlagRunKind
            if os.path.basename(words[3]).startswith('do_scala'):
                event = 100
            else:
                event = int(words[5])+1
            for n in range(event_old, event):
                # This is a pose in this run ,
                exposures.append(Exposure(words, runs[-1], n))
            event_old = event

        # TODO: check for incomplet run
        # for n in range(event_old,event_max):
        #   check if the event n exist ...

        # TODO: we should check than event_old <= event_max + 1 ,
        # and complain if it's not the case

    f.close()

    return runs, exposures
