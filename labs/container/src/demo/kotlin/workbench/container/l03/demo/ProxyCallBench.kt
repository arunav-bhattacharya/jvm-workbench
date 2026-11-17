package workbench.container.l03.demo

// ProxyCallBench.java times these calls with JMH, which needs Java classes in this lab. This twin
// makes the same four calls from Kotlin and counts the bytes each one allocates with the JVM's
// per-thread allocation counter, after a warm-up so the JIT has compiled them.
import net.bytebuddy.ByteBuddy
import net.bytebuddy.implementation.MethodDelegation
import net.bytebuddy.matcher.ElementMatchers.named
import workbench.container.l03.InterceptingHandler
import workbench.container.l03.Interceptor
import workbench.container.l03.Invocation
import workbench.container.l03.SubclassBridge
import java.lang.management.ManagementFactory
import java.lang.reflect.Proxy

interface KPrices {
    fun feeCents(priceCents: Long): Long
}

open class KPlainPrices : KPrices {
    override fun feeCents(priceCents: Long) = (priceCents * 29 + 500) / 1000
}

private val chain = listOf(Interceptor { it.proceed() })          // does nothing but carry on

/** The shape RegistryGenerator writes for an intercepted interface. */
class KPricesProxy(private val target: KPrices) : KPrices {
    override fun feeCents(priceCents: Long): Long =
        Invocation("KPrices.feeCents", arrayOf(priceCents), chain) { target.feeCents(priceCents) }.proceed() as Long
}

private val threads = ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean
private var sink = 0L                                              // results go somewhere the JIT can't ignore

// inline: every use gets its own call site, which sees one class, as each JMH benchmark does
private inline fun bytesPerCall(call: (Long) -> Long): Double {
    repeat(200_000) { sink += call(12_000L + it % 3) }             // warm up: let C2 compile the path
    val before = threads.currentThreadAllocatedBytes
    repeat(100_000) { sink += call(12_000L + it % 3) }
    return (threads.currentThreadAllocatedBytes - before).toDouble() / 100_000
}

fun main() {
    val fee = KPrices::class.java.getMethod("feeCents", Long::class.java)
    val jdkProxy = Proxy.newProxyInstance(KPrices::class.java.classLoader, arrayOf(KPrices::class.java),
        InterceptingHandler(KPlainPrices(), mapOf(fee to chain))) as KPrices
    val byteBuddy = ByteBuddy().subclass(KPlainPrices::class.java)
        .method(named("feeCents"))
        .intercept(MethodDelegation.withDefaultConfiguration().filter(named("intercept"))
            .to(SubclassBridge(mapOf(KPlainPrices::class.java.getMethod("feeCents", Long::class.java) to chain))))
        .make().load(KPlainPrices::class.java.classLoader).loaded
        .getConstructor().newInstance()
    val direct = KPlainPrices()
    val generated = KPricesProxy(KPlainPrices())
    println("%-10s %8.1f B/call".format("direct", bytesPerCall { direct.feeCents(it) }))
    println("%-10s %8.1f B/call".format("jdkProxy", bytesPerCall { jdkProxy.feeCents(it) }))
    println("%-10s %8.1f B/call".format("byteBuddy", bytesPerCall { byteBuddy.feeCents(it) }))
    println("%-10s %8.1f B/call".format("generated", bytesPerCall { generated.feeCents(it) }))
    println("(checksum $sink)")
}
