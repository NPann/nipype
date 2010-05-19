import os
import tempfile
import shutil

from nipype.testing import (assert_equal, assert_not_equal, assert_raises,
                            with_setup, TraitError, parametric)

from nipype.utils.filemanip import split_filename
import nipype.interfaces.fsl.preprocess as fsl
from nipype.interfaces.fsl import Info
from nipype.interfaces.base import InterfaceResult, File

def fsl_name(obj, fname):
    """Create valid fsl name, including file extension for output type.
    """
    ext = Info.outputtype_to_ext(obj.inputs.outputtype)
    return fname + ext

tmp_infile = None
tmp_dir = None
def setup_infile():
    global tmp_infile, tmp_dir
    ext = Info.outputtype_to_ext(Info.outputtype())
    tmp_dir = tempfile.mkdtemp()
    tmp_infile = os.path.join(tmp_dir, 'foo' + ext)
    file(tmp_infile, 'w')

def teardown_infile():
    shutil.rmtree(tmp_dir)

# test BET
@with_setup(setup_infile, teardown_infile)
def test_bet():
    better = fsl.BET()
    yield assert_equal, better.cmd, 'bet'

    # Test raising error with mandatory args absent
    yield assert_raises, ValueError, better.run

    # Test generated outfile name
    better.inputs.infile = tmp_infile
    outfile = fsl_name(better, 'foo_brain')
    outpath = os.path.join(os.getcwd(), outfile)
    realcmd = 'bet %s %s' % (tmp_infile, outpath)
    yield assert_equal, better.cmdline, realcmd
    # Test specified outfile name
    outfile = fsl_name(better, '/newdata/bar')
    better.inputs.outfile = outfile
    realcmd = 'bet %s %s' % (tmp_infile, outfile)
    yield assert_equal, better.cmdline, realcmd

    # infile foo.nii doesn't exist
    def func():
        better.run(infile='foo.nii', outfile='bar.nii')
    yield assert_raises, TraitError, func

    # .run() based parameter setting
    better = fsl.BET()
    better.inputs.frac = 0.40
    outfile = fsl_name(better, 'outfile')
    betted = better.run(infile=tmp_infile, outfile=outfile)
    yield assert_equal, betted.interface.inputs.infile, tmp_infile
    yield assert_equal, betted.interface.inputs.outfile, outfile
    realcmd = 'bet %s %s -f 0.40' % (tmp_infile, outfile)
    yield assert_equal, betted.runtime.cmdline, realcmd

    # Our options and some test values for them
    # Should parallel the opt_map structure in the class for clarity
    opt_map = {
        'outline':            ('-o', True),
        'mask':               ('-m', True),
        'skull':              ('-s', True),
        'nooutput':           ('-n', True),
        'frac':               ('-f 0.40', 0.4),
        'vertical_gradient':  ('-g 0.75', 0.75),
        'radius':             ('-r 20', 20),
        'center':             ('-c 54 75 80', [54, 75, 80]),
        'threshold':          ('-t', True),
        'mesh':               ('-e', True),
        #'verbose':            ('-v', True),
        #'flags':              ('--i-made-this-up', '--i-made-this-up'),
            }
    # Currently we don't test -R, -S, -B, -Z, -F, -A or -A2

    # test each of our arguments
    better = fsl.BET()
    outfile = fsl_name(better, 'foo_brain')
    outpath = os.path.join(os.getcwd(), outfile)
    for name, settings in opt_map.items():
        better = fsl.BET(**{name: settings[1]})
        # Add mandatory input
        better.inputs.infile = tmp_infile
        realcmd =  ' '.join([better.cmd, tmp_infile, outpath, settings[0]])
        yield assert_equal, better.cmdline, realcmd


# test fast
def test_fast():
    faster = fsl.FAST()
    faster.inputs.verbose = True
    fasted = faster.run(infiles='infile')
    fasted2 = faster.run(infiles=['infile', 'otherfile'])

    yield assert_equal, faster.cmd, 'fast'
    yield assert_equal, faster.inputs.verbose, True
    yield assert_equal, faster.inputs.manualseg , None
    yield assert_not_equal, faster, fasted
    yield assert_equal, fasted.runtime.cmdline, 'fast -v infile'
    yield assert_equal, fasted2.runtime.cmdline, 'fast -v infile otherfile'

    faster = fsl.FAST()
    faster.inputs.infiles = 'foo.nii'
    yield assert_equal, faster.cmdline, 'fast foo.nii'
    faster.inputs.infiles = ['foo.nii', 'bar.nii']
    yield assert_equal, faster.cmdline, 'fast foo.nii bar.nii'

    # Our options and some test values for them
    # Should parallel the opt_map structure in the class for clarity
    opt_map = {'number_classes':       ('-n 4', 4),
               'bias_iters':           ('-I 5', 5),
               'bias_lowpass':         ('-l 15', 15),
               'img_type':             ('-t 2', 2),
               'init_seg_smooth':      ('-f 0.035', 0.035),
               'segments':             ('-g', True),
               'init_transform':       ('-a xform.mat', 'xform.mat'),
               'other_priors':         ('-A prior1.nii prior2.nii prior3.nii',
                       ('prior1.nii', 'prior2.nii', 'prior3.nii')),
               'nopve':                ('--nopve', True),
               'output_biasfield':     ('-b', True),
               'output_biascorrected': ('-B', True),
               'nobias':               ('-N', True),
               'n_inputimages':        ('-S 2', 2),
               'out_basename':         ('-o fasted', 'fasted'),
               'use_priors':           ('-P', True),
               'segment_iters':        ('-W 14', 14),
               'mixel_smooth':         ('-R 0.25', 0.25),
               'iters_afterbias':      ('-O 3', 3),
               'hyper':                ('-H 0.15', 0.15),
               'verbose':              ('-v', True),
               'manualseg':            ('-s intensities.nii',
                       'intensities.nii'),
               'probability_maps':     ('-p', True),
              }

    # test each of our arguments
    for name, settings in opt_map.items():
        faster = fsl.FAST(**{name: settings[1]})
        yield assert_equal, faster.cmdline, ' '.join([faster.cmd, settings[0]])

def setup_flirt():
    ext = Info.outputtype_to_ext(Info.outputtype())
    tmpdir = tempfile.mkdtemp()
    _, infile = tempfile.mkstemp(suffix = ext, dir = tmpdir)
    _, reffile = tempfile.mkstemp(suffix = ext, dir = tmpdir)
    return tmpdir, infile, reffile

def teardown_flirt(tmpdir):
    shutil.rmtree(tmpdir)

@parametric
def test_flirt():
    # setup
    tmpdir, infile, reffile = setup_flirt()

    flirter = fsl.FLIRT()
    yield assert_equal(flirter.cmd, 'flirt')

    flirter.inputs.bins = 256
    flirter.inputs.cost = 'mutualinfo'

    flirted = flirter.run(infile=infile, reference=reffile,
                          outfile='outfile', outmatrix='outmat.mat')
    flirt_est = flirter.run(infile=infile, reference=reffile,
                            outmatrix='outmat.mat')
    yield assert_not_equal(flirter, flirted)
    yield assert_not_equal(flirted, flirt_est)

    yield assert_equal(flirter.inputs.bins, flirted.interface.inputs.bins)
    yield assert_equal(flirter.inputs.cost, flirt_est.interface.inputs.cost)
    realcmd = 'flirt -in %s -ref %s -out outfile -omat outmat.mat ' \
        '-bins 256 -cost mutualinfo' % (infile, reffile)
    yield assert_equal(flirted.runtime.cmdline, realcmd)

    flirter = fsl.FLIRT()
    # infile not specified
    yield assert_raises(ValueError, flirter.run)
    flirter.inputs.infile = infile
    # reference not specified
    yield assert_raises(ValueError, flirter.run)
    flirter.inputs.reference = reffile
    res = flirter.run()
    # Generate outfile and outmatrix
    pth, fname, ext = split_filename(infile)
    outfile = '%s_flirt%s' % (fname, ext)
    outfile = os.path.join(os.getcwd(), outfile)
    outmat = '%s_flirt.mat' % fname
    outmat = os.path.join(os.getcwd(), outmat)
    realcmd = 'flirt -in %s -ref %s -out %s -omat %s' % (infile, reffile,
                                                         outfile, outmat)
    yield assert_equal(res.interface.cmdline, realcmd)

    _, tmpfile = tempfile.mkstemp(suffix = '.nii', dir = tmpdir)
    # Loop over all inputs, set a reasonable value and make sure the
    # cmdline is updated correctly.
    for key, trait_spec in sorted(fsl.FLIRT.input_spec().traits().items()):
        # Skip mandatory inputs and the trait methods
        if key in ('trait_added', 'trait_modified', 'infile', 'reference',
                   'environ', 'outputtype', 'outfile', 'outmatrix'):
            continue
        param = None
        value = None
        if key == 'args':
            param = '-v'
            value = '-v'
        elif isinstance(trait_spec.trait_type, File):
            value = tmpfile
            param = trait_spec.argstr  % value
        elif trait_spec.default is False:
            param = trait_spec.argstr
            value = True
        elif key in ('searchrx', 'searchry', 'searchrz'):
            value = [-45, 45]
            param = trait_spec.argstr % ' '.join(str(elt) for elt in value)
        else:
            value = trait_spec.default
            param = trait_spec.argstr % value
        cmdline = 'flirt -in %s -ref %s' % (infile, reffile)
        # Handle autogeneration of outfile
        pth, fname, ext = split_filename(infile)
        outfile = '%s_flirt%s' % (fname, ext)
        outfile = os.path.join(os.getcwd(), outfile)
        outfile = ' '.join(['-out', outfile])
        # Handle autogeneration of outmatrix
        outmatrix = '%s_flirt.mat' % fname
        outmatrix = os.path.join(os.getcwd(), outmatrix)
        outmatrix = ' '.join(['-omat', outmatrix])
        # Build command line
        cmdline = ' '.join([cmdline, outfile, outmatrix, param])
        flirter = fsl.FLIRT(infile = infile, reference = reffile)
        setattr(flirter.inputs, key, value)
        yield assert_equal(flirter.cmdline, cmdline)

    # Test OutputSpec
    flirter = fsl.FLIRT(infile = infile, reference = reffile)
    pth, fname, ext = split_filename(infile)
    flirter.inputs.outfile = ''.join(['foo', ext])
    flirter.inputs.outmatrix = ''.join(['bar', ext])
    outs = flirter._list_outputs()
    yield assert_equal(outs['outfile'], flirter.inputs.outfile)
    yield assert_equal(outs['outmatrix'], flirter.inputs.outmatrix)

    teardown_flirt(tmpdir)

def test_applyxfm():
    # ApplyXFM subclasses FLIRT.
    flt = fsl.ApplyXfm(infile='subj.nii', inmatrix='xfm.mat',
                       outfile='xfm_subj.nii', reference='mni152.nii')
    flt.run()
    yield assert_equal, flt.cmdline, \
        'flirt -in subj.nii -ref mni152.nii -init xfm.mat ' \
        '-applyxfm -out xfm_subj.nii'
    flt = fsl.ApplyXfm()
    yield assert_raises, AttributeError, flt.run
    flt.inputs.infile = 'subj.nii'
    flt.inputs.outfile = 'xfm_subj.nii'
    # reference not specified
    yield assert_raises, AttributeError, flt.run
    flt.inputs.reference = 'mni152.nii'
    # inmatrix not specified
    yield assert_raises, AttributeError, flt.run
    flt.inputs.inmatrix = 'xfm.mat'
    res = flt.run()
    realcmd = 'flirt -in subj.nii -ref mni152.nii -init xfm.mat '\
        '-applyxfm -out xfm_subj.nii'
    yield assert_equal, res.interface.cmdline, realcmd
    # Test generated outfile name
    infile = 'foo.nii'
    xfm = fsl.ApplyXfm(infile = infile)
    outfile = os.path.join(os.getcwd(), 'foo_axfm.nii')
    realcmd = 'flirt -in %s -applyxfm -out %s' % (infile, outfile)
    yield assert_equal, xfm.cmdline, realcmd

# Mcflirt
def test_mcflirt():
    frt = fsl.MCFLIRT()
    yield assert_equal, frt.cmd, 'mcflirt'
    # Test generated outfile name
    infile = '/data/foo.nii'
    frt.inputs.infile = infile
    outfile = os.path.join(os.getcwd(), 'foo_mcf.nii')
    realcmd = 'mcflirt -in ' + infile + ' -out ' + outfile
    yield assert_equal, frt.cmdline, realcmd
    # Test specified outfile name
    outfile = '/newdata/bar.nii'
    frt.inputs.outfile = outfile
    realcmd = 'mcflirt -in ' + infile + ' -out ' + outfile
    yield assert_equal, frt.cmdline, realcmd

    opt_map = {
        'outfile':     ('-out bar.nii', 'bar.nii'),
        'cost':        ('-cost mutualinfo', 'mutualinfo'),
        'bins':        ('-bins 256', 256),
        'dof':         ('-dof 6', 6),
        'refvol':      ('-refvol 2', 2),
        'scaling':     ('-scaling 6.00', 6.00),
        'smooth':      ('-smooth 1.00', 1.00),
        'rotation':    ('-rotation 2', 2),
        'verbose':     ('-verbose', True),
        'stages':      ('-stages 3', 3),
        'init':        ('-init matrix.mat', 'matrix.mat'),
        'usegradient': ('-gdt', True),
        'usecontour':  ('-edge', True),
        'meanvol':     ('-meanvol', True),
        'statsimgs':   ('-stats', True),
        'savemats':    ('-mats', True),
        'saveplots':   ('-plots', True),
        'report':      ('-report', True),
        }

    for name, settings in opt_map.items():
        fnt = fsl.MCFLIRT(**{name : settings[1]})
        yield assert_equal, fnt.cmdline, ' '.join([fnt.cmd, settings[0]])

    # Test error is raised when missing required args
    fnt = fsl.MCFLIRT()
    yield assert_raises, AttributeError, fnt.run
    # Test run result
    fnt = fsl.MCFLIRT()
    fnt.inputs.infile = 'foo.nii'
    res = fnt.run()
    yield assert_equal, type(res), InterfaceResult
    res = fnt.run(infile='bar.nii')
    yield assert_equal, type(res), InterfaceResult


#test fnirt
def test_fnirt():
    fnirt = fsl.FNIRT()
    yield assert_equal, fnirt.cmd, 'fnirt'

    # Test inputs with variable number of values
    fnirt.inputs.sub_sampling = [8, 6, 4]
    yield assert_equal, fnirt.inputs.sub_sampling, [8, 6, 4]
    fnirtd = fnirt.run(infile='infile', reference='reference')
    realcmd = 'fnirt --in=infile --ref=reference --subsamp=8,6,4'
    yield assert_equal, fnirtd.runtime.cmdline, realcmd

    fnirt2 = fsl.FNIRT(sub_sampling=[8, 2])
    fnirtd2 = fnirt2.run(infile='infile', reference='reference')
    realcmd = 'fnirt --in=infile --ref=reference --subsamp=8,2'
    yield assert_equal, fnirtd2.runtime.cmdline, realcmd

    # Test case where input that can be a list is just a single value
    params = [('sub_sampling', '--subsamp'),
              ('max_iter', '--miter'),
              ('referencefwhm', '--reffwhm'),
              ('imgfwhm', '--infwhm'),
              ('lambdas', '--lambda'),
              ('estintensity', '--estint'),
              ('applyrefmask', '--applyrefmask'),
              ('applyimgmask', '--applyinmask')]
    for item, flag in params:


        if item in ('sub_sampling', 'max_iter',
                    'referencefwhm', 'imgfwhm',
                    'lambdas', 'estintensity'):
            fnirt = fsl.FNIRT(**{item : 5})
            cmd = 'fnirt %s=%d' % (flag, 5)
        else:
            fnirt = fsl.FNIRT(**{item : 5})
            cmd = 'fnirt %s=%f' % (flag, 5)
        yield assert_equal, fnirt.cmdline, cmd

    # Test error is raised when missing required args
    fnirt = fsl.FNIRT()
    yield assert_raises, AttributeError, fnirt.run
    fnirt.inputs.infile = 'foo.nii'
    # I don't think this is correct. See FNIRT documentation -DJC
    # yield assert_raises, AttributeError, fnirt.run
    fnirt.inputs.reference = 'mni152.nii'
    res = fnirt.run()
    yield assert_equal, type(res), InterfaceResult

    opt_map = {
        'affine':           ('--aff=affine.mat', 'affine.mat'),
        'initwarp':         ('--inwarp=warp.mat', 'warp.mat'),
        'initintensity':    ('--intin=inten.mat', 'inten.mat'),
        'configfile':       ('--config=conf.txt', 'conf.txt'),
        'referencemask':    ('--refmask=ref.mat', 'ref.mat'),
        'imagemask':        ('--inmask=mask.nii', 'mask.nii'),
        'fieldcoeff_file':  ('--cout=coef.txt', 'coef.txt'),
        'outimage':         ('--iout=out.nii', 'out.nii'),
        'fieldfile':        ('--fout=fld.txt', 'fld.txt'),
        'jacobianfile':     ('--jout=jaco.txt', 'jaco.txt'),
        'reffile':          ('--refout=refout.nii', 'refout.nii'),
        'intensityfile':    ('--intout=intout.txt', 'intout.txt'),
        'logfile':          ('--logout=log.txt', 'log.txt'),
        'verbose':          ('--verbose', True),
        'flags':            ('--fake-flag', '--fake-flag')}

    for name, settings in opt_map.items():
        fnirt = fsl.FNIRT(**{name : settings[1]})
        yield assert_equal, fnirt.cmdline, ' '.join([fnirt.cmd, settings[0]])

def test_applywarp():
    opt_map = {
        'infile':            ('--in=foo.nii', 'foo.nii'),
        'outfile':           ('--out=bar.nii', 'bar.nii'),
        'reference':         ('--ref=refT1.nii', 'refT1.nii'),
        'fieldfile':         ('--warp=warp_field.nii', 'warp_field.nii'),
        'premat':            ('--premat=prexform.mat', 'prexform.mat'),
        'postmat':           ('--postmat=postxform.mat', 'postxform.mat')
        }

    for name, settings in opt_map.items():
        awarp = fsl.ApplyWarp(**{name : settings[1]})
        if name == 'infile':
            outfile = os.path.join(os.getcwd(), 'foo_warp.nii')
            realcmd = 'applywarp --in=foo.nii --out=%s' % outfile
            yield assert_equal, awarp.cmdline, realcmd
        else:
            yield assert_equal, awarp.cmdline, \
                ' '.join([awarp.cmd, settings[0]])
