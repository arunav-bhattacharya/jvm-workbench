package workbench.modernjava.l01.demo

// List<String> is a read-only view in Kotlin, not an immutable list: the caller may still hold a MutableList
data class Crate(val branch: String, val titles: List<String>)

// Kotlin can't reassign a constructor parameter, so the defensive copy goes in a factory
data class SafeCrate(val branch: String, val titles: List<String>) {
    companion object {
        fun of(branch: String, titles: List<String>) = SafeCrate(branch, java.util.List.copyOf(titles))
    }
}

data class Rating(val stars: Double)

/** Equality, hashCode and toString are only as deep as the properties. */
fun main() {
    val titles = mutableListOf("Dune", "Emma")
    val crate = Crate("NORTH", titles)
    val sent = hashSetOf(crate)
    val before = crate.hashCode()

    titles += "Ulysses"                                         // someone reuses their list

    println("crate now:          $crate")
    println("hashCode changed:   ${before != crate.hashCode()}")
    println("sent.contains:      ${crate in sent}")

    val copy = crate.copy(branch = "SOUTH")                     // copy() is shallow too
    titles += "Persuasion"
    println("copy shares list:   $copy")

    val titles2 = mutableListOf("Dune", "Emma")
    val safe = SafeCrate.of("SOUTH", titles2)
    titles2 += "Ulysses"
    println("safe crate:         $safe")

    println("NaN data class ==:  ${Rating(Double.NaN) == Rating(Double.NaN)}  (but NaN == NaN is ${Double.NaN == Double.NaN})")
    println("0.0 vs -0.0 ==:     ${Rating(0.0) == Rating(-0.0)} (but 0.0 == -0.0 is ${0.0 == -0.0})")
}
