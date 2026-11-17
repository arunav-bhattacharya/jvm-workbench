package workbench.functional.l04.demo

// Cookie, Status and sampleDay are in SampleDay.kt, next to this file.
fun main() {
    println("map:         ${sampleDay.map { it.grams }}")
    println("filter:      ${sampleDay.filter { it.status == Status.GOLDEN }.map { it.id }}")
    println("mapNotNull:  ${sampleDay.mapNotNull { it.nibbledGrams }}")

    val trays = listOf(sampleDay.take(3), sampleDay.drop(3))        // two trays out of the oven
    println("flatMap:     ${trays.flatMap { tray -> tray.map { it.id } }}")

    println("sumOf:       ${sampleDay.sumOf { it.grams }}")
    println("count:       ${sampleDay.count { it.status == Status.GOLDEN }}")
    println("any / all:   ${sampleDay.any { it.grams > 75 }} / ${sampleDay.all { it.grams > 0 }}")

    val (golden, rest) = sampleDay.partition { it.status == Status.GOLDEN }
    println("partition:   ${golden.map { it.id }} / ${rest.map { it.id }}")

    println("map returns: ${sampleDay.map { it.id }.javaClass.name}")
}
