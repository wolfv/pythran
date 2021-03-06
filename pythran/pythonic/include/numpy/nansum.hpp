#ifndef PYTHONIC_INCLUDE_NUMPY_NANSUM_HPP
#define PYTHONIC_INCLUDE_NUMPY_NANSUM_HPP

#include "pythonic/include/utils/functor.hpp"
#include "pythonic/include/types/ndarray.hpp"
#include "pythonic/include/numpy/isnan.hpp"

namespace pythonic
{

  namespace numpy
  {
    template <class E, class F>
    void _nansum(E begin, E end, F &sum, utils::int_<1>);

    template <class E, class F, size_t N>
    void _nansum(E begin, E end, F &sum, utils::int_<N>);

    template <class E>
    typename E::dtype nansum(E const &expr);

    DECLARE_FUNCTOR(pythonic::numpy, nansum);
  }
}

#endif
