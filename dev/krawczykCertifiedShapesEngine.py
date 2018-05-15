from snappy import snap
from snappy.sage_helper import _within_sage, SageNotAvailable

from snappy import Verify

if _within_sage:
    from sage.rings.complex_interval_field import ComplexIntervalField
    from sage.rings.real_mpfi import RealIntervalField
    from sage.all import ComplexDoubleField
    from sage.all import matrix
    from sage.matrix.constructor import block_matrix
    from sage.modules.free_module_element import vector
    from snappy.pari import prec_dec_to_bits

__all__ = ['KrawczykCertifiedShapesEngine']

class KrawczykCertifiedShapesEngine:

    """
    An engine that is initialized with an approximated candidate solution to
    the rectangular gluing equations and produces intervals certified to
    contain a true solution. After the engine is successfully run, the
    resulting intervals are stored in certified_shapes which is a vector of
    elements in a Sage's ComplexIntervalField.

    SOME OF THIS NEEDS TO BE UPDATED OR COMPLETED.

    Its objective is thus the same as HIKMOT and it is certainly HIKMOT
    inspired. However, it conceptually differs in that:

    1. It uses complex numbers in it's computations.
       We simply use Sage's complex interval type avoiding the need of
       converting n x n complex matrices into 2n x 2n real matrices as
       described Section 3.4 of the HIKMOT paper.
       
    2. We avoid automatic differentiation.  We pick an independent set of
       equations of the following form and try to solve them:

               log(LHS) = 0

       where
       
               LHS =  c * z0^a0 * (1-z0)^b0 *  z1^a1 * (1-z1)^b1 * ...

       with a, b and c's as returned by Manifold.gluing_equations('rect').

       The derivative of log (LHS) with respect to zj is simply given by

                            aj/zj - bj/(1-zj)
         
       and thus no need for automatic differentiation.

    In contrast to HIKMOT, we use and return Sage's native implementation of
    (complex) interval arithmetic here, which allows for increased interoperability. 
    Another advantage is that Sage supports arbitrary precision. Unfortunately,
    performance suffers and this implementation is 5-10 times slower than HIKMOT.

    Here is an example how to explicitly invoke the KrawczykCertifiedShapesEngine::

        sage: shapes = M.tetrahedra_shapes('rect', bits_prec = 80)
        sage: C = KrawczykCertifiedShapesEngine(M, shapes, bits_prec = 80)
        sage: C.expand_until_certified()
        True
        sage: C.certified_shapes # doctest: +ELLIPSIS
        (0.662358978622373012981? + 0.562279512062301243...?*I, 0.66235897862237301298...? + 0.562279512062301243...?*I, 0.66235897862237301298...? + 0.562279512062301243...?*I)

    """

    def log_gluing_LHSs(self, shapes):
        """
        Given the result of M.gluing_equations('rect') or a
        subset of rows of it and shapes, return a vector of
        log(LHS) where

           LHS = c * z0 ** a0 * (1-z0) ** b0 * z1 ** a1 * ...

        Let f: C^n -> C^n denote the function which takes
        shapes and returns the vector of log(LHS).

        The reason we take the logarithm of the rectangular
        gluing equations is because the logarithmic derivative
        is of a particular nice form::

            sage: from snappy import Manifold
            sage: M = Manifold("m019")
            sage: equations = M.gluing_equations('rect')
            sage: RIF = RealIntervalField(80)
            sage: CIF = ComplexIntervalField(80)
            sage: zero = CIF(0).center()
            sage: shape1 = CIF(RIF(0.78055,0.78056), RIF(0.9144, 0.9145))
            sage: shape2 = CIF(RIF(0.46002,0.46003), RIF(0.6326, 0.6327))

        An interval solution containing the true solution. The log of each
        rectangular equation should be 0 for the true solution, hence the interval
        should contain zero::

            sage: shapes = [shape1, shape1, shape2]
            sage: LHSs = KrawczykCertifiedShapesEngine.log_gluing_LHSs(equations, shapes)
            sage: LHSs # doctest: +ELLIPSIS
            (0.000? + 0.000?*I, 0.000? + 0.000?*I, 0.000? + 0.000?*I, 0.000...? + 0.000...?*I, 0.000? + 0.000?*I)
            sage: zero in LHSs[0]
            True

        An interval not containing the true solution::

            sage: shapes = [shape1, shape1, shape1]
            sage: LHSs = KrawczykCertifiedShapesEngine.log_gluing_LHSs(equations, shapes)
            sage: LHSs # doctest: +ELLIPSIS
            (0.430? - 0.078?*I, -0.2...? + 0.942?*I, -0.1...? - 0.8...?*I, 0.000...? + 0.000...?*I, 0.430? - 0.078?*I)
            sage: zero in LHSs[0]
            False

        """

        # Determine the field (should be ComplexField
        # or ComplexIntervalField with some precision)
        # of the shapes
        BaseField = shapes[0].parent()

        one = BaseField(1)
        # The resulting vector as python list
        gluing_LHSs = []
        # Iterate through the rows of the result similar to
        # M.gluing_equations('rect')
        for A, B, c in self.equations:
            # A and B are rows, c is an entry
            # prod keeps the above product
            prod = BaseField(c)
            for a, b, shape in zip(A, B, shapes):
                prod *= (shape ** a) * (one - shape) ** b

            # Take log of the entire product
            gluing_LHSs.append(prod.log())
    
        return vector(BaseField, gluing_LHSs)

    def log_gluing_LHS_derivatives(self, shapes):
        """
        Compute the Jacobian of the vector-valued function f
        described in the above log_gluing_LHSs::

            sage: from snappy import Manifold
            sage: M = Manifold("m019")
            sage: equations = M.gluing_equations('rect')
            sage: RIF = RealIntervalField(80)
            sage: CIF = ComplexIntervalField(80)
            sage: shape1 = CIF(RIF(0.78055,0.78056), RIF(0.9144, 0.9145))
            sage: shape2 = CIF(RIF(0.46002,0.46003), RIF(0.6326, 0.6327))
            sage: shapes = [shape1, shape1, shape2]
            sage: KrawczykCertifiedShapesEngine.log_gluing_LHS_derivatives(equations, shapes) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
            [  0.292? - 1.66...?*I   0.292? - 1.66...?*I   0.752? - 1.034...?*I]
            [-0.5400? + 0.63...?*I -0.5400? + 0.63...?*I   1.561? + 1.829...?*I]
            [ 0.2482? + 1.034...?*I  0.2482? + 1.034...?*I  -2.313? - 0.795...?*I]
            [ 0.5400? - 0.63...?*I -0.5400? + 0.63...?*I                    0]
            [...-0.4963? - 2.068?*I  1.0800? - 1.26...?*I   0.752? - 1.034...?*I]
        
        """

        # Similar to log_gluing_LHS
        BaseField = shapes[0].parent()
        zero = BaseField(0)
        one  = BaseField(1)
        
        # 1 /    z for each shape z
        shape_inverses           = [ one / shape         for shape in shapes ]

        # 1 / (1-z) for each shape z
        one_minus_shape_inverses = [ one / (one - shape) for shape in shapes ] 

        gluing_LHS_derivatives = []
        for A, B, c in self.equations:
            row = []
            for a, b, shape_inverse,  one_minus_shape_inverse in zip(
                A, B, shape_inverses, one_minus_shape_inverses):
                # Equation for the derivative
                #     derivative = (   a /      z -  b / (1-z) )
                derivative = zero
                if not a == 0:
                    derivative  = BaseField(int(a)) * shape_inverse
                if not b == 0:
                    derivative -= BaseField(int(b)) * one_minus_shape_inverse

                row.append( derivative )
            
            gluing_LHS_derivatives.append(row)
    
        return matrix(BaseField, gluing_LHS_derivatives)

    def log_gluing_LHS_derivatives_sparse(self, shapes):
        # Similar to log_gluing_LHS
        BaseField = shapes[0].parent()
        zero = BaseField(0)
        one  = BaseField(1)
        
        gluing_LHS_derivatives = []

        for eqns_column, shape in zip(self.sparse_equations, shapes):
            shape_inverse = one / shape
            one_minus_shape_inverse = one / (one - shape)

            column = []
            for r, (a, b) in eqns_column:
                derivative = zero
                if not a == 0:
                    derivative  = BaseField(int(a)) * shape_inverse
                if not b == 0:
                    derivative -= BaseField(int(b)) * one_minus_shape_inverse
                column.append((r, derivative))
            gluing_LHS_derivatives.append(column)
        return gluing_LHS_derivatives
    
    #@staticmethod
    def matrix_times_sparse(self, m, sparse_m):

        return matrix(self.CIF, Verify.matrix_times_sparse(m, sparse_m))

        CIF = m.base_ring()
        zero = CIF(0)
        rows = []
        for row in m.rows():
            result_row = []
            for col in sparse_m:
                v = zero
                for r, d in col:
                    v += d * row[r]
                result_row.append(v)
            rows.append(result_row)
        return matrix(CIF, rows)

    @staticmethod
    def interval_vector_mid_points(vec):
        """
        Given a vector of complex intervals, return the midpoints (as 0-length
        complex intervals) of them.
        """
        # Should be ComplexIntervalField with the desired precision
        BaseField = vec[0].parent()

        return vec.apply_map(lambda shape: BaseField(shape.center()))

    def krawczyk_iteration(self, shape_intervals):
        """
        SOME OF THIS NEEDS TO BE UPDATED OR COMPLETED.

        A very approximate solution::

            sage: from snappy import Manifold
            sage: M = Manifold("m019")
            sage: shapes = [ 0.7+1j, 0.7+1j, 0.5+0.5j ]

        Get the equations and initialize zero-length intervals from it::
        
            sage: C = KrawczykCertifiedShapesEngine(M, shapes, bits_prec = 80)
            sage: C.initial_shapes
            (0.69999999999999995559107902? + 1*I, 0.69999999999999995559107902? + 1*I, 0.50000000000000000000000000? + 0.50000000000000000000000000?*I)

        Do several Newton interval operations to get a better solution::

            sage: shape_intervals = C.initial_shapes
            sage: for i in range(4): # doctest: +ELLIPSIS
            ...     shape_intervals = KrawczykCertifiedShapesEngine.krawczyk_iteration(C.equations, shape_intervals)
            ...     print shape_intervals
            (0.78674683118381457770...? + 0.9208680745160821379529?*I, 0.786746831183814577703...? + 0.9208680745160821379529?*I, 0.459868058287098030934...? + 0.61940871855835167317...?*I)
            (0.78056102517632648594...? + 0.9144962118446750482...?*I, 0.78056102517632648594...? + 0.9144962118446750482...?*I, 0.4599773577869384936554? + 0.63251940718694538695...?*I)
            (0.78055253104531610049...? + 0.9144736621585220345231?*I, 0.780552531045316100497...? + 0.9144736621585220345231?*I, 0.460021167103732494700...? + 0.6326241909236695020810...?*I)
            (0.78055252785072483256...? + 0.91447366296772644033...?*I, 0.7805525278507248325678? + 0.914473662967726440333...?*I, 0.4600211755737178641204...? + 0.6326241936052562241142...?*I)

        For comparison::

            sage: M.tetrahedra_shapes('rect')
            [0.780552527850725 + 0.914473662967726*I, 0.780552527850725 + 0.914473662967726*I, 0.460021175573718 + 0.632624193605256*I]
        
        Start with a rather big interval, note that the Newton interval method is
        stable in the sense that the interval size decreases::
        
            sage: box = C.CIF(C.RIF(-0.0001,0.0001),C.RIF(-0.0001,0.0001))
            sage: shape_intervals = C.initial_shapes.apply_map(lambda shape: shape + box)
            sage: shape_intervals
            (0.700? + 1.000?*I, 0.700? + 1.000?*I, 0.500? + 0.500?*I)
            sage: for i in range(7): 
            ...     shape_intervals = KrawczykCertifiedShapesEngine.newton_iteration(C.equations, shape_intervals)
            sage: print shape_intervals # doctest: +ELLIPSIS
            (0.78055252785072483798...? + 0.91447366296772645593...?*I, 0.7805525278507248379869? + 0.914473662967726455938...?*I, 0.460021175573717872891...? + 0.632624193605256171637...?*I)
        

        """

        # Compute (DF)(z)
        derivatives_sparse = self.log_gluing_LHS_derivatives_sparse(shape_intervals)

        return (  self.initial_shapes
                - self.approx_inverse_times_interval_value_at_point
                + (self.identity - 
                   self.matrix_times_sparse(
                        self.approx_inverse_double, derivatives_sparse)) *
                  (shape_intervals - self.initial_shapes))

    @staticmethod
    def interval_vector_is_contained_in(vecA, vecB):
        """
        Given two vectors of intervals, return whether the first one
        is contained in the second one.  Examples::

            sage: RIF = RealIntervalField(80)
            sage: CIF = ComplexIntervalField(80)
            sage: box = CIF(RIF(-1,1),RIF(-1,1))
            sage: a = [ CIF(0.1), CIF(1) + box ]
            sage: b = [ CIF(0) + box, CIF(1) + 2 * box ]
            sage: c = [ CIF(0), CIF(1) + 3 * box ]

            sage: KrawczykCertifiedShapesEngine.interval_vector_is_contained_in(a, b)
            True
            sage: KrawczykCertifiedShapesEngine.interval_vector_is_contained_in(a, c)
            False
            sage: KrawczykCertifiedShapesEngine.interval_vector_is_contained_in(b, a)
            False
            sage: KrawczykCertifiedShapesEngine.interval_vector_is_contained_in(b, c)
            False
            sage: KrawczykCertifiedShapesEngine.interval_vector_is_contained_in(c, a)
            False
            sage: KrawczykCertifiedShapesEngine.interval_vector_is_contained_in(c, b)
            False
        """
        return all([(a in b) for a, b in zip(vecA, vecB)])

    @staticmethod
    def interval_vector_union(vecA, vecB):
        """
        Given two vectors of intervals, return the vector of their unions,
        i.e., the smallest interval containing both intervals.
        """

        return vector([ a.union(b) for a, b in zip(vecA, vecB) ])

    def certified_krawczyk_iteration(self, shape_intervals):
        """
        SOME OF THIS NEEDS TO BE UPDATED OR COMPLETED.

        Given shape intervals z, performs a Krawczyk interval iteration N(z)
        as described in newton_iteration. Returns a pair (boolean, N(z)) where
        the boolean is True if N(z) is contained in z.

        If the boolean is True, it is certified that N(z) contains a true
        solution, e.g., a point for which f is truely zero.

        See newton_iteration for the other parameters.

        This follows from Theorem 1 of `Zgliczynski's notes
        <http://ww2.ii.uj.edu.pl/~zgliczyn/cap07/krawczyk.pdf>`_.  

        Some examples::
        
            sage: from snappy import Manifold
            sage: M = Manifold("m019")
            sage: C = KrawczykCertifiedShapesEngine(M, M.tetrahedra_shapes('rect'),
            ...                           bits_prec = 80)

        Intervals containing the true solution::

            sage: good_shapes = vector([
            ...       C.CIF(C.RIF(0.78055, 0.78056), C.RIF(0.91447, 0.91448)),
            ...       C.CIF(C.RIF(0.78055, 0.78056), C.RIF(0.91447, 0.91448)),
            ...       C.CIF(C.RIF(0.46002, 0.46003), C.RIF(0.63262, 0.63263))])
            sage: is_certified, shapes = KrawczykCertifiedShapesEngine.certified_newton_iteration(C.equations, good_shapes)

            sage: is_certified
            True
            sage: shapes  # doctest: +ELLIPSIS
            (0.78055253? + 0.91447366...?*I, 0.7805525...? + 0.9144736...?*I, 0.4600211...? + 0.632624...?*I)

        This means that a true solution to the rectangular gluing equations is
        contained in both the given intervals (good_shapes) and the returned
        intervals (shapes) which are a refinement of the given intervals.

        Intervals not containing a true solution::

            sage: bad_shapes = vector([
            ...       C.CIF(C.RIF(0.78054, 0.78055), C.RIF(0.91447, 0.91448)),
            ...       C.CIF(C.RIF(0.78055, 0.78056), C.RIF(0.91447, 0.91448)),
            ...       C.CIF(C.RIF(0.46002, 0.46003), C.RIF(0.63262, 0.63263))])
            sage: is_certified, shapes = KrawczykCertifiedShapesEngine.certified_newton_iteration(C.equations, bad_shapes)
            sage: is_certified
            False

        """


        new_shapes = self.krawczyk_iteration(shape_intervals)
        return (
            KrawczykCertifiedShapesEngine.interval_vector_is_contained_in(
                new_shapes, shape_intervals),
            new_shapes)
        
    def __init__(self, M, initial_shapes, bits_prec = None, dec_prec = None):
        """
        Initializes the KrawczykCertifiedShapesEngine given an orientable SnapPy
        Manifold M, approximated solutions initial_shapes to the
        gluing equations (e.g., as returned by M.tetrahedra_shapes('rect'))
        and the precision to be used for the desired computations in either
        bits bits_prec or decimal digits dec_prec.

        This requires Sage since it uses Sage's ComplexIntervalField for its
        computations.

        Note that this will choose an independent set of edge equations and
        one equation per cusp. It is known that a solution to such a subset of
        rectangular gluing equations is also a solution to the full set of
        rectangular gluing equations::

            sage: from snappy import Manifold
            sage: M = Manifold("m019")

            sage: C = KrawczykCertifiedShapesEngine(M, M.tetrahedra_shapes('rect'), bits_prec = 53)
            sage: C.expand_until_certified()
            True
            sage: C.certified_shapes # doctest: +ELLIPSIS
            (0.780552527850...? + 0.914473662967...?*I, 0.780552527850...? + 0.91447366296773?*I, 0.4600211755737...? + 0.6326241936052...?*I)

        Does not work with non-orientable manifolds::

            sage: M = Manifold("m000")
            sage: KrawczykCertifiedShapesEngine(M, M.tetrahedra_shapes('rect'), bits_prec = 53)
            Traceback (most recent call last):
            ...
            Exception: Manifold needs to be orientable


        Or some non-hyperbolic manifolds::
        
            sage: Manifold("t02333(1,0)").tetrahedra_shapes(intervals = True)
            Traceback (most recent call last):
            ...
            RuntimeError: Could not certify shape intervals, either there are degenerate shapes or the precision must be increased.

        """

        # Require sage
        if not _within_sage:
            raise SageNotAvailable("Sorry, the verify module can only be used within Sage")

        # Convert to precision in bits if necessary
        if dec_prec:
            self.prec = prec_dec_to_bits(dec_prec)
        elif bits_prec:
            self.prec = bits_prec
        else:
            raise Exception("Need dec_prec or bits_prec")

        # Setup interval types of desired precision
        self.CIF = ComplexIntervalField(self.prec)
        self.RIF = RealIntervalField(self.prec)

        # Verify that manifold is orientable
        if not M.is_orientable():
            raise Exception("Manifold needs to be orientable")

        # Intialize the shape intervals, they have zero length
        self.initial_shapes = vector(
            [self.CIF(shape) for shape in initial_shapes])
        
        # Get an independent set of gluing equations from snap
        self.equations = snap.shapes.enough_gluing_equations(M)
        
        self.identity = matrix.identity(self.CIF, len(self.initial_shapes))

        CDF = ComplexDoubleField()

        approx_deriv = self.log_gluing_LHS_derivatives(
            [ CDF(shape) for shape in initial_shapes] )
        self.approx_inverse_double = approx_deriv.inverse()

        self.approx_inverse = self.approx_inverse_double.change_ring(self.CIF)

        # Shapes have not been certified yet
        self.certified_shapes = None

        self._make_sparse_equations()

    def _make_sparse_equations(self):
        num_eqns = len(self.equations)
        self.sparse_equations = [ ]
        for c in range(num_eqns):
            column = []
            for r in range(num_eqns):
                A, B, dummy = self.equations[r]
                a = A[c]
                b = B[c]
                if a != 0 or b != 0:
                    column.append((r, (a,b)))
            self.sparse_equations.append(column)

    def expand_until_certified(self, verbose = False):
        """
        Try Newton interval iterations, expanding the shape intervals
        until we can certify they contain a true solution.
        If succeeded, return True and write certified shapes to
        certified_shapes.
        Set verbose = True for printing additional information.
        """
        
        # In the equation for the Newton interval iteration
        #          N(z) = z_center - ((Df)(z))^-1 f(z_center)
        #
        # We always let z_center be the initial_shapes (which is a 0-length
        # interval) and expand the interval for z.
        # We evaluate the interval value of f(z_center) only once, here:
        self.interval_value_at_initial_shapes = self.log_gluing_LHSs(
            self.initial_shapes)

        self.approx_inverse_times_interval_value_at_point = (
            self.approx_inverse * self.interval_value_at_initial_shapes)

        # Initialize the interval shapes to be the initial shapes
        shapes = self.initial_shapes

        # Number of iterations we do before giving up.
        # For double precision, give up quickly because failure to
        # converge here most likely indicates we need to use higher
        # precision.
        num_iterations = (25 if self.prec > 53 else 11)

        # Do several Newton interval iteration
        for i in range(num_iterations + 1):
            # Remember the old shapes
            old_shapes = shapes

            # Do the Newton step
            try:
                is_certified, shapes = (
                    self.certified_krawczyk_iteration(shapes))
            except ZeroDivisionError:
                if verbose:
                    print("Division by zero in interval Gaussian elimination")
                return False

            # If the shapes are certified, set them, we are done
            if is_certified:
                if verbose:
                    print("Certified shapes after %d iterations" % (i + 1))

                self.certified_shapes = shapes
                return True

            # Expand the shape intervals by taking the union of the
            # old and new shapes
            shapes = KrawczykCertifiedShapesEngine.interval_vector_union(shapes,
                                                                         old_shapes)

            # Make it much faster
            if i == 0:
                shapes = shapes.apply_map(lambda z: z + (z - z) / 64)

        # After several iterations, still no certified shapes, give up.
        if verbose:
            print("Could not certify shapes")

        return False