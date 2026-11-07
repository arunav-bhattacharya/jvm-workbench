package workbench.bytecode.l04

import java.lang.reflect.InvocationHandler
import java.lang.reflect.Modifier
import java.lang.reflect.Proxy

interface KFxQuotes {
    fun quoteMicros(pair: String): Long
    fun spreadMicros(pair: String): Long = quoteMicros(pair) / 1_000   // a JVM default method (jvmTarget 21)
}

interface KAudited {
    fun auditId(): String
}

/** What Proxy.newProxyInstance generates, which calls reach the handler, and how the class is cached. */
fun main() {
    val seen = mutableListOf<String>()
    val h = InvocationHandler { proxy, m, a ->
        seen += "${m.declaringClass.simpleName}.${m.name}"
        when (m.name) {
            "quoteMicros" -> 1_084_250L
            "hashCode" -> 42
            "equals" -> proxy === a[0]
            "toString" -> "KFxQuotes proxy"
            else -> null
        }
    }
    val app = KFxQuotes::class.java.classLoader
    val q = Proxy.newProxyInstance(app, arrayOf(KFxQuotes::class.java), h) as KFxQuotes

    // 1. the generated class
    val pc = q.javaClass
    println("class      ${Modifier.toString(pc.modifiers)} ${pc.name}")
    println("extends    ${pc.superclass.name}, implements ${pc.interfaces.toList()}")
    println("module     ${pc.module.name}, hidden: ${pc.isHidden}")
    println("fields     ${pc.declaredFields.map { it.name }.sorted()}")
    println("methods    ${pc.declaredMethods.map { it.name }.sorted()}")

    // 2. which calls reach the handler
    q.quoteMicros("EURUSD")
    q.toString()
    q.hashCode()
    q.equals(q)
    q.javaClass
    println("handler saw $seen")

    // 3. the class is cached per loader and per ordered interface list
    val again = Proxy.newProxyInstance(app, arrayOf(KFxQuotes::class.java)) { _, _, _ -> 0L }
    val ab = Proxy.newProxyInstance(app, arrayOf(KFxQuotes::class.java, KAudited::class.java), h)
    val ba = Proxy.newProxyInstance(app, arrayOf(KAudited::class.java, KFxQuotes::class.java), h)
    println("same class for the same interface: ${again.javaClass == pc}")
    println("{KFxQuotes, KAudited} -> ${ab.javaClass.name}, {KAudited, KFxQuotes} -> ${ba.javaClass.name}")
}
