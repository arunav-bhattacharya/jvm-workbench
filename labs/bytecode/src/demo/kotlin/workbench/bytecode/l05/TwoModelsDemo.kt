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
class KotlinFinalService {
    fun settle(batch: String) = "settled $batch"
}

open class KSettlementService {
    init { constructed++ }

    open fun settle(batch: String) = "settled $batch (${this.audit(batch)})"   // self-call
    open fun audit(batch: String) = "audited $batch"
    fun region() = "eu-west"                                                    // final: no `open`

    companion object {
        var constructed = 0
    }
}

/** ArC-style: the generated subclass instance is the bean; @SuperCall runs the original body on it. */
class KInSubclass {
    @RuntimeType
    fun intercept(@Origin m: Method, @SuperCall original: Callable<*>): Any? {
        log += "intercepted ${m.name}"
        return original.call()
    }
}

/** Spring-style: the generated subclass forwards to a separate target object. */
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
    val sub = subclass(KSettlementService::class.java, KInSubclass())
    println("generated ${sub.name}")
    println("declares  ${sub.declaredMethods.map { it.name }.sorted()}")

    val bean = sub.getDeclaredConstructor().newInstance()
    println("${bean.settle("B-17")}, region ${bean.region()}")
    println("subclass model:   $log")
    log.clear()

    KSettlementService.constructed = 0
    val target = KSettlementService()
    val proxy = subclass(KSettlementService::class.java, KForwarding(target)).getDeclaredConstructor().newInstance()
    println(proxy.settle("B-18"))
    println("forwarding model: $log, constructors run: ${KSettlementService.constructed}")

    try {
        ByteBuddy().subclass(KotlinFinalService::class.java).make()
    } catch (e: IllegalArgumentException) {
        println("Kotlin class without open: ${e.message}")
    }
}
