package workbench.bytecode.l04

import java.lang.reflect.InvocationHandler
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Proxy

interface KScenes {
    fun minutes(scene: String): Int

    fun total(a: String, b: String): Int =       // calls minutes twice, on `this`
        minutes(a) + minutes(b)
}

class RealKScenes : KScenes {
    override fun minutes(scene: String) = scene.length * 10
}

/** Logs every call it sees. Default methods go either to the target or through invokeDefault. */
fun logging(target: KScenes, useInvokeDefault: Boolean, log: MutableList<String>): KScenes =
    Proxy.newProxyInstance(KScenes::class.java.classLoader, arrayOf(KScenes::class.java)) { proxy, m, args ->
        log += m.name
        if (useInvokeDefault && m.isDefault) {
            InvocationHandler.invokeDefault(proxy, m, *args)       // the body runs with this = proxy
        } else {
            try {
                m.invoke(target, *args)                            // the body runs with this = target
            } catch (e: InvocationTargetException) {
                throw e.cause!!
            }
        }
    } as KScenes

/** Who is `this` inside a default method? It decides which inner calls the handler sees. */
fun main() {
    val log = mutableListOf<String>()
    var t = logging(RealKScenes(), false, log).total("prologue", "duel")
    println("forward to target: total=$t, handler saw $log")

    log.clear()
    t = logging(RealKScenes(), true, log).total("prologue", "duel")
    println("invokeDefault:     total=$t, handler saw $log")

    // no implementation class at all: the handler answers minutes, the interface supplies total
    val noTarget = Proxy.newProxyInstance(KScenes::class.java.classLoader, arrayOf(KScenes::class.java)) { proxy, m, a ->
        if (m.isDefault) InvocationHandler.invokeDefault(proxy, m, *a) else 5
    } as KScenes
    println("no target:         total=${noTarget.total("x", "y")}")

    try {
        InvocationHandler.invokeDefault(noTarget, KScenes::class.java.getMethod("minutes", String::class.java), "x")
    } catch (e: Throwable) {
        println("invokeDefault on an abstract method -> ${e.javaClass.simpleName}")
    }
}
