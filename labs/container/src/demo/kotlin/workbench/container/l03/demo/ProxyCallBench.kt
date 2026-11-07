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

interface KFees {
    fun feeMinor(amountMinor: Long): Long
}

open class KPlainFees : KFees {
    override fun feeMinor(amountMinor: Long) = (amountMinor * 29 + 500) / 1000
}

private val chain = listOf(Interceptor { it.proceed() })          // does nothing but carry on

/** The shape RegistryGenerator writes for an intercepted interface. */
class KFeesProxy(private val target: KFees) : KFees {
    override fun feeMinor(amountMinor: Long): Long =
        Invocation("KFees.feeMinor", arrayOf(amountMinor), chain) { target.feeMinor(amountMinor) }.proceed() as Long
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
    val fee = KFees::class.java.getMethod("feeMinor", Long::class.java)
    val jdkProxy = Proxy.newProxyInstance(KFees::class.java.classLoader, arrayOf(KFees::class.java),
        InterceptingHandler(KPlainFees(), mapOf(fee to chain))) as KFees
    val byteBuddy = ByteBuddy().subclass(KPlainFees::class.java)
        .method(named("feeMinor"))
        .intercept(MethodDelegation.withDefaultConfiguration().filter(named("intercept"))
            .to(SubclassBridge(mapOf(KPlainFees::class.java.getMethod("feeMinor", Long::class.java) to chain))))
        .make().load(KPlainFees::class.java.classLoader).loaded
        .getConstructor().newInstance()
    val direct = KPlainFees()
    val generated = KFeesProxy(KPlainFees())
    println("%-10s %8.1f B/call".format("direct", bytesPerCall { direct.feeMinor(it) }))
    println("%-10s %8.1f B/call".format("jdkProxy", bytesPerCall { jdkProxy.feeMinor(it) }))
    println("%-10s %8.1f B/call".format("byteBuddy", bytesPerCall { byteBuddy.feeMinor(it) }))
    println("%-10s %8.1f B/call".format("generated", bytesPerCall { generated.feeMinor(it) }))
    println("(checksum $sink)")
}
