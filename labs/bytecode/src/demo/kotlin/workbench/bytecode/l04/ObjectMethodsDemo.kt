package workbench.bytecode.l04

import java.io.IOException
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Proxy
import java.lang.reflect.UndeclaredThrowableException

interface KIssuerClient {
    @Throws(IOException::class)
    fun authorize(pan: String): String   // @Throws writes `throws IOException` into the class file
    fun status(): String                 // Kotlin declares nothing unless you say so
}

class RealKIssuer : KIssuerClient {
    override fun authorize(pan: String): String = throw IOException("issuer timed out after 120 ms")
    override fun status() = "UP"
}

fun forwardingEverything(target: KIssuerClient): KIssuerClient =
    Proxy.newProxyInstance(KIssuerClient::class.java.classLoader, arrayOf(KIssuerClient::class.java)) { _, m, args ->
        try {
            m.invoke(target, *(args ?: emptyArray()))   // equals and hashCode go to the target too
        } catch (e: InvocationTargetException) {
            throw e.cause!!
        }
    } as KIssuerClient

/** Two handler bugs: forwarding equals to the target, and throwing a checked exception the method doesn't declare. */
fun main() {
    val p = forwardingEverything(RealKIssuer())
    println("p.equals(p): ${p.equals(p)}   (target.equals(p) was asked)")
    val listeners = ArrayList<KIssuerClient>()
    listeners += p
    println("listeners.remove(p) after listeners.add(p): ${listeners.remove(p)}, size still ${listeners.size}")
    val set = HashSet(listeners)
    println("HashSet.contains(p): ${p in set}   (HashMap checks == before equals)")

    try {
        p.authorize("4111111111111111")
    } catch (e: IOException) {
        println("declared IOException passes through: ${e.message}")
    }

    val angry = Proxy.newProxyInstance(KIssuerClient::class.java.classLoader, arrayOf(KIssuerClient::class.java)) { _, _, _ ->
        throw IOException("connection reset")
    } as KIssuerClient
    try {
        angry.status()
    } catch (e: UndeclaredThrowableException) {
        println("undeclared IOException from status() -> UndeclaredThrowableException, cause: ${e.cause}")
    }
}
