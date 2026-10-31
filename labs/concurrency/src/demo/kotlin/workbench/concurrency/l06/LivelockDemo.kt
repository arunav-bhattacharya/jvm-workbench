package workbench.concurrency.l06

import kotlin.concurrent.thread

// Two polite diners share one spoon. Each hands it over while the other is hungry. Try -Pargs=fixed.
@Volatile private var spoonOwner = 0                // diner 0 or diner 1
private val hungry = booleanArrayOf(true, true)     // guarded by synchronized(hungry)
@Volatile private var stop = false
private val handovers = LongArray(2)

fun main(args: Array<String>) {
    val fixed = args.firstOrNull() == "fixed"
    val d0 = thread(name = "diner-0") { dine(0, fixed) }
    val d1 = thread(name = "diner-1") { dine(1, fixed) }
    d0.join(1_000)
    d1.join(1_000)
    stop = true
    d0.join()
    d1.join()
    val meals = (if (hungry[0]) 0 else 1) + (if (hungry[1]) 0 else 1)
    println("spoon handed over %,d times; meals eaten: %d".format(handovers[0] + handovers[1], meals))
}

private fun dine(me: Int, fixed: Boolean) {
    val other = 1 - me
    var politeTurns = 0
    while (!stop) {
        if (spoonOwner != me) {                     // not my spoon: wait for it
            Thread.onSpinWait()
            continue
        }
        val otherHungry = synchronized(hungry) { hungry[other] }
        if (otherHungry && (!fixed || politeTurns < 3)) {
            politeTurns++
            handovers[me]++
            spoonOwner = other                      // "you first": both keep saying it
            continue
        }
        synchronized(hungry) { hungry[me] = false } // eat
        spoonOwner = other                          // then pass the spoon on
        return
    }
}
