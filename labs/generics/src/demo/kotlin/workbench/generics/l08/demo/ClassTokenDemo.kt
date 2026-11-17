package workbench.generics.l08.demo

/** The shop's standard item of each kind: ask for "an apple" without saying which, and you get a Gala. */
private val defaults: Map<Class<*>, Any> = mapOf(
    Apple::class.java to Apple("Gala", 180),
    Lemon::class.java to Lemon("Eureka", 120),
    String::class.java to "",
)

/** The core takes a Class token, so it works for Java callers too. */
fun <T : Any> defaultOf(type: Class<T>): T =
    type.cast(defaults[type] ?: throw IllegalArgumentException("no default for ${type.simpleName}"))

/** The Kotlin wrapper: the compiler writes T::class.java into each call site. */
inline fun <reified T : Any> defaultOf(): T = defaultOf(T::class.java)

fun main() {
    val apple: Apple = defaultOf()                             // T inferred from the expected type
    val lemon = defaultOf<Lemon>()
    val blank = defaultOf(String::class.java)                  // the Java-style call, from Kotlin
    println("apple = $apple, lemon = $lemon, blank = '$blank'")

    // A trap with primitives: Int::class.java is the primitive int, but a reified Int is boxed.
    println("Int::class.java = ${Int::class.java}, javaObjectType = ${Int::class.javaObjectType}")
}
