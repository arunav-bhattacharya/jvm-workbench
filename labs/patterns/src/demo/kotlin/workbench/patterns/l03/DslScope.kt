package workbench.patterns.l03

// A tiny delivery-round DSL. @DslMarker stops an inner block from reaching the outer builder by accident.

@DslMarker
annotation class RoundDsl

data class Stop(val orderId: String, val parcels: Int)
data class Round(val driver: String, val stops: List<Stop>)

@RoundDsl
class StopsBuilder {
    private val stops = mutableListOf<Stop>()
    fun stop(orderId: String, parcels: Int) { stops += Stop(orderId, parcels) }
    fun build() = stops.toList()
}

@RoundDsl
class RoundBuilder {
    var driver: String = "unassigned"
    private var stops: List<Stop> = emptyList()
    fun stops(block: StopsBuilder.() -> Unit) { stops = StopsBuilder().apply(block).build() }
    fun build() = Round(driver, stops)
}

fun round(block: RoundBuilder.() -> Unit): Round = RoundBuilder().apply(block).build()

fun main() {
    val r = round {
        driver = "Sam"
        stops {
            stop("o-101", 2)
            stop("o-102", 3)
            // driver = "oops"     // step 2 of the Try it: uncomment this line
        }
    }
    println(r)
    println("parcels on the van: ${r.stops.sumOf { it.parcels }}")
}
