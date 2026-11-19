package workbench.ksp.l01.demo

import workbench.ksp.l01.Lamp
import workbench.ksp.l01.inventoryCard
import workbench.ksp.l01.reflectionCard

// The hand-written card against the reflection card: the same text, then what each costs. It uses your
// reflectionCard with -Pmine=l01, the reference one otherwise.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l01.demo.ReflectionCostDemoKt
// The timings are for teaching, from a single run: expect different numbers on your machine.

fun main() {
    val lamp = Lamp("desk lamp", 1, null)
    "warm up string building: ${lamp.name}".length // so neither first call pays for it

    // correctness first: the same card both ways
    var start = System.nanoTime()
    val byHand = lamp.inventoryCard()
    val firstByHand = System.nanoTime() - start
    start = System.nanoTime()
    val byReflection = reflectionCard(lamp)
    val firstByReflection = System.nanoTime() - start
    println("hand-written: $byHand")
    println("reflection:   $byReflection")
    println("the same card: ${byHand == byReflection}")

    // then the cost: the very first call, and the average over many calls once the JVM has warmed up
    println("first call:     hand-written %,9d ns   reflection %,9d ns".format(firstByHand, firstByReflection))
    val calls = 2_000_000
    repeat(3) { round ->
        val hand = timePerCall(calls) { lamp.inventoryCard() }
        val reflection = timePerCall(calls) { reflectionCard(lamp) }
        println("round ${round + 1} per call: hand-written %,9.0f ns   reflection %,9.0f ns".format(hand, reflection))
    }
}

/** Average nanoseconds per call of [card] over [calls] calls (the lengths are summed so the JIT keeps the work). */
private fun timePerCall(calls: Int, card: () -> String): Double {
    var sink = 0L
    val start = System.nanoTime()
    repeat(calls) { sink += card().length }
    val elapsed = System.nanoTime() - start
    if (sink == 42L) println("unlikely") // uses sink
    return elapsed.toDouble() / calls
}
