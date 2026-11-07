package workbench.container.l03

import net.bytebuddy.ByteBuddy
import net.bytebuddy.description.method.MethodDescription
import net.bytebuddy.implementation.MethodDelegation
import net.bytebuddy.implementation.bind.annotation.AllArguments
import net.bytebuddy.implementation.bind.annotation.Origin
import net.bytebuddy.implementation.bind.annotation.RuntimeType
import net.bytebuddy.implementation.bind.annotation.SuperCall
import net.bytebuddy.matcher.ElementMatchers.isAnnotatedWith
import net.bytebuddy.matcher.ElementMatchers.named
import java.lang.reflect.Constructor
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Method
import java.lang.reflect.Modifier
import java.lang.reflect.Proxy
import java.util.concurrent.Callable
import java.util.function.LongSupplier

/**
 * Builds each component. A component that implements interfaces gets a JDK proxy around a plain
 * instance; one without interfaces gets a Byte Buddy subclass. Nothing to intercept: no proxy at all.
 */
class Interception @JvmOverloads constructor(
    val log: CallLog = CallLog(),
    private val clock: LongSupplier = LongSupplier { System.nanoTime() },
) {
    fun create(component: Class<*>, constructor: Constructor<*>, args: Array<Any?>): Any {
        if (component.interfaces.isNotEmpty()) {
            val chains = component.interfaces.flatMap { it.methods.asList() }.filter(::isIntercepted).associateWith(::chainFor)
            val target = newInstance(constructor, args)
            if (chains.isEmpty()) return target
            return Proxy.newProxyInstance(component.classLoader, component.interfaces, InterceptingHandler(target, chains))
        }
        val chains = component.methods.filter(::isIntercepted).associateWith(::chainFor)
        if (chains.isEmpty()) return newInstance(constructor, args)
        return subclass(component, constructor, args, chains)
    }

    /**
     * Refuses, when the container starts, a component whose interceptors could never run.
     * A JDK proxy sees only the interface's methods. A subclass can't extend a final class, and
     * can't override a final or private method.
     */
    fun check(component: Class<*>) {
        if (component.interfaces.isNotEmpty()) {
            val hidden = component.declaredMethods.filter { isIntercepted(it) && !annotatedOnAnInterface(component, it) }
            if (hidden.isNotEmpty()) {
                val m = hidden.first()
                throw ContainerException("${component.simpleName}.${m.name} has its annotations on the class, but its " +
                    "JDK proxy only sees ${component.interfaces.map { it.simpleName }}: put them on the interface")
            }
            return
        }
        val intercepted = component.declaredMethods.filter(::isIntercepted)
        if (intercepted.isEmpty()) return                                 // nothing to intercept: final is fine
        if (Modifier.isFinal(component.modifiers)) {
            throw ContainerException("${component.simpleName} is final, so no subclass can intercept it: make it open, or give it an interface")
        }
        for (m in intercepted) {
            val why = when {
                Modifier.isPrivate(m.modifiers) -> "private"              // never overridden, even in an open class
                Modifier.isFinal(m.modifiers) -> "final"                  // Kotlin: an open class with a plain fun
                else -> continue
            }
            throw ContainerException("${component.simpleName}.${m.name} is $why, so no subclass can intercept it: make it open")
        }
    }

    /** @Timed outside @Retry, so the recorded time includes every attempt. */
    fun chainFor(method: Method): List<Interceptor> {
        val retry = method.getAnnotation(Retry::class.java)
        return chain(method.isAnnotationPresent(Timed::class.java), retry?.attempts ?: 0,
            *retry?.on?.map { it.java }?.toTypedArray() ?: emptyArray())
    }

    /** The same chain from plain values, for generated code that read the annotations at build time. */
    fun chain(timed: Boolean, retryAttempts: Int, vararg retryOn: Class<out Throwable>): List<Interceptor> = buildList {
        if (timed) add(TimedInterceptor(log, clock))
        if (retryAttempts > 0) add(RetryInterceptor(retryAttempts, retryOn.toList()))
    }

    private fun subclass(component: Class<*>, constructor: Constructor<*>, args: Array<Any?>,
                         chains: Map<Method, List<Interceptor>>): Any {
        val type = ByteBuddy()
            .subclass(component)                                          // copies the public constructors
            .method(isAnnotatedWith<MethodDescription>(Timed::class.java).or(isAnnotatedWith(Retry::class.java)))
            .intercept(MethodDelegation.withDefaultConfiguration().filter(named("intercept")).to(SubclassBridge(chains)))
            .make()
            .load(component.classLoader)                                  // a new child loader per generated class
            .loaded
        return newInstance(type.getConstructor(*constructor.parameterTypes), args)
    }

    companion object {
        @JvmStatic
        fun isIntercepted(m: Method): Boolean =
            m.isAnnotationPresent(Timed::class.java) || m.isAnnotationPresent(Retry::class.java)

        @JvmStatic
        fun nameOf(m: Method): String = "${m.declaringClass.simpleName}.${m.name}"

        private fun annotatedOnAnInterface(component: Class<*>, m: Method): Boolean =
            component.interfaces.any { i ->
                runCatching { i.getMethod(m.name, *m.parameterTypes) }.getOrNull()?.let(::isIntercepted) == true
            }

        private fun newInstance(constructor: Constructor<*>, args: Array<Any?>): Any =
            try {
                constructor.newInstance(*args)
            } catch (e: InvocationTargetException) {
                throw ContainerException("constructor of ${constructor.declaringClass.simpleName} failed", e.cause)
            }
    }
}

/** Byte Buddy calls this for every intercepted method of the subclass. The subclass IS the bean. */
class SubclassBridge(private val chains: Map<Method, List<Interceptor>>) {
    @RuntimeType
    fun intercept(@Origin method: Method, @AllArguments args: Array<Any?>, @SuperCall zuper: Callable<*>): Any? =
        Invocation(Interception.nameOf(method), args, chains.getValue(method), zuper).proceed()   // zuper runs super.method()
}
