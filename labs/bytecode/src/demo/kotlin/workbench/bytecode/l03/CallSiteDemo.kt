package workbench.bytecode.l03

import java.lang.invoke.ConstantCallSite
import java.lang.invoke.MethodHandles
import java.lang.invoke.MethodType
import java.lang.invoke.MutableCallSite

// A call site is a slot holding a target method handle. invokedynamic calls through one.
object Formats {
    @JvmStatic fun eur(minor: Long) = "%d.%02d EUR".format(minor / 100, minor % 100)
    @JvmStatic fun usd(minor: Long) = "$%d.%02d".format(minor / 100, minor % 100)
}

fun main() {
    val lookup = MethodHandles.lookup()
    val type = MethodType.methodType(String::class.java, Long::class.javaPrimitiveType)
    val eur = lookup.findStatic(Formats::class.java, "eur", type)
    val usd = lookup.findStatic(Formats::class.java, "usd", type)

    val site = MutableCallSite(eur)
    val invoker = site.dynamicInvoker()             // what an invokedynamic instruction would call through
    println("linked to eur: " + invoker.invoke(362_550L) as String)
    site.target = usd                               // relink: same invoker, new target
    println("relinked to usd: " + invoker.invoke(362_550L) as String)

    val fixed = ConstantCallSite(eur)               // what lambdas and string concatenation get
    try {
        fixed.target = usd
    } catch (e: UnsupportedOperationException) {
        println("ConstantCallSite.setTarget -> UnsupportedOperationException: linked for good")
    }
}
