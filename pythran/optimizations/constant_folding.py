"""
ConstantFolding performs some kind of partial evaluation.
"""
import ast
import types
import numpy
import itertools
from pythran.analyses import ConstantExpressions, Aliases
from pythran.passmanager import Transformation
from pythran.tables import modules, cxx_keywords
from pythran.transformations import NormalizeTuples


class ConstantFolding(Transformation):
    '''
    Replace constant expression by their evaluation.

    >>> import ast, passmanager, backend
    >>> node = ast.parse("def foo(): return 1+3")
    >>> pm = passmanager.PassManager("test")
    >>> node = pm.apply(ConstantFolding, node)
    >>> print pm.dump(backend.Python, node)
    def foo():
        return 4
    '''

    # maximum length of folded sequences
    # containers larger than this are not unfolded to limit code size growth
    MAX_LEN = 2 ** 8

    class ConversionError(Exception):
        pass

    class ToNotEval(Exception):
        """
            Exception raised when we don't want to evaluate the value (case of
            too long expression for example).
        """
        pass

    def __init__(self):
        Transformation.__init__(self, ConstantExpressions, Aliases)

    def prepare(self, node, ctx):
        self.env = {'__builtin__': __import__('__builtin__')}

        for module_name in modules:
            not_builtin = ["__builtin__", "__exception__", "__dispatch__",
                           "__iterator__"]
            # module starting with "__" are pythran internal module and
            # should not be imported in the Python interpreter
            if not module_name.startswith('__'):
                import_name = module_name
                if (module_name.endswith("_")
                        and module_name[:-1] in cxx_keywords):
                    import_name = module_name[:-1]
                self.env[module_name] = __import__(import_name)
            elif module_name not in not_builtin:
                if module_name == "__ndarray__":
                    self.env["numpy"] = __import__("numpy")
                    self.env[module_name] = numpy.ndarray
                else:
                    try:
                        self.env[module_name] = \
                            __import__(module_name.strip('_'))
                    except:
                        try:
                            # should try from another package than builtin,
                            # e.g. for ndarray
                            self.env[module_name] = getattr(
                                self.env['__builtin__'],
                                module_name.strip('_'))
                        except:
                            pass

        try:
            eval(compile(node, '<constant_folding>', 'exec'), self.env)
        except Exception as e:
            print ast.dump(node)
            print 'error in constant folding: ', e
            pass
        super(ConstantFolding, self).prepare(node, ctx)

    def to_ast(self, value):
        numpy_type = (numpy.float64, numpy.float32, numpy.float16,
                      numpy.complex_, numpy.complex64, numpy.complex128,
                      numpy.float_, numpy.uint8, numpy.uint16, numpy.uint32,
                      numpy.uint64, numpy.int8, numpy.int16, numpy.int32,
                      numpy.int64, numpy.intp, numpy.intc, numpy.int_,
                      numpy.bool_)
        unfolded_type = (types.BuiltinFunctionType, types.BuiltinMethodType,
                         types.FunctionType, types.TypeType, types.XRangeType,
                         numpy.ufunc, type(list.append), types.FileType,
                         BaseException, types.GeneratorType, itertools.count)
        if (type(value) in (int, long, float, complex)):
            return ast.Num(value)
        elif isinstance(value, bool):
            return ast.Attribute(ast.Name('__builtin__', ast.Load()),
                                 'True' if value else 'False', ast.Load())
        elif isinstance(value, str):
            return ast.Str(value)
        elif isinstance(value, list):
            if len(value) < ConstantFolding.MAX_LEN:
                return ast.List(map(self.to_ast, value), ast.Load())
            else:
                raise ConstantFolding.ToNotEval()
        elif isinstance(value, tuple):
            if len(value) < ConstantFolding.MAX_LEN:
                return ast.Tuple(map(self.to_ast, value), ast.Load())
            else:
                raise ConstantFolding.ToNotEval()
        elif isinstance(value, set):
            if len(value) < ConstantFolding.MAX_LEN:
                return ast.Set(map(self.to_ast, value))
            else:
                raise ConstantFolding.ToNotEval()
        elif isinstance(value, dict):
            if len(value) < ConstantFolding.MAX_LEN:
                keys = map(self.to_ast, value.iterkeys())
                values = map(self.to_ast, value.itervalues())
                return ast.Dict(keys, values)
            else:
                raise ConstantFolding.ToNotEval()
        elif isinstance(value, types.NoneType):
            return ast.Attribute(ast.Name('__builtin__', ast.Load()),
                                 'None',
                                 ast.Load())
        elif isinstance(value, numpy.ndarray):
            return ast.Call(func=ast.Attribute(ast.Name('numpy', ast.Load()),
                                               'array',
                                               ast.Load()),
                            args=[self.to_ast(value.tolist())],
                            keywords=[],
                            starargs=None,
                            kwargs=None)
        elif isinstance(value, numpy_type):
            return self.to_ast(numpy.asscalar(value))
        elif isinstance(value, unfolded_type):
            raise ConstantFolding.ToNotEval()
        else:
            raise ConstantFolding.ConversionError()

    def generic_visit(self, node):
        if node in self.constant_expressions:
            try:
                fake_node = ast.Expression(
                    node.value if isinstance(node, ast.Index) else node)
                code = compile(fake_node, '<constant folding>', 'eval')
                value = eval(code, self.env)
                new_node = self.to_ast(value)
                if (isinstance(node, ast.Index)
                        and not isinstance(new_node, ast.Index)):
                    new_node = ast.Index(new_node)
                return new_node
            except ConstantFolding.ConversionError as e:
                print ast.dump(node)
                print 'error in constant folding: ', e
                raise
            except ConstantFolding.ToNotEval:
                return Transformation.generic_visit(self, node)
            except AttributeError as e:
                # FIXME expression that use int, bool, float, ... operators
                # are not processed by constant folding
                if e.args[0][-2] == "_":
                    return Transformation.generic_visit(self, node)
                raise
            except NameError as e:
                # FIXME dispatched function are not processed by constant
                # folding
                if "__dispatch__" in e.args[0]:
                    return Transformation.generic_visit(self, node)
                raise
        else:
            return Transformation.generic_visit(self, node)
