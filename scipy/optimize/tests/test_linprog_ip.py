"""
Unit test for Linear Programming via Simplex Algorithm.
"""

# add tests for:
# https://github.com/scipy/scipy/issues/5400
# https://github.com/scipy/scipy/issues/6690

from __future__ import division, print_function, absolute_import

import numpy as np
from numpy.testing import (assert_, assert_array_almost_equal, assert_allclose,
        assert_almost_equal, assert_raises, assert_equal, run_module_suite)
import json
import warnings

from scipy.optimize import linprog, OptimizeWarning
from scipy.optimize.linprog_ip import linprog as linprog_ip
from scipy._lib._numpy_compat import _assert_warns


def magic_square(n):
    np.random.seed(0)
    M = n*(n**2+1)/2
    
    numbers = np.arange(n**4) // n**2 + 1
    
    numbers = numbers.reshape(n**2,n,n)
    
    zeros = np.zeros((n**2,n,n))
    
    A_list = []
    b_list = []
    
    # Rule 1: use every number exactly once
    for i in range(n**2):
        A_row = zeros.copy()
        A_row[i,:,:] = 1
        A_list.append(A_row.flatten())
        b_list.append(1)
        
    # Rule 2: Only one number per square
    for i in range(n):
        for j in range(n):
            A_row = zeros.copy()
            A_row[:,i,j] = 1
            A_list.append(A_row.flatten())
            b_list.append(1)
        
    # Rule 3: sum of rows is M
    for i in range(n):
        A_row = zeros.copy()
        A_row[:,i,:] = numbers[:,i,:]
        A_list.append(A_row.flatten())
        b_list.append(M)
        
    # Rule 4: sum of columns is M
    for i in range(n):
        A_row = zeros.copy()
        A_row[:,:,i] = numbers[:,:,i]
        A_list.append(A_row.flatten())
        b_list.append(M)
        
    # Rule 5: sum of diagonals is M
    A_row = zeros.copy()
    A_row[:,range(n),range(n)] = numbers[:,range(n),range(n)]
    A_list.append(A_row.flatten())
    b_list.append(M)
    A_row = zeros.copy()
    A_row[:,range(n),range(-1,-n-1,-1)] = numbers[:,range(n),range(-1,-n-1,-1)]
    A_list.append(A_row.flatten())
    b_list.append(M)
    
        
    A = np.array(np.vstack(A_list),dtype = float)
    b = np.array(b_list,dtype= float)
    #c = np.zeros(A.shape[1],dtype= float)
    c = np.random.rand(A.shape[1])
    
    return A,b,c, numbers
    
def lpgen_2d(m,n):
    """ -> A b c LP test: m*n vars, m+n constraints
        row sums == n/m, col sums == 1
        https://gist.github.com/denis-bz/8647461
    """
    np.random.seed(0)
    c = - np.random.exponential(size=(m,n))
    Arow = np.zeros((m,m*n))
    brow = np.zeros(m)
    for j in range(m):
        j1 = j + 1
        Arow[j,j*n:j1*n] = 1
        brow[j] = n/m

    Acol = np.zeros((n,m*n))
    bcol = np.zeros(n)
    for j in range(n):
        j1 = j + 1
        Acol[j,j::n] = 1
        bcol[j] = 1

    A = np.vstack((Arow,Acol))
    b = np.hstack((brow,bcol))

    return A, b, c.ravel()


def _assert_infeasible(res):
    # res: linprog result object
    assert_(not res.success, "incorrectly reported success")
    assert_equal(res.status, 2, "failed to report infeasible status")


def _assert_unbounded(res):
    # res: linprog result object
    assert_(not res.success, "incorrectly reported success")  
    assert_equal(res.status, 3, "failed to report unbounded status")


def _assert_success(res, desired_fun=None, desired_x=None, rtol = 1e-7, atol = 1e-7):
    # res: linprog result object
    # desired_fun: desired objective function value or None
    # desired_x: desired solution or None
    assert_(res.success)
    assert_equal(res.status, 0)
    if desired_fun is not None:
        assert_allclose(res.fun, desired_fun,
                        err_msg="converged to an unexpected objective value", rtol=rtol, atol=atol)
    if desired_x is not None:
        assert_allclose(res.x, desired_x,
                        err_msg="converged to an unexpected solution", rtol=rtol, atol=atol)


def test_aliasing_b_ub():
    c = np.array([1.0])
    A_ub = np.array([[1.0]])
    b_ub_orig = np.array([3.0])
    b_ub = b_ub_orig.copy()
    bounds = (-4.0, np.inf)
    res = linprog_ip(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds)
    _assert_success(res, desired_fun=-4, desired_x=[-4])
    assert_allclose(b_ub_orig, b_ub)


def test_aliasing_b_eq():
    c = np.array([1.0])
    A_eq = np.array([[1.0]])
    b_eq_orig = np.array([3.0])
    b_eq = b_eq_orig.copy()
    bounds = (-4.0, np.inf)
    res = linprog_ip(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
    _assert_success(res, desired_fun=3, desired_x=[3])
    assert_allclose(b_eq_orig, b_eq)


def test_bounds_second_form_unbounded_below():
    c = np.array([1.0])
    A_eq = np.array([[1.0]])
    b_eq = np.array([3.0])
    bounds = (None, 10.0)
    res = linprog_ip(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
    _assert_success(res, desired_fun=3, desired_x=[3])


def test_bounds_second_form_unbounded_above():
    c = np.array([1.0])
    A_eq = np.array([[1.0]])
    b_eq = np.array([3.0])
    bounds = (1.0, None)
    res = linprog_ip(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
    _assert_success(res, desired_fun=3, desired_x=[3])


def test_non_ndarray_args():
    c = [1.0]
    A_ub = [[1.0]]
    b_ub = [3.0]
    A_eq = [[1.0]]
    b_eq = [2.0]
    bounds = (-1.0, 10.0)
    res = linprog_ip(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
    _assert_success(res, desired_fun=2, desired_x=[2])


def test_linprog_upper_bound_constraints():
    # Maximize a linear function subject to only linear upper bound constraints.
    #  http://www.dam.brown.edu/people/huiwang/classes/am121/Archive/simplex_121_c.pdf
    c = np.array([3,2])*-1  # maximize
    A_ub = [[2,1],
            [1,1],
            [1,0]]
    b_ub = [10,8,4]
    res = (linprog_ip(c,A_ub=A_ub,b_ub=b_ub))
    _assert_success(res, desired_fun=-18, desired_x=[2, 6])


def test_linprog_mixed_constraints():
    # Minimize linear function subject to non-negative variables.
    #  http://www.statslab.cam.ac.uk/~ff271/teaching/opt/notes/notes8.pdf
    c = [6,3]
    A_ub = [[0, 3],
           [-1,-1],
           [-2, 1]]
    b_ub = [2,-1,-1]
    res = linprog_ip(c,A_ub=A_ub,b_ub=b_ub)
    _assert_success(res, desired_fun=5, desired_x=[2/3, 1/3])


# default for allclose comparison is rtol = 1e-7 and atol = 0
# since some desired x are 0, no disagreement is acceptable
# added small atol to compare properly
def test_linprog_cyclic_recovery():
    # Test linprogs recovery from cycling using the Klee-Minty problem
    #  Klee-Minty  http://www.math.ubc.ca/~israel/m340/kleemin3.pdf
    c = np.array([100,10,1])*-1  # maximize
    A_ub = [[1, 0, 0],
            [20, 1, 0],
            [200,20, 1]]
    b_ub = [1,100,10000]
    res = linprog_ip(c,A_ub=A_ub,b_ub=b_ub)
    _assert_success(res, desired_x=[0, 0, 10000],atol = 5e-6)


# not success test is not appropriate for linprog_ip
# there is no bland anticycling rule
# need atol
def test_linprog_cyclic_bland():
    # Test the effect of Bland's rule on a cycling problem
    c = np.array([-10, 57, 9, 24.])
    A_ub = np.array([[0.5, -5.5, -2.5, 9],
                     [0.5, -1.5, -0.5, 1],
                     [1, 0, 0, 0]])
    b_ub = [0, 0, 1]
    res = linprog_ip(c, A_ub=A_ub, b_ub=b_ub, options=dict(maxiter=100))
#    assert_(not res.success)
#    res = linprog_ip(c, A_ub=A_ub, b_ub=b_ub,
#                  options=dict(maxiter=100, bland=True,))
    _assert_success(res, desired_x=[1, 0, 1, 0])

## whaat does the test environment do to the RNG?
## need to improve test for unboundedness
def test_linprog_unbounded():
    # Test linprog response to an unbounded problem
    c = np.array([1,1])*-1  # maximize
    A_ub = [[-1,1],
            [-1,-1]]
    b_ub = [-1,-2]
    res = linprog_ip(c,A_ub=A_ub,b_ub=b_ub,options={"disp":True})
    _assert_unbounded(res)

def test_linprog_infeasible():
    # Test linrpog response to an infeasible problem
    c = [-1,-1]
    A_ub = [[1,0],
            [0,1],
            [-1,-1]]
    b_ub = [2,2,-5]
    res = linprog_ip(c,A_ub=A_ub,b_ub=b_ub)
    _assert_infeasible(res)


def test_nontrivial_problem():
    # Test linprog for a problem involving all constraint types,
    # negative resource limits, and rounding issues.
    c = [-1,8,4,-6]
    A_ub = [[-7,-7,6,9],
            [1,-1,-3,0],
            [10,-10,-7,7],
            [6,-1,3,4]]
    b_ub = [-3,6,-6,6]
    A_eq = [[-10,1,1,-8]]
    b_eq = [-4]
    res = linprog_ip(c,A_ub=A_ub,b_ub=b_ub,A_eq=A_eq,b_eq=b_eq)
    _assert_success(res, desired_fun=7083/1391,
                    desired_x=[101/1391,1462/1391,0,752/1391])


def test_negative_variable():
    # Test linprog with a problem with one unbounded variable and
    # another with a negative lower bound.
    c = np.array([-1,4])*-1  # maximize
    A_ub = np.array([[-3,1],
                     [1, 2]], dtype=np.float64)
    A_ub_orig = A_ub.copy()
    b_ub = [6,4]
    x0_bounds = (-np.inf,np.inf)
    x1_bounds = (-3,np.inf)

    res = linprog_ip(c,A_ub=A_ub,b_ub=b_ub,bounds=(x0_bounds,x1_bounds))

    assert_equal(A_ub, A_ub_orig)   # user input not overwritten
    _assert_success(res, desired_fun=-80/7, desired_x=[-8/7, 18/7])


def test_large_problem():
    # Test linprog simplex with a rather large problem (400 variables,
    # 40 constraints) generated by https://gist.github.com/denis-bz/8647461
    A,b,c = lpgen_2d(20,20)
    res = linprog_ip(c,A_ub=A,b_ub=b,options={"sparse":False}) # Sparse not worth it without sparse Cholesky
    _assert_success(res, desired_fun=-64.049494229)

def test_magic_square():
    # test linprog_ip with a problem with a rank-deficient A_eq matrix
    A,b,c,N = magic_square(3)
    res = linprog_ip(c,A_eq=A,b_eq=b,bounds=(0,1),options={"sparse":True})
    _assert_success(res, desired_fun=1.7305505947333977)
    
def test_network_flow():
    # A network flow problem with supply and demand at nodes
    # and with costs along directed edges.
    # https://www.princeton.edu/~rvdb/542/lectures/lec10.pdf
    c = [2, 4, 9, 11, 4, 3, 8, 7, 0, 15, 16, 18]
    n, p = -1, 1
    A_eq = [
            [n, n, p, 0, p, 0, 0, 0, 0, p, 0, 0],
            [p, 0, 0, p, 0, p, 0, 0, 0, 0, 0, 0],
            [0, 0, n, n, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, p, p, 0, 0, p, 0],
            [0, 0, 0, 0, n, n, n, 0, p, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, n, n, 0, 0, p],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, n, n, n]]
    b_eq = [0, 19, -16, 33, 0, 0, -36]
    res = linprog_ip(c=c, A_eq=A_eq, b_eq=b_eq)
    _assert_success(res, desired_fun=755,atol =1e-6)

# does not support callback yet
# fails due to numerical issues unless lstsq is used
def test_network_flow_limited_capacity():
    # A network flow problem with supply and demand at nodes
    # and with costs and capacities along directed edges.
    # http://blog.sommer-forst.de/2013/04/10/
    cost = [2, 2, 1, 3, 1]
    bounds = [
            [0, 4],
            [0, 2],
            [0, 2],
            [0, 3],
            [0, 5]]
    n, p = -1, 1
    A_eq = [
            [n, n, 0, 0, 0],
            [p, 0, n, n, 0],
            [0, p, p, 0, n],
            [0, 0, 0, p, p]]
    b_eq = [-4, 0, 0, 4]
    # Including the callback here ensures the solution can be
    # calculated correctly, even when phase 1 terminated
    # with some of the artificial variables as pivots
    # (i.e. basis[:m] contains elements corresponding to
    # the artificial variables)
#    res = linprog_ip(c=cost, A_eq=A_eq, b_eq=b_eq, bounds=bounds,
#                  callback=lambda x, **kwargs: None)
    res = linprog_ip(c=cost, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
    _assert_success(res, desired_fun=14)


def test_simplex_algorithm_wikipedia_example():
    # http://en.wikipedia.org/wiki/Simplex_algorithm#Example
    Z = [-2, -3, -4]
    A_ub = [
            [3, 2, 1],
            [2, 5, 3]]
    b_ub = [10, 15]
    res = linprog_ip(c=Z, A_ub=A_ub, b_ub=b_ub)
    _assert_success(res, desired_fun=-20)


def test_enzo_example():
    # http://projects.scipy.org/scipy/attachment/ticket/1252/lp2.py
    #
    # Translated from Octave code at:
    # http://www.ecs.shimane-u.ac.jp/~kyoshida/lpeng.htm
    # and placed under MIT licence by Enzo Michelangeli
    # with permission explicitly granted by the original author,
    # Prof. Kazunobu Yoshida  
    c = [4, 8, 3, 0, 0, 0]
    A_eq = [
            [2, 5, 3, -1, 0, 0],
            [3, 2.5, 8, 0, -1, 0],
            [8, 10, 4, 0, 0, -1]]
    b_eq = [185, 155, 600]
    res = linprog_ip(c=c, A_eq=A_eq, b_eq=b_eq)
    _assert_success(res, desired_fun=317.5,
                    desired_x=[66.25, 0, 17.5, 0, 183.75, 0],atol = 6e-6)


def test_enzo_example_b():
    # rescued from https://github.com/scipy/scipy/pull/218
    c = [2.8, 6.3, 10.8, -2.8, -6.3, -10.8]
    A_eq = [[-1, -1, -1, 0, 0, 0],
            [0, 0, 0, 1, 1, 1],
            [1, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 1]]
    b_eq = [-0.5, 0.4, 0.3, 0.3, 0.3]
    # Including the callback here ensures the solution can be
    # calculated correctly.
#    res = linprog(c=c, A_eq=A_eq, b_eq=b_eq,
#                  callback=lambda x, **kwargs: None)
    res = linprog_ip(c=c, A_eq=A_eq, b_eq=b_eq)
    _assert_success(res, desired_fun=-1.77,
                    desired_x=[0.3, 0.2, 0.0, 0.0, 0.1, 0.3])


def test_enzo_example_c_with_degeneracy():
    # rescued from https://github.com/scipy/scipy/pull/218
    m = 20
    c = -np.ones(m)
    tmp = 2*np.pi*np.arange(1, m+1)/(m+1)
    A_eq = np.vstack((np.cos(tmp)-1, np.sin(tmp)))
    b_eq = [0, 0]
    res = linprog_ip(c=c, A_eq=A_eq, b_eq=b_eq)
    _assert_success(res, desired_fun=0, desired_x=np.zeros(m))


def test_enzo_example_c_with_unboundedness():
    # rescued from https://github.com/scipy/scipy/pull/218
    m = 50
    c = -np.ones(m)
    tmp = 2*np.pi*np.arange(m)/(m+1)
    A_eq = np.vstack((np.cos(tmp)-1, np.sin(tmp)))
    b_eq = [0, 0]
    res = linprog_ip(c=c, A_eq=A_eq, b_eq=b_eq)
    _assert_unbounded(res)


def test_enzo_example_c_with_infeasibility():
    # rescued from https://github.com/scipy/scipy/pull/218
    m = 50
    c = -np.ones(m)
    tmp = 2*np.pi*np.arange(m)/(m+1)
    A_eq = np.vstack((np.cos(tmp)-1, np.sin(tmp)))
    b_eq = [1, 1]
    res = linprog_ip(c=c, A_eq=A_eq, b_eq=b_eq,options ={"presolve":False})
    _assert_infeasible(res)


def test_empty_constraint_1():
    res = linprog_ip([-1, 1, -1, 1], bounds = [(0,np.inf),(-np.inf,0),(-1,1),(-1,1)])
    _assert_unbounded(res)
    assert_equal(res.nit,0)
    
def test_empty_constraint_2():
    res = linprog_ip([1, -1, 1, -1], bounds = [(0,np.inf),(-np.inf,0),(-1,1),(-1,1)])
    _assert_success(res, desired_x = [0, 0, -1, 1], desired_fun = -2)

def test_zero_row_1():
    m, n = 2,4
    c = np.random.rand(n)
    A_eq = np.random.rand(m,n)
    A_eq[0,:] = 0
    b_eq = np.random.rand(m)
    res = linprog_ip(c=c, A_eq=A_eq, b_eq=b_eq)
    _assert_infeasible(res)
    assert_equal(res.nit,0)
  
def test_zero_row_2():
    A_eq = [[0,0,0], [1,1,1], [0,0,0]]
    b_eq = [0,3,0]
    c = [1, 2, 3]
    res = linprog_ip(c=c, A_eq=A_eq, b_eq=b_eq)
    _assert_success(res, desired_fun = 3)
    
def test_zero_row_3():
    m, n = 2,4
    c = np.random.rand(n)
    A_ub = np.random.rand(m,n)
    A_ub[0,:] = 0
    b_ub = -np.random.rand(m)
    res = linprog_ip(c=c, A_ub=A_ub, b_ub=b_ub)
    _assert_infeasible(res)
    assert_equal(res.nit,0)
  
def test_zero_row_4():
    A_ub = [[0,0,0], [1,1,1], [0,0,0]]
    b_ub = [0,3,0]
    c = [1, 2, 3]
    res = linprog_ip(c=c, A_ub=A_ub, b_ub=b_ub)
    _assert_success(res, desired_fun = 0)
    
def test_zero_column_1():
    m, n = 3,4
    np.random.seed(0)
    c = np.random.rand(n)
    c[1] = 1
    A_eq = np.random.rand(m,n)
    A_eq[:,1] = 0
    b_eq = np.random.rand(m)
    A_ub = [[1,0,1,1]]
    b_ub = 3
    res = linprog_ip(c,A_ub,b_ub,A_eq,b_eq, bounds = [(-10,10), (-10, 10), (-10, None), (None,None)], options = {"presolve":True})
    _assert_success(res,desired_fun=-9.7087836730413404)

def test_zero_column_2():
    np.random.seed(0)
    m, n = 2,4
    c = np.random.rand(n)
    c[1] = -1
    A_eq = np.random.rand(m,n)
    A_eq[:,1] = 0
    b_eq = np.random.rand(m)
    
    A_ub = np.random.rand(m,n)
    A_ub[:,1] = 0
    b_ub = np.random.rand(m)
    res = linprog_ip(c, A_ub, b_ub, A_eq, b_eq, bounds = (None,None))
    _assert_unbounded(res)
    assert_equal(res.nit, 0)
    
def test_singleton_row_eq_1():
    c = [1, 1, 1, 2]
    A_eq = [[1,0,0,0],[0,2,0,0],[1,0,0,0],[1,1,1,1]]
    b_eq = [1,2,2,4]
    res = linprog_ip(c,A_eq = A_eq, b_eq = b_eq)
    _assert_infeasible(res)
    assert_equal(res.nit, 0)
    
def test_singleton_row_eq_2():
    c = [1, 1, 1, 2]
    A_eq = [[1,0,0,0],[0,2,0,0],[1,0,0,0],[1,1,1,1]]
    b_eq = [1,2,1,4]
    res = linprog_ip(c,A_eq = A_eq, b_eq = b_eq)
    _assert_success(res,desired_fun = 4)

def test_singleton_row_ub_1():
    c = [1, 1, 1, 2]
    A_ub = [[1,0,0,0],[0,2,0,0],[-1,0,0,0],[1,1,1,1]]
    b_ub = [1,2,-2,4]
    res = linprog_ip(c,A_ub = A_ub, b_ub = b_ub, bounds = [(None,None),(0,None),(0,None),(0,None)])
    _assert_infeasible(res)
    assert_equal(res.nit, 0)
    
def test_singleton_row_ub_2():
    c = [1, 1, 1, 2]
    A_ub = [[1,0,0,0],[0,2,0,0],[-1,0,0,0],[1,1,1,1]]
    b_ub = [1,2,-0.5,4]
    res = linprog_ip(c,A_ub = A_ub, b_ub = b_ub, bounds = [(None,None),(0,None),(0,None),(0,None)])
    _assert_success(res,desired_fun = 0.5)
    
def test_bug_6690():
    # https://github.com/scipy/scipy/issues/6690
    A_eq=np.array([[ 0.  ,  0.  ,  0.  ,  0.93,  0.  ,  0.65,  0.  ,  0.  ,  0.83,  0.  ]])   
    b_eq=np.array([ 0.9626])
    A_ub=np.array([[ 0.  ,  0.  ,  0.  ,  1.18,  0.  ,  0.  ,  0.  , -0.2 ,  0.  ,
            -0.22],
           [ 0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ],
           [ 0.  ,  0.  ,  0.  ,  0.43,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ],
           [ 0.  , -1.22, -0.25,  0.  ,  0.  ,  0.  , -2.06,  0.  ,  0.  ,
             1.37],
           [ 0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  , -0.25,  0.  ,  0.  ]]) 
    b_ub= np.array([ 0.615,  0.   ,  0.172, -0.869, -0.022])
    bounds=  np.array([[-0.84, -0.97,  0.34,  0.4 , -0.33, -0.74,  0.47,  0.09, -1.45, -0.73],
                   [ 0.37,  0.02,  2.86,  0.86,  1.18,  0.5 ,  1.76,  0.17,  0.32, -0.15]]).T
    c=np.array([-1.64,  0.7 ,  1.8 , -1.06, -1.16,  0.26,  2.13,  1.53,  0.66,  0.28])
    sol=linprog_ip(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
    _assert_success(sol,desired_fun = -1.191)
    
def test_bug_5400():
    # https://github.com/scipy/scipy/issues/5400
    bounds = [
        (0, None),
        (0, 100), (0, 100), (0, 100), (0, 100), (0, 100), (0, 100),
        (0, 900), (0, 900), (0, 900), (0, 900), (0, 900), (0, 900),
        (0, None), (0, None), (0, None), (0, None), (0, None), (0, None)]

    A_ub = np.array([
        [1, -2.99, 0, 0, -3, 0, 0, 0, -1, -1, 0, -1, -1, 1, 1, 0, 0, 0, 0],
        [1, 0, -2.9, -3.1, 0, -3, 0, -1, 0, 0, -1, 0, -1, 0, 0, 1, 1, 0, 0],
        [1, 0, 0, -3.1, 0, 0, -3, -1, -1, 0, -1, -1, 0, 0, 0, 0, 0, 1, 1],
        [0, 1.99, -1, -1, 0, 0, 0, -1, 1/9, 1/9, 0, 0, 0, -1e4, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 2, -1, -1, 0, 0, 0, -1, 1/9, 1/9, 0, -1e4, 0, 0, 0, 0],
        [0, -1, 1.9, 2.1, 0, 0, 0, 1/9, -1, -1, 0, 0, 0, 0, 0, -1e4, 0, 0, 0],
        [0, 0, 0, 0, -1, 2, -1, 0, 0, 0, 1/9, -1, 1/9, 0, 0, 0, -1e4, 0, 0],
        [0, -1, -1, 2.1, 0, 0, 0, 1/9, 1/9, -1, 0, 0, 0, 0, 0, 0, 0, -1e4, 0],
        [0, 0, 0, 0, -1, -1, 2, 0, 0, 0, 1/9, 1/9, -1, 0, 0, 0, 0, 0, -1e4]])
    
    b_ub = np.array([0.0, 0, 0, 0, 0, 0, 0, 0, 0])
    c = np.array([-1.0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    
    res = linprog_ip(c, A_ub, b_ub, bounds=bounds)
    _assert_success(res,desired_fun = -106.63507541835018)

def test_bug_7044():
    # https://github.com/scipy/scipy/issues/7044
    d = json.loads('{"c": [0.5488135039273248, 0.7151893663724195, 0.6027633760716439, 0.5448831829968969, 0.4236547993389047, 0.6458941130666561, 0.4375872112626925, 0.8917730007820798, 0.9636627605010293, 0.3834415188257777, 0.7917250380826646, 0.5288949197529045, 0.5680445610939323, 0.925596638292661, 0.07103605819788694, 0.08712929970154071, 0.02021839744032572, 0.832619845547938, 0.7781567509498505, 0.8700121482468192, 0.978618342232764, 0.7991585642167236, 0.46147936225293185, 0.7805291762864555, 0.11827442586893322, 0.6399210213275238, 0.1433532874090464, 0.9446689170495839, 0.5218483217500717, 0.4146619399905236, 0.26455561210462697, 0.7742336894342167, 0.45615033221654855, 0.5684339488686485, 0.018789800436355142, 0.6176354970758771, 0.6120957227224214, 0.6169339968747569, 0.9437480785146242, 0.6818202991034834, 0.359507900573786, 0.43703195379934145, 0.6976311959272649, 0.06022547162926983, 0.6667667154456677, 0.6706378696181594, 0.2103825610738409, 0.1289262976548533, 0.31542835092418386, 0.3637107709426226, 0.5701967704178796, 0.43860151346232035, 0.9883738380592262, 0.10204481074802807, 0.2088767560948347, 0.16130951788499626, 0.6531083254653984, 0.2532916025397821, 0.4663107728563063, 0.24442559200160274, 0.15896958364551972, 0.11037514116430513, 0.6563295894652734, 0.1381829513486138, 0.1965823616800535, 0.3687251706609641, 0.8209932298479351, 0.09710127579306127, 0.8379449074988039, 0.09609840789396307, 0.9764594650133958, 0.4686512016477016, 0.9767610881903371, 0.604845519745046, 0.7392635793983017, 0.039187792254320675, 0.2828069625764096, 0.1201965612131689, 0.29614019752214493, 0.11872771895424405, 0.317983179393976], "A_eq": [[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 2.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 4.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 6.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.0, 7.0, 7.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.0, 8.0, 8.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.0, 9.0, 9.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 2.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 4.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 6.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.0, 7.0, 7.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.0, 8.0, 8.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.0, 9.0, 9.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 2.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 4.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 6.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.0, 7.0, 7.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.0, 8.0, 8.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.0, 9.0, 9.0], [1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 0.0, 0.0, 3.0, 0.0, 0.0, 3.0, 0.0, 0.0, 3.0, 0.0, 0.0, 4.0, 0.0, 0.0, 4.0, 0.0, 0.0, 4.0, 0.0, 0.0, 5.0, 0.0, 0.0, 5.0, 0.0, 0.0, 5.0, 0.0, 0.0, 6.0, 0.0, 0.0, 6.0, 0.0, 0.0, 6.0, 0.0, 0.0, 7.0, 0.0, 0.0, 7.0, 0.0, 0.0, 7.0, 0.0, 0.0, 8.0, 0.0, 0.0, 8.0, 0.0, 0.0, 8.0, 0.0, 0.0, 9.0, 0.0, 0.0, 9.0, 0.0, 0.0, 9.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 0.0, 0.0, 3.0, 0.0, 0.0, 3.0, 0.0, 0.0, 3.0, 0.0, 0.0, 4.0, 0.0, 0.0, 4.0, 0.0, 0.0, 4.0, 0.0, 0.0, 5.0, 0.0, 0.0, 5.0, 0.0, 0.0, 5.0, 0.0, 0.0, 6.0, 0.0, 0.0, 6.0, 0.0, 0.0, 6.0, 0.0, 0.0, 7.0, 0.0, 0.0, 7.0, 0.0, 0.0, 7.0, 0.0, 0.0, 8.0, 0.0, 0.0, 8.0, 0.0, 0.0, 8.0, 0.0, 0.0, 9.0, 0.0, 0.0, 9.0, 0.0, 0.0, 9.0, 0.0], [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 0.0, 0.0, 3.0, 0.0, 0.0, 3.0, 0.0, 0.0, 3.0, 0.0, 0.0, 4.0, 0.0, 0.0, 4.0, 0.0, 0.0, 4.0, 0.0, 0.0, 5.0, 0.0, 0.0, 5.0, 0.0, 0.0, 5.0, 0.0, 0.0, 6.0, 0.0, 0.0, 6.0, 0.0, 0.0, 6.0, 0.0, 0.0, 7.0, 0.0, 0.0, 7.0, 0.0, 0.0, 7.0, 0.0, 0.0, 8.0, 0.0, 0.0, 8.0, 0.0, 0.0, 8.0, 0.0, 0.0, 9.0, 0.0, 0.0, 9.0, 0.0, 0.0, 9.0], [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 2.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 2.0, 3.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 3.0, 4.0, 0.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 4.0, 5.0, 0.0, 0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 5.0, 6.0, 0.0, 0.0, 0.0, 6.0, 0.0, 0.0, 0.0, 6.0, 7.0, 0.0, 0.0, 0.0, 7.0, 0.0, 0.0, 0.0, 7.0, 8.0, 0.0, 0.0, 0.0, 8.0, 0.0, 0.0, 0.0, 8.0, 9.0, 0.0, 0.0, 0.0, 9.0, 0.0, 0.0, 0.0, 9.0], [0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 2.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 3.0, 0.0, 3.0, 0.0, 3.0, 0.0, 0.0, 0.0, 0.0, 4.0, 0.0, 4.0, 0.0, 4.0, 0.0, 0.0, 0.0, 0.0, 5.0, 0.0, 5.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 6.0, 0.0, 6.0, 0.0, 6.0, 0.0, 0.0, 0.0, 0.0, 7.0, 0.0, 7.0, 0.0, 7.0, 0.0, 0.0, 0.0, 0.0, 8.0, 0.0, 8.0, 0.0, 8.0, 0.0, 0.0, 0.0, 0.0, 9.0, 0.0, 9.0, 0.0, 9.0, 0.0, 0.0]], "b_eq": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 15.0, 15.0, 15.0, 15.0, 15.0, 15.0, 15.0, 15.0]}')
    A_eq = np.array(d["A_eq"])
    b_eq = np.array(d["b_eq"])
    c = np.array(d["c"])
    sol = linprog_ip(c, A_eq = A_eq, b_eq = b_eq,options = dict(presolve=False, sym_pos = False, pc=False)) # no presolve speeds it up
    _assert_success(sol,desired_fun = 1.730550597)
    

def test_callback():
    # Check that callback is as advertised
    callback_complete = [False]
    last_xk = []

    def cb(xk, **kwargs):
        kwargs.pop('tableau')
        assert_(isinstance(kwargs.pop('phase'), int))
        assert_(isinstance(kwargs.pop('nit'), int))

        i, j = kwargs.pop('pivot')
        assert_(np.isscalar(i))
        assert_(np.isscalar(j))

        basis = kwargs.pop('basis')
        assert_(isinstance(basis, np.ndarray))
        assert_(basis.dtype == np.int_)

        complete = kwargs.pop('complete')
        assert_(isinstance(complete, bool))
        if complete:
            last_xk.append(xk)
            callback_complete[0] = True
        else:
            assert_(not callback_complete[0])

        # no more kwargs
        assert_(not kwargs)
    
    c = np.array([-3,-2])
    A_ub = [[2,1], [1,1], [1,0]]
    b_ub = [10,8,4]
    res = linprog(c,A_ub=A_ub,b_ub=b_ub, callback=cb)

    assert_(callback_complete[0])
    assert_allclose(last_xk[0], res.x)


def test_unknown_options_or_solver():
    c = np.array([-3,-2])
    A_ub = [[2,1], [1,1], [1,0]]
    b_ub = [10,8,4]

    _assert_warns(OptimizeWarning, linprog,
                  c, A_ub=A_ub, b_ub=b_ub, options=dict(spam='42'))

    assert_raises(ValueError, linprog,
                  c, A_ub=A_ub, b_ub=b_ub, method='ekki-ekki-ekki')

def test_no_constraints(): #trivially unbounded
    res = linprog_ip([-1, 1])
    _assert_unbounded(res)
    assert_equal(res.x, [np.inf, 0])


def test_simple_bounds():
    res = linprog_ip([1, 2], bounds=(1, 2))
    _assert_success(res, desired_x=[1, 1])
    res = linprog_ip([1, 2], bounds=[(1, 2), (1, 2)])
    _assert_success(res, desired_x=[1, 1])


def test_invalid_inputs():
    for bad_bound in [[(5, 0), (1, 2), (3, 4)],
                      [(1, 2), (3, 4)],
                      [(1, 2), (3, 4), (3, 4, 5)],
                      [(1, 2), (np.inf, np.inf), (3, 4)],
                      [(1, 2), (-np.inf, -np.inf), (3, 4)],
                      ]:
        assert_raises(ValueError, linprog_ip, [1, 2, 3], bounds=bad_bound)

    assert_raises(ValueError, linprog_ip, [1,2], A_ub=[[1,2]], b_ub=[1,2])
    assert_raises(ValueError, linprog_ip, [1,2], A_ub=[[1]], b_ub=[1])
    assert_raises(ValueError, linprog_ip, [1,2], A_eq=[[1,2]], b_eq=[1,2])
    assert_raises(ValueError, linprog_ip, [1,2], A_eq=[[1]], b_eq=[1])
    assert_raises(ValueError, linprog_ip, [1,2], A_eq=[1], b_eq=1)
    assert_raises(ValueError, linprog_ip, [1,2], A_ub=np.zeros((1,1,3)), b_eq=1)


def test_basic_artificial_vars():
    # Test if linprog succeeds when at the end of Phase 1 some artificial
    # variables remain basic, and the row in T corresponding to the
    # artificial variables is not all zero.
    c = np.array([-0.1, -0.07, 0.004, 0.004, 0.004, 0.004])
    A_ub = np.array([[1.0, 0, 0, 0, 0, 0], [-1.0, 0, 0, 0, 0, 0],
                     [0, -1.0, 0, 0, 0, 0], [0, 1.0, 0, 0, 0, 0],
                     [1.0, 1.0, 0, 0, 0, 0]])
    b_ub = np.array([3.0, 3.0, 3.0, 3.0, 20.0])
    A_eq = np.array([[1.0, 0, -1, 1, -1, 1], [0, -1.0, -1, 1, -1, 1]])
    b_eq = np.array([0, 0])
#    res = linprog_ip(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
#                  callback=lambda x, **kwargs: None)
    res = linprog_ip(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq)
    _assert_success(res, desired_fun=0, desired_x=np.zeros_like(c),atol = 2e-6)

def test_bounded_below_only():
    A = np.eye(3)
    b = np.array([1,2,3])
    c = np.ones(3)
    res = linprog_ip(c,A_eq=A,b_eq=b,bounds = (0.5,np.inf))
    _assert_success(res, desired_x=b, desired_fun = np.sum(b))

def test_bounded_above_only():
    A = np.eye(3)
    b = np.array([1,2,3])
    c = np.ones(3)
    res = linprog_ip(c,A_eq=A,b_eq=b,bounds = (-np.inf,4))
    _assert_success(res, desired_x=b, desired_fun = np.sum(b))
    
def unbounded_below_and_above():
    A = np.eye(3)
    b = np.array([1,2,3])
    c = np.ones(3)
    res = linprog_ip(c,A_eq=A,b_eq=b,bounds = (-np.inf,np.inf))
    _assert_success(res, desired_x=b, desired_fun = np.sum(b))

if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_module_suite()
