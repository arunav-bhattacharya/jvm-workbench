package workbench.functional.l04.demo

// Payment, Status and sampleDay are in SampleDay.kt, next to this file.
fun main() {
    println("map:         ${sampleDay.map { it.amountCents }}")
    println("filter:      ${sampleDay.filter { it.status == Status.SETTLED }.map { it.id }}")
    println("mapNotNull:  ${sampleDay.mapNotNull { it.refundCents }}")

    val batches = listOf(sampleDay.take(3), sampleDay.drop(3))      // two acquirer files
    println("flatMap:     ${batches.flatMap { batch -> batch.map { it.id } }}")

    println("sumOf:       ${sampleDay.sumOf { it.amountCents }}")
    println("count:       ${sampleDay.count { it.status == Status.SETTLED }}")
    println("any / all:   ${sampleDay.any { it.amountCents > 10_000 }} / ${sampleDay.all { it.amountCents > 0 }}")

    val (settled, rest) = sampleDay.partition { it.status == Status.SETTLED }
    println("partition:   ${settled.map { it.id }} / ${rest.map { it.id }}")

    println("map returns: ${sampleDay.map { it.id }.javaClass.name}")
}
