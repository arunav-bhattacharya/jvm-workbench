package workbench.patterns.l05

import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Proxy

// Dynamic proxies: a retrying proxy for any interface, and a tracing proxy that shows self-invocation.

fun interface CourierLine { fun book(address: String, grams: Int): String }
interface Stockroom { fun pick(item: String); fun pickBoth(first: String, second: String) }

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
    val busy = CourierLine { _, grams ->
        check(++calls >= 3) { "line busy" }
        "BB-$grams"
    }
    val line = retrying(busy, 3)
    println("book -> ${line.book("12 Mill Lane", 1_250)} after $calls target calls")
    println("proxy class: ${Proxy.isProxyClass(line.javaClass)}")

    val trace = mutableListOf<String>()
    val real = object : Stockroom {
        override fun pick(item: String) {}
        override fun pickBoth(first: String, second: String) { pick(first); pick(second) }   // this.pick(): skips the proxy
    }
    tracing<Stockroom>(real, trace).pickBoth("tea", "jam")
    println("calls the proxy saw: $trace")
}
