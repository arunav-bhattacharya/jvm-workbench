package workbench.concurrency.l10

import java.util.concurrent.Phaser
import kotlin.concurrent.thread

// A stocktake in three phases. Helper 2 only counts, then goes home; the Phaser just has fewer parties.
fun main() {
    val phases = listOf("count", "check", "report")
    val phaser = object : Phaser(1) {                         // 1 party: main, until it deregisters
        override fun onAdvance(phase: Int, parties: Int): Boolean {
            println("  phase %d (%s) done, %d parties".format(phase, phases[phase], parties))
            return phase == phases.lastIndex || parties == 0     // true ends the phaser
        }
    }
    val helpers = List(3) { me ->
        phaser.register()                                     // a new party joins
        thread(name = "helper-$me") {
            for (p in phases.indices) {
                if (me == 2 && p == 1) {
                    phaser.arriveAndDeregister()              // helper 2 only counts, then leaves
                    return@thread
                }
                phaser.arriveAndAwaitAdvance()                // like a barrier, for this phase
            }
        }
    }
    phaser.arriveAndDeregister()                              // main stops taking part
    helpers.forEach { it.join() }
    println("terminated: ${phaser.isTerminated}")
}
