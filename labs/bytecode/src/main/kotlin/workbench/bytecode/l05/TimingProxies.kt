package workbench.bytecode.l05

import java.util.function.LongSupplier

/**
 * Two kinds of Byte Buddy subclass proxy that time the public methods declared by a class.
 * Name each call `"${method.declaringClass.simpleName}.${method.name}"`, read [LongSupplier]
 * `clock` once before and once after the call, and report failures with `failed = true`
 * before rethrowing the exception unchanged.
 */
object TimingProxies {
    /**
     * The proxy object IS the instance (ArC's intercepted-subclass model). Build
     * `ByteBuddy().subclass(type).method(isPublic().and(isDeclaredBy(type)))` and intercept with
     * `MethodDelegation` to an interceptor that takes `@Origin Method` and `@SuperCall Callable<*>`.
     * Return a new instance of the generated class. Calls the class makes on `this` are timed too.
     */
    fun <T : Any> subclassTimed(type: Class<T>, clock: LongSupplier, sink: TimingSink): T =
        TODO("Byte Buddy subclass + MethodDelegation with @SuperCall")

    /**
     * The proxy forwards every call to a separate [target] (Spring AOP's model). Intercept with an
     * interceptor that takes `@Origin Method` and `@AllArguments Array<Any?>` and calls
     * `method.invoke(target, *args)`, unwrapping `InvocationTargetException`. Calls the target
     * makes on its own `this` are NOT timed.
     */
    fun <T : Any> forwardingTimed(type: Class<T>, target: T, clock: LongSupplier, sink: TimingSink): T =
        TODO("Byte Buddy subclass + MethodDelegation that forwards to target")
}
