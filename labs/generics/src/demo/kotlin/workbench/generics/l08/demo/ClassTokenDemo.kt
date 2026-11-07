package workbench.generics.l08.demo

import java.math.BigDecimal

private val defaults: Map<Class<*>, Any> = mapOf(
    String::class.java to "",
    BigDecimal::class.java to BigDecimal.ZERO,
    java.util.Currency::class.java to java.util.Currency.getInstance("EUR"),
)

/** The core takes a Class token, so it works for Java callers too. */
fun <T : Any> defaultOf(type: Class<T>): T =
    type.cast(defaults[type] ?: throw IllegalArgumentException("no default for ${type.simpleName}"))

/** The Kotlin wrapper: the compiler writes T::class.java into each call site. */
inline fun <reified T : Any> defaultOf(): T = defaultOf(T::class.java)

fun main() {
    val zero: BigDecimal = defaultOf()                         // T inferred from the expected type
    val eur = defaultOf<java.util.Currency>()
    val blank = defaultOf(String::class.java)                  // the Java-style call, from Kotlin
    println("zero = $zero, eur = $eur, blank = '$blank'")

    // A trap with primitives: Int::class.java is the primitive int, but a reified Int is boxed.
    println("Int::class.java = ${Int::class.java}, javaObjectType = ${Int::class.javaObjectType}")
}
