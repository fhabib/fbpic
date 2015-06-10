"""
This file is part of the Fourier-Bessel Particle-In-Cell code (FB-PIC)
It defines a set of generic functions that operate on a GPU.
"""
from numba import cuda

# ------------------
# Copying functions
# ------------------

@cuda.jit('void(complex128[:,:], complex128[:,:])')
def cuda_copy_2d_to_2d( array_in, array_out ) :
    """
    Copy array_in to array_out, on the GPU
    
    This is typically done in cases where one of the two
    arrays is in C-order and the other one is in Fortran order.
    This conversion from C order to Fortran order is needed
    before using cuBlas functions.
        
    Parameters :
    ------------
    array_in, array_out : 2darray of complexs
        Arrays of shape (Nz, Nr)
    """

    # Set up cuda grid
    iz, ir = cuda.grid(2)
    
    # Copy from array_in to array_out
    if (iz < array_in.shape[0]) and (ir < array_in.shape[1]) :
        array_out[iz, ir] = array_in[iz, ir]

@cuda.jit('void(complex128[:,:], complex128[:])')
def cuda_copy_2d_to_1d( array_2d, array_1d ) :
    """
    Copy array_2d to array_1d, so that the first axis of array_2d
    is contiguous in array_1d
    
    This is typically done before using the cuFFT API,
    which requires 1d arrays to do FFT in only one dimension.
        
    Parameters :
    ------------
    array_2d : 2darray of complexs
        Array of shape (Nz, Nr)

    array_1d : 1d array of complexs
        Array of shape (Nz*Nr,)
    """

    # Set up cuda grid
    iz, ir = cuda.grid(2)
    
    # Copy from array_2d to array_1d
    if (iz < array_2d.shape[0]) and (ir < array_2d.shape[1]) :
        i = iz + array_2d.shape[0]*ir
        array_1d[i] = array_2d[iz, ir]

@cuda.jit('void(complex128[:], complex128[:,:])')
def cuda_copy_1d_to_2d( array_1d, array_2d ) :
    """
    Copy array_1d to array_2d, so that the first axis of array_2d
    is contiguous in array_1d
    
    This is typically done after using the cuFFT API,
    since the the output of cuFFT is a 1d array
        
    Parameters :
    ------------
    array_2d : 2darray of complexs
        Array of shape (Nz, Nr)

    array_1d : 1d array of complexs
        Array of shape (Nz*Nr,)
    """

    # Set up cuda grid
    iz, ir = cuda.grid(2)
    
    # Copy from array_1d to array_2d
    if (iz < array_2d.shape[0]) and (ir < array_2d.shape[1]) :
        i = iz + array_2d.shape[0]*ir
        array_2d[iz, ir] = array_1d[i]

# ----------------------------------------------------
# Functions that combine components in spectral space
# ----------------------------------------------------

@cuda.jit('void(complex128[:,:], complex128[:,:], \
                complex128[:,:], complex128[:,:])')
def cuda_rt_to_pm( buffer_r, buffer_t, buffer_p, buffer_m ) :
    """
    Combine the arrays buffer_r and buffer_t to produce the
    arrays buffer_p and buffer_m, according to the rules of
    the Fourier-Hankel decomposition (see associated paper)
    """
    # Set up cuda grid
    iz, ir = cuda.grid(2)

    if (iz < buffer_r.shape[0]) and (ir < buffer_r.shape[1]) :
        # Use intermediate variables, as the arrays
        # buffer_r and buffer_t may actually point to the same
        # object as buffer_p and buffer_m, for economy of memory
        value_r = buffer_r[iz, ir]
        value_t = buffer_t[iz, ir]
        # Combine the values
        buffer_p[iz, ir] = 0.5*( value_r - 1.j*value_t )
        buffer_m[iz, ir] = 0.5*( value_r + 1.j*value_t )


@cuda.jit('void(complex128[:,:], complex128[:,:], \
                complex128[:,:], complex128[:,:])')
def cuda_pm_to_rt( buffer_p, buffer_m, buffer_r, buffer_t ) :
    """
    Combine the arrays buffer_p and buffer_m to produce the
    arrays buffer_r and buffer_t, according to the rules of
    the Fourier-Hankel decomposition (see associated paper)
    """
    # Set up cuda grid
    iz, ir = cuda.grid(2)

    if (iz < buffer_p.shape[0]) and (ir < buffer_p.shape[1]) :
        # Use intermediate variables, as the arrays
        # buffer_r and buffer_t may actually point to the same
        # object as buffer_p and buffer_m, for economy of memory
        value_p = buffer_p[iz, ir]
        value_m = buffer_m[iz, ir]
        # Combine the values
        buffer_r[iz, ir] =     ( value_p + value_m )
        buffer_t[iz, ir] = 1.j*( value_p - value_m )

# -----------------------------------------------------
# CUDA grid utilities
# -----------------------------------------------------

def cuda_tpb_bpg_1d(x, TPB = 256):
    """
    Get the needed blocks per grid for a 1D CUDA grid.

    Parameters :
    ------------
    x : int
        Total number of threads

    TPB : int
        Threads per block

    Returns :
    ------------
    BPG : int
        Number of blocks per grid

    TPB : int
        Threads per block
    """
    # Calculates the needed blocks per grid
    BPG = int(x/TPB + 1)
    return BPG, TPB

def cuda_tpb_bpg_2d(x, y, TPBx = 8, TPBy = 8):
    """
    Get the needed blocks per grid for a 2D CUDA grid.

    Parameters :
    ------------
    x, y  : int
        Total number of threads in first and second dimension

    TPBx, TPBy : int
        Threads per block in x and y

    Returns :
    ------------
    (BPGx, BPGy) : tuple of ints
        Number of blocks per grid in x and y

    (TPBx, TPBy) : tuple of ints
        Threads per block in x and y
    """
    # Calculates the needed blocks per grid
    BPGx = int(x/TPBx + 1)
    BPGy = int(y/TPBy + 1)
    return (BPGx, BPGy), (TPBx, TPBy)

# -----------------------------------------------------
# CUDA memory management
# -----------------------------------------------------

def send_data_to_gpu(simulation):
    """
    Send the simulation data to the GPU.
    Calls the functions of the particle and field package
    that send the data to the GPU.

    Parameters :
    ------------
    simulation : object
        A simulation object that contains the particle
        (ptcl) and field object (fld)
    """
    # Send particles to the GPU (if CUDA is used)
    for species in simulation.ptcl :
        if species.use_cuda:
            species.send_particles_to_gpu()
    # Send fields to the GPU (if CUDA is used)
    simulation.fld.send_fields_to_gpu()

def receive_data_from_gpu(simulation):
    """
    Receive the simulation data from the GPU.
    Calls the functions of the particle and field package
    that receive the data from the GPU.

    Parameters :
    ------------
    simulation : object
        A simulation object that contains the particle
        (ptcl) and field object (fld)
    """
    # Receive the particles from the GPU (if CUDA is used)
    for species in simulation.ptcl :
        if species.use_cuda:
            species.receive_particles_from_gpu() 
    # Receive fields from the GPU (if CUDA is used)
    simulation.fld.receive_fields_from_gpu()
