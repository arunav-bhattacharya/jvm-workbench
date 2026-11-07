package workbench.container.l02

import java.lang.reflect.InvocationHandler
import java.lang.reflect.Method

/**
 * The handler behind a JDK proxy. Give each kind of method its own answer, in this order:
 * 1. `equals`, `hashCode`, `toString` (`method.declaringClass == Any::class.java`): answer on the
 *    proxy itself: `proxy === args[0]`, `System.identityHashCode(proxy)`, and `"Proxy[$target]"`.
 * 2. default methods (`method.isDefault`): `InvocationHandler.invokeDefault(proxy, method, *args)`,
 *    so the calls inside the default body come back through this handler.
 * 3. everything else: `Invocation(Interception.nameOf(method), args, chains[method].orEmpty()) { ... }.proceed()`,
 *    where the lambda calls `method.invoke(target, *args)`.
 * 4. unwrap `InvocationTargetException` in that lambda and throw its cause.
 * `args` is null for methods without parameters.
 */
class InterceptingHandler(
    private val target: Any,
    private val chains: Map<Method, List<Interceptor>>,
) : InvocationHandler {

    override fun invoke(proxy: Any, method: Method, args: Array<Any?>?): Any? =
        TODO("Object methods, default methods, the chain, and unwrapping")
}
