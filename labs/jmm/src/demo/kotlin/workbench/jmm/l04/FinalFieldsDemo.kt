package workbench.jmm.l04

/** Where final fields come from in Kotlin. Run javap on the compiled classes to see them. */
class KQuote(val scheme: String, val feeCents: Long)          // val: a private final backing field
class KMutableQuote(var scheme: String, var feeCents: Long)   // var: a private, non-final backing field

fun main() {
    val q = KQuote("VISA", 120)
    val m = KMutableQuote("MC", 135)
    m.feeCents = 140
    println("${q.scheme} ${q.feeCents} and a mutable quote for ${m.scheme} ${m.feeCents}")
}
