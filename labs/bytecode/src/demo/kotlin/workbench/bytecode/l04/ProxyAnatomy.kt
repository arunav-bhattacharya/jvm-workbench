package workbench.bytecode.l04

import java.lang.reflect.InvocationHandler
import java.lang.reflect.Modifier
import java.lang.reflect.Proxy

interface KWardrobe {
    fun costumes(role: String): Int
    fun dressed(role: String): Boolean = costumes(role) > 0   // a JVM default method (jvmTarget 21)
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
            "costumes" -> 3
            "hashCode" -> 42
            "equals" -> proxy === a[0]
            "toString" -> "KWardrobe proxy"
            else -> null
        }
    }
    val app = KWardrobe::class.java.classLoader
    val q = Proxy.newProxyInstance(app, arrayOf(KWardrobe::class.java), h) as KWardrobe

    // 1. the generated class
    val pc = q.javaClass
    println("class      ${Modifier.toString(pc.modifiers)} ${pc.name}")
    println("extends    ${pc.superclass.name}, implements ${pc.interfaces.toList()}")
    println("module     ${pc.module.name}, hidden: ${pc.isHidden}")
    println("fields     ${pc.declaredFields.map { it.name }.sorted()}")
    println("methods    ${pc.declaredMethods.map { it.name }.sorted()}")

    // 2. which calls reach the handler
    q.costumes("Hamlet")
    q.toString()
    q.hashCode()
    q.equals(q)
    q.javaClass
    println("handler saw $seen")

    // 3. the class is cached per loader and per ordered interface list
    val again = Proxy.newProxyInstance(app, arrayOf(KWardrobe::class.java)) { _, _, _ -> 0 }
    val ab = Proxy.newProxyInstance(app, arrayOf(KWardrobe::class.java, KAudited::class.java), h)
    val ba = Proxy.newProxyInstance(app, arrayOf(KAudited::class.java, KWardrobe::class.java), h)
    println("same class for the same interface: ${again.javaClass == pc}")
    println("{KWardrobe, KAudited} -> ${ab.javaClass.name}, {KAudited, KWardrobe} -> ${ba.javaClass.name}")
}
