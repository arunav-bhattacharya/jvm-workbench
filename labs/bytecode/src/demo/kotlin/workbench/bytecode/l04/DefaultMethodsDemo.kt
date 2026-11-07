package workbench.bytecode.l04

import java.lang.reflect.InvocationHandler
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Proxy

interface KLedger {
    fun balanceMinor(account: String): Long

    fun totalMinor(a: String, b: String): Long =       // calls balanceMinor twice, on `this`
        balanceMinor(a) + balanceMinor(b)
}

class RealKLedger : KLedger {
    override fun balanceMinor(account: String) = account.length * 1_000L
}

/** Logs every call it sees. Default methods go either to the target or through invokeDefault. */
fun logging(target: KLedger, useInvokeDefault: Boolean, log: MutableList<String>): KLedger =
    Proxy.newProxyInstance(KLedger::class.java.classLoader, arrayOf(KLedger::class.java)) { proxy, m, args ->
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
    } as KLedger

/** Who is `this` inside a default method? It decides which inner calls the handler sees. */
fun main() {
    val log = mutableListOf<String>()
    var t = logging(RealKLedger(), false, log).totalMinor("ops", "fees")
    println("forward to target: total=$t, handler saw $log")

    log.clear()
    t = logging(RealKLedger(), true, log).totalMinor("ops", "fees")
    println("invokeDefault:     total=$t, handler saw $log")

    // no implementation class at all: the handler answers balanceMinor, the interface supplies totalMinor
    val noTarget = Proxy.newProxyInstance(KLedger::class.java.classLoader, arrayOf(KLedger::class.java)) { proxy, m, a ->
        if (m.isDefault) InvocationHandler.invokeDefault(proxy, m, *a) else 500L
    } as KLedger
    println("no target:         total=${noTarget.totalMinor("x", "y")}")

    try {
        InvocationHandler.invokeDefault(noTarget, KLedger::class.java.getMethod("balanceMinor", String::class.java), "x")
    } catch (e: Throwable) {
        println("invokeDefault on an abstract method -> ${e.javaClass.simpleName}")
    }
}
