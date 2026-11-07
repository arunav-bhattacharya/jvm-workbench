package workbench.bytecode.l03

import java.lang.invoke.LambdaMetafactory
import java.lang.invoke.MethodHandles
import java.lang.invoke.MethodType.methodType
import java.lang.invoke.StringConcatFactory
import java.util.function.Supplier

object Banners {
    @JvmStatic fun banner() = "settlement batch 42"
}

// The two bootstrap calls an invokedynamic would make, made by hand from Kotlin.
fun main() {
    val lookup = MethodHandles.lookup()

    // 1. () -> banner() as a Supplier<String>
    val site = LambdaMetafactory.metafactory(
        lookup,
        "get",                                                   // the interface method's name
        methodType(Supplier::class.java),                        // factory type: captures nothing
        methodType(Any::class.java),                             // Supplier.get() after erasure
        lookup.findStatic(Banners::class.java, "banner", methodType(String::class.java)),
        methodType(String::class.java),                          // get() as this lambda returns it
    )
    @Suppress("UNCHECKED_CAST")
    val s = site.target.invoke() as Supplier<String>
    println("${s.get()}  <- ${s.javaClass.name}, call site: ${site.javaClass.simpleName}")

    // 2. "batch " + id + " has " + count + " payments"
    val concat = StringConcatFactory.makeConcatWithConstants(
        lookup, "concat", methodType(String::class.java, Int::class.javaPrimitiveType, Long::class.javaPrimitiveType),
        "batch \u0001 has \u0001 payments",
    )
    println("${concat.target.invoke(42, 1_250L)}  <- call site: ${concat.javaClass.simpleName}")
}
