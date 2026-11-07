package workbench.container.l02

import java.lang.reflect.InvocationHandler
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Method

/** The handler behind a JDK proxy: four kinds of method, four answers. */
class InterceptingHandler(
    private val target: Any,
    private val chains: Map<Method, List<Interceptor>>,
) : InvocationHandler {

    override fun invoke(proxy: Any, method: Method, args: Array<Any?>?): Any? {
        val a = args ?: emptyArray()                                   // no-argument methods get null
        // 1. equals, hashCode, toString: answer on the proxy, or collections can't find it
        if (method.declaringClass == Any::class.java) {
            return when (method.name) {
                "equals" -> proxy === a[0]
                "hashCode" -> System.identityHashCode(proxy)
                else -> "Proxy[$target]"
            }
        }
        // 2. a default method runs with this = proxy, so the calls inside it come back through here
        if (method.isDefault) return InvocationHandler.invokeDefault(proxy, method, *a)
        // 3. the interceptors, ending in the real method on the target
        val chain = chains[method].orEmpty()
        return Invocation(Interception.nameOf(method), a, chain) {
            try {
                method.invoke(target, *a)
            } catch (e: InvocationTargetException) {
                throw e.cause!!                                        // 4. the target's own exception
            }
        }.proceed()
    }
}
