package workbench.bytecode.l05

import net.bytebuddy.ByteBuddy
import net.bytebuddy.implementation.MethodDelegation
import net.bytebuddy.implementation.bind.annotation.AllArguments
import net.bytebuddy.implementation.bind.annotation.Origin
import net.bytebuddy.implementation.bind.annotation.RuntimeType
import net.bytebuddy.implementation.bind.annotation.SuperCall
import net.bytebuddy.matcher.ElementMatchers.isDeclaredBy
import java.lang.reflect.Method
import java.util.concurrent.Callable

private val log = mutableListOf<String>()

/** Final, like every Kotlin class without `open`. */
class KotlinCueRunner {
    fun run(cue: String) = "ran $cue"
}

/** Runs one lighting or sound cue. No interface: a JDK proxy can't stand in for it. */
open class KCueRunner {
    init { constructed++ }

    open fun run(cue: String) = "ran $cue (${this.check(cue)})"   // self-call
    open fun check(cue: String) = "checked $cue"
    fun stage() = "main stage"                                    // final: no `open`

    companion object {
        var constructed = 0
    }
}

/** Quarkus ArC style: the generated subclass instance IS the object; @SuperCall runs the original body on it. */
class KInSubclass {
    @RuntimeType
    fun intercept(@Origin m: Method, @SuperCall original: Callable<*>): Any? {
        log += "intercepted ${m.name}"
        return original.call()
    }
}

/** Spring AOP style: the generated subclass forwards to a separate target object. */
class KForwarding(private val target: Any) {
    @RuntimeType
    fun intercept(@Origin m: Method, @AllArguments args: Array<Any?>): Any? {
        log += "forwarded ${m.name}"
        return m.invoke(target, *args)
    }
}

private fun <T : Any> subclass(type: Class<T>, interceptor: Any): Class<out T> =
    ByteBuddy().subclass(type)
        .method(isDeclaredBy(type))
        .intercept(MethodDelegation.withDefaultConfiguration().filter { it.name == "intercept" }.to(interceptor))
        .make().load(type.classLoader).loaded

/** The same subclass proxy, two models: the proxy IS the object, or the proxy forwards to a target. */
fun main() {
    val sub = subclass(KCueRunner::class.java, KInSubclass())
    println("generated ${sub.name}")
    println("declares  ${sub.declaredMethods.map { it.name }.sorted()}")

    val runner = sub.getDeclaredConstructor().newInstance()
    println("${runner.run("LX-14")}, on the ${runner.stage()}")
    println("subclass model:   $log")
    log.clear()

    KCueRunner.constructed = 0
    val target = KCueRunner()
    val proxy = subclass(KCueRunner::class.java, KForwarding(target)).getDeclaredConstructor().newInstance()
    println(proxy.run("LX-15"))
    println("forwarding model: $log, constructors run: ${KCueRunner.constructed}")

    try {
        ByteBuddy().subclass(KotlinCueRunner::class.java).make()
    } catch (e: IllegalArgumentException) {
        println("Kotlin class without open: ${e.message}")
    }
}
