package workbench.bytecode.l03

import java.lang.invoke.ConstantCallSite
import java.lang.invoke.MethodHandles
import java.lang.invoke.MethodType
import java.lang.invoke.MutableCallSite

// A call site is a slot holding a target method handle. invokedynamic calls through one.
object Formats {
    @JvmStatic fun inSeconds(s: Long) = "$s seconds"
    @JvmStatic fun inMinutes(s: Long) = "${s / 60} minutes"
}

fun main() {
    val lookup = MethodHandles.lookup()
    val type = MethodType.methodType(String::class.java, Long::class.javaPrimitiveType)
    val inSeconds = lookup.findStatic(Formats::class.java, "inSeconds", type)
    val inMinutes = lookup.findStatic(Formats::class.java, "inMinutes", type)

    val site = MutableCallSite(inSeconds)
    val invoker = site.dynamicInvoker()             // what an invokedynamic instruction would call through
    println("linked to inSeconds: " + invoker.invoke(120L) as String)
    site.target = inMinutes                         // relink: same invoker, new target
    println("relinked to inMinutes: " + invoker.invoke(120L) as String)

    val fixed = ConstantCallSite(inSeconds)         // what lambdas and string concatenation get
    try {
        fixed.target = inMinutes
    } catch (e: UnsupportedOperationException) {
        println("ConstantCallSite.setTarget -> UnsupportedOperationException: linked for good")
    }
}
