package workbench.container.l03

import java.util.concurrent.Callable

/** Runs around a method call. Call [Invocation.proceed] to go on to the next interceptor, or to the method. */
fun interface Interceptor {
    fun intercept(inv: Invocation): Any?
}

/**
 * One call on its way through a chain of interceptors. [proceed] runs the next interceptor, and
 * after the last one, [target]: the real method. An interceptor may call [proceed] more than once.
 */
class Invocation private constructor(
    val name: String,
    val args: Array<Any?>,
    private val chain: List<Interceptor>,
    private val target: Callable<*>,
    private val index: Int,
) {
    constructor(name: String, args: Array<Any?>, chain: List<Interceptor>, target: Callable<*>) :
        this(name, args, chain, target, 0)

    fun proceed(): Any? =
        if (index == chain.size) target.call()
        else chain[index].intercept(Invocation(name, args, chain, target, index + 1))
}
