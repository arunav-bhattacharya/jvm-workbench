package workbench.bytecode.l04

import java.io.IOException
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Proxy
import java.lang.reflect.UndeclaredThrowableException

interface KPropStore {
    @Throws(IOException::class)
    fun fetch(prop: String): String      // @Throws writes `throws IOException` into the class file
    fun status(): String                 // Kotlin declares nothing unless you say so
}

class RealKPropStore : KPropStore {
    override fun fetch(prop: String): String = throw IOException("prop store took longer than 120 ms")
    override fun status() = "OPEN"
}

fun forwardingEverything(target: KPropStore): KPropStore =
    Proxy.newProxyInstance(KPropStore::class.java.classLoader, arrayOf(KPropStore::class.java)) { _, m, args ->
        try {
            m.invoke(target, *(args ?: emptyArray()))   // equals and hashCode go to the target too
        } catch (e: InvocationTargetException) {
            throw e.cause!!
        }
    } as KPropStore

/** Two handler bugs: forwarding equals to the target, and throwing a checked exception the method doesn't declare. */
fun main() {
    val p = forwardingEverything(RealKPropStore())
    println("p.equals(p): ${p.equals(p)}   (target.equals(p) was asked)")
    val listeners = ArrayList<KPropStore>()
    listeners += p
    println("listeners.remove(p) after listeners.add(p): ${listeners.remove(p)}, size still ${listeners.size}")
    val set = HashSet(listeners)
    println("HashSet.contains(p): ${p in set}   (HashMap checks == before equals)")

    try {
        p.fetch("crown")
    } catch (e: IOException) {
        println("declared IOException passes through: ${e.message}")
    }

    val angry = Proxy.newProxyInstance(KPropStore::class.java.classLoader, arrayOf(KPropStore::class.java)) { _, _, _ ->
        throw IOException("connection reset")
    } as KPropStore
    try {
        angry.status()
    } catch (e: UndeclaredThrowableException) {
        println("undeclared IOException from status() -> UndeclaredThrowableException, cause: ${e.cause}")
    }
}
