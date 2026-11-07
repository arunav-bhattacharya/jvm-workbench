package workbench.bytecode.l05

import net.bytebuddy.ByteBuddy
import net.bytebuddy.description.method.MethodDescription
import net.bytebuddy.implementation.MethodDelegation
import net.bytebuddy.implementation.bind.annotation.AllArguments
import net.bytebuddy.implementation.bind.annotation.Origin
import net.bytebuddy.implementation.bind.annotation.RuntimeType
import net.bytebuddy.implementation.bind.annotation.SuperCall
import net.bytebuddy.matcher.ElementMatchers.isDeclaredBy
import net.bytebuddy.matcher.ElementMatchers.isPublic
import net.bytebuddy.matcher.ElementMatchers.named
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Method
import java.util.concurrent.Callable
import java.util.function.LongSupplier

object TimingProxies {
    fun <T : Any> subclassTimed(type: Class<T>, clock: LongSupplier, sink: TimingSink): T =
        build(type, SuperCallInterceptor(clock, sink))

    fun <T : Any> forwardingTimed(type: Class<T>, target: T, clock: LongSupplier, sink: TimingSink): T =
        build(type, ForwardingInterceptor(target, clock, sink))

    private fun <T : Any> build(type: Class<T>, interceptor: Any): T =
        ByteBuddy()
            .subclass(type)                                      // throws for final classes
            .method(isPublic<MethodDescription>().and(isDeclaredBy(type)))   // final methods are skipped
            .intercept(
                MethodDelegation.withDefaultConfiguration()
                    .filter(named("intercept"))                  // bind only to intercept(), not equals() etc.
                    .to(interceptor),
            )
            .make()
            .load(type.classLoader)                              // a new child loader holds the generated class
            .loaded
            .getDeclaredConstructor()
            .newInstance()                                       // runs FxQuoteService's constructor as usual

    private inline fun timed(clock: LongSupplier, sink: TimingSink, method: Method, call: () -> Any?): Any? {
        val name = "${method.declaringClass.simpleName}.${method.name}"
        val start = clock.asLong
        try {
            val result = call()
            sink.record(name, clock.asLong - start, false)
            return result
        } catch (e: Throwable) {
            sink.record(name, clock.asLong - start, true)
            throw e
        }
    }

    /** The instance is the subclass: zuper.call() runs the original body ON THIS OBJECT. */
    class SuperCallInterceptor(private val clock: LongSupplier, private val sink: TimingSink) {
        @RuntimeType
        fun intercept(@Origin method: Method, @SuperCall zuper: Callable<*>): Any? =
            timed(clock, sink, method) { zuper.call() }          // the original exception, unwrapped
    }

    /** A separate target: the original body runs on the TARGET, whose `this` calls skip the proxy. */
    class ForwardingInterceptor(private val target: Any, private val clock: LongSupplier, private val sink: TimingSink) {
        @RuntimeType
        fun intercept(@Origin method: Method, @AllArguments args: Array<Any?>): Any? =
            timed(clock, sink, method) {
                try {
                    method.invoke(target, *args)
                } catch (e: InvocationTargetException) {
                    throw e.cause!!                              // unwrap, as in lesson 4
                }
            }
    }
}
