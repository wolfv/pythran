#ifndef PYTHONIC_INCLUDE_TYPES_TRAITS_HPP
#define PYTHONIC_INCLUDE_TYPES_TRAITS_HPP

#include <complex>

namespace pythonic
{

  namespace types
  {

    /* could overload is_scalar to consider complex has scalar types */
    template <class T>
    struct is_complex {
      static constexpr bool value = false;
      using type = T;
    };

    template <class T>
    struct is_complex<std::complex<T>> {
      static constexpr bool value = true;
      using type = T;
    };

#define MEMBER_TYPE_TRAIT(check_struct, member)                                \
  template <typename T>                                                        \
  struct check_struct {                                                        \
    template <class C>                                                         \
    static auto _test(int)                                                     \
        -> decltype(std::declval<typename C::member>(), std::true_type());     \
    template <class>                                                           \
    static auto _test(...) -> std::false_type;                                 \
    static const bool value =                                                  \
        std::is_same<decltype(                                                 \
                         _test<typename std::remove_reference<T>::type>(0)),   \
                     std::true_type>::value;                                   \
  };

#define MEMBER_ATTR_TRAIT(check_struct, member, ...)                           \
  template <typename T>                                                        \
  struct check_struct {                                                        \
    template <class C>                                                         \
    static auto _test(int)                                                     \
        -> decltype(std::declval<C>().member(__VA_ARGS__), std::true_type());  \
    template <class>                                                           \
    static auto _test(...) -> std::false_type;                                 \
    static const bool value =                                                  \
        std::is_same<decltype(                                                 \
                         _test<typename std::remove_reference<T>::type>(0)),   \
                     std::true_type>::value;                                   \
  };

    /* trait to check if a type is iterable*/
    MEMBER_TYPE_TRAIT(is_iterable, iterator);

    /* trait to check if a type is callable */
    MEMBER_TYPE_TRAIT(is_callable, callable);

    /* trait to check if a type is pure */
    MEMBER_TYPE_TRAIT(is_pure, pure);

    /* trait to check if the type has a size member */
    MEMBER_ATTR_TRAIT(has_size, size);

    /* trait to check if the type has a contains member */
    template <typename T, class V>
    struct has_contains {
      template <class C>
      static auto _test(int)
          -> decltype(std::declval<C>().contains(std::declval<V>()),
                      std::true_type());
      template <class>
      static auto _test(...) -> std::false_type;
      static const bool value =
          std::is_same<decltype(
                           _test<typename std::remove_reference<T>::type>(0)),
                       std::true_type>::value;
    };

    /* trait to check if the type has a shape member */
    MEMBER_ATTR_TRAIT(has_shape, shape);

    /* trait to check if the type has a static size */
    template <class T>
    struct len_of {
      static long constexpr value = -1;
    };
  }
}

#endif