"""
This test file is part of FB-PIC (Fourier-Bessel Particle-In-Cell).

It makes sure that the example input scripts in `docs/example_input`
runs **without crashing**. It runs the following scripts:
- lpa_sim.py with a single proc
- boosted_frame_sim.py with a single proc
- lpa_sim.py with two proc
**It does not actually check the validity of the physics involved.**

Usage:
This file is meant to be run from the top directory of fbpic,
by any of the following commands
$ python tests/test_example_docs_script.py
$ py.test -q tests/test_example_docs_script.py
$ python setup.py test
"""
import os
import shutil

def test_lpa_sim_singleproc():
    "Test the example input script with one proc in `docs/example_input`"

    temporary_dir = './tests/tmp_test_dir'

    # Create a temporary directory for the simulation
    # and copy the example script into this directory
    if os.path.exists( temporary_dir ):
        shutil.rmtree( temporary_dir )
    os.mkdir( temporary_dir )
    shutil.copy('./docs/example_input/lpa_sim.py', temporary_dir )

    # Enter the temporary directory and run the script
    os.chdir( temporary_dir )
    # The globals command make sure that the package which
    # are imported within the script can be used here.
    execfile( 'lpa_sim.py', globals(), globals() )

    # Exit the temporary directory and suppress it
    os.chdir('../../')
    shutil.rmtree( temporary_dir )

def test_boosted_frame_sim_singleproc():
    "Test the example input script with one proc in `docs/example_input`"

    temporary_dir = './tests/tmp_test_dir'

    # Create a temporary directory for the simulation
    # and copy the example script into this directory
    if os.path.exists( temporary_dir ):
        shutil.rmtree( temporary_dir )
    os.mkdir( temporary_dir )
    shutil.copy('./docs/example_input/boosted_frame_sim.py', temporary_dir )

    # Enter the temporary directory and run the script
    os.chdir( temporary_dir )
    # The globals command make sure that the package which
    # are imported within the script can be used here.
    execfile( 'boosted_frame_sim.py', globals(), globals() )

    # Exit the temporary directory and suppress it
    os.chdir('../../')
    shutil.rmtree( temporary_dir )

def test_lpa_sim_twoproc():
    "Test the example input script with two proc in `docs/example_input`"

    temporary_dir = './tests/tmp_test_dir'

    # Create a temporary directory for the simulation
    # and copy the example script into this directory
    if os.path.exists( temporary_dir ):
        shutil.rmtree( temporary_dir )
    os.mkdir( temporary_dir )
    shutil.copy('./docs/example_input/lpa_sim.py', temporary_dir )

    # Enter the temporary directory and run the script
    os.chdir( temporary_dir )
    # Launch the script from the OS, with 2 proc
    response = os.system( 'mpirun -np 2 python lpa_sim.py' )
    assert response==0

    # Exit the temporary directory and suppress it
    os.chdir('../../')
    shutil.rmtree( temporary_dir )



if __name__ == '__main__':
    test_lpa_sim_singleproc()
    test_boosted_frame_sim_singleproc()
    test_lpa_sim_twoproc()