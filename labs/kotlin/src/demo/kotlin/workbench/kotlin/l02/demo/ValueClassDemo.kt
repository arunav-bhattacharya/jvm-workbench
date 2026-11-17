package workbench.kotlin.l02.demo

/** A value class: a Grams in your code, a long in the bytecode. */
@JvmInline
value class Grams(val value: Long) {
    init {
        require(value >= 0) { "negative weight: $value" }
    }

    operator fun plus(other: Grams): Grams = Grams(value + other.value)

    override fun toString(): String = "$value g"
}

/** A type alias is only a second name. Any Long is accepted where a GramsAlias is expected. */
typealias GramsAlias = Long

fun ship(weight: Grams): String = "shipped $weight"

@JvmName("shipFromJava")
fun shipJava(weight: Grams): String = "shipped $weight"

fun shipAlias(weight: GramsAlias): String = "shipped $weight g (alias)"

fun main() {
    val parcel = Grams(150) + Grams(49)
    println(ship(parcel))
    val sheets: Long = 500
    println(shipAlias(sheets))         // compiles: a sheet count is a Long, so it is a GramsAlias too
    try {
        Grams(-1)
    } catch (e: IllegalArgumentException) {
        println("rejected: ${e.message}")
    }

    // Wrong move. Uncomment, predict the error, then run.
    // println(ship(sheets))
}
