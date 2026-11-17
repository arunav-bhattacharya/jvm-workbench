package workbench.kotlin.l04.demo

// Two function types. Inside the first, the StringBuilder is `this`; in the second it's a parameter.
val withReceiver: StringBuilder.() -> Unit = { append("copies: "); append(250) }
val withParameter: (StringBuilder) -> Unit = { sb -> sb.append("copies: ").append(250) }

/** An ordinary function that takes a lambda with receiver: the smallest possible DSL entry point. */
fun ticket(block: StringBuilder.() -> Unit): String = StringBuilder().apply(block).toString()

fun main() {
    val sb = StringBuilder()
    sb.withReceiver()                     // call it like an extension function...
    withReceiver(sb)                      // ...or pass the receiver as the first argument
    println(sb)

    val swapped: StringBuilder.() -> Unit = withParameter    // the two types are interchangeable
    println(ticket(swapped))
    println(ticket { append("flyer.pdf x "); append(250) })

    println("JVM type of withReceiver: ${withReceiver.javaClass.interfaces.joinToString { it.name }}")
}
