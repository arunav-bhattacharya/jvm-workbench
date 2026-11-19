package workbench.ksp.app.l09

import java.lang.management.ManagementFactory

// Generated cards (lesson 7's MovingDayList.cardFor, written by KSP in this build) against reflection.
// The first call of each way, in this order, then many calls. Run it twice, the second time with the order
// swapped, and see which cost moves with the order:
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l09.CardTimingKt
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l09.CardTimingKt -Pargs=reflection-first
fun main(args: Array<String>) {
    val ways: Map<String, (Any) -> String> = linkedMapOf(
        "generated" to MovingDayList::cardFor,
        "reflection" to ::reflectionCard,
        "cached" to CachedReflectionCards::card,
    )
    val things = movingDayThings()
    val lamp = things[1]

    // 1. the first call of each way: time, and the classes the JVM loaded for it
    val order = if (args.firstOrNull() == "reflection-first") listOf("reflection", "generated") else listOf("generated", "reflection")
    val classes = ManagementFactory.getClassLoadingMXBean()
    for (name in order) {
        val loadedBefore = classes.totalLoadedClassCount
        val start = System.nanoTime()
        val card = ways.getValue(name)(lamp)
        val ms = (System.nanoTime() - start) / 1e6
        println("first call, %-10s %6.2f ms, %3d classes loaded -> %s".format(name + ":", ms, classes.totalLoadedClassCount - loadedBefore, card))
    }

    // 2. correctness before speed: every way writes the same four cards
    val agree = things.all { thing -> ways.values.map { it(thing) }.distinct().size == 1 }
    println("all three ways agree on all ${things.size} cards: $agree")

    // 3. many calls, after a warm-up: nanoseconds per card, three rounds each
    val calls = 1_000_000
    for ((name, f) in ways) {
        repeat(200_000) { f(things[it % 4]) }
        val rounds = (1..3).map {
            var length = 0L
            val t0 = System.nanoTime()
            for (i in 0 until calls) length += f(things[i % 4]).length
            check(length > 0)
            (System.nanoTime() - t0).toDouble() / calls
        }
        println("%-12s %s ns per card".format(name, rounds.joinToString(" / ") { "%.0f".format(it) }))
    }
}
