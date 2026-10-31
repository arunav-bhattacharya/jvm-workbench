package workbench.patterns.l05

import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Proxy

// Dynamic proxies: a retrying proxy for any interface, and a tracing proxy that shows self-invocation.

fun interface PspClient { fun charge(token: String, amountMinor: Long): String }
interface Ledger { fun post(entry: String); fun postTwice(entry: String) }

// reified T replaces the Class<T> parameter the Java version needs
inline fun <reified T : Any> retrying(target: T, maxAttempts: Int): T =
    Proxy.newProxyInstance(T::class.java.classLoader, arrayOf(T::class.java)) { _, method, args ->
        var last: Throwable? = null
        repeat(maxAttempts) {
            try {
                return@newProxyInstance method.invoke(target, *(args ?: emptyArray()))
            } catch (e: InvocationTargetException) {      // unwrap, or callers see a reflective wrapper
                last = e.cause
            }
        }
        throw last!!
    } as T

inline fun <reified T : Any> tracing(target: T, trace: MutableList<String>): T =
    Proxy.newProxyInstance(T::class.java.classLoader, arrayOf(T::class.java)) { _, method, args ->
        trace += method.name
        try {
            method.invoke(target, *(args ?: emptyArray()))
        } catch (e: InvocationTargetException) {
            throw e.cause!!
        }
    } as T

fun main() {
    var calls = 0
    val flaky = PspClient { _, amount ->
        check(++calls >= 3) { "PSP 503" }
        "ch_$amount"
    }
    val psp = retrying(flaky, 3)
    println("charge -> ${psp.charge("tok_42", 1_250)} after $calls target calls")
    println("proxy class: ${Proxy.isProxyClass(psp.javaClass)}")

    val trace = mutableListOf<String>()
    val real = object : Ledger {
        override fun post(entry: String) {}
        override fun postTwice(entry: String) { post(entry); post(entry) }   // this.post(): skips the proxy
    }
    tracing<Ledger>(real, trace).postTwice("fee 3.20")
    println("calls the proxy saw: $trace")
}
