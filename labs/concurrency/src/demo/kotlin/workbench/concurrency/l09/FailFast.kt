package workbench.concurrency.l09

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArrayList

// ConcurrentModificationException needs no second thread. And concurrent collections never throw it.
fun main() {
    // 1. one thread, an ArrayList, a remove inside a for loop
    var pending = mutableListOf("pay-1", "pay-2", "pay-3", "pay-4")
    try {
        for (p in pending) {
            if (p == "pay-2") pending.remove(p)              // changes the list under its own iterator
        }
    } catch (e: RuntimeException) {
        println("ArrayList, one thread:      ${e.javaClass.simpleName}")
    }

    // 2. the same with a ConcurrentHashMap: weakly consistent, never throws
    val open = ConcurrentHashMap(mapOf("pay-1" to 1, "pay-2" to 2, "pay-3" to 3, "pay-4" to 4))
    for (k in open.keys) {
        if (k == "pay-2") open.remove(k)
        if (k == "pay-3") open["pay-5"] = 5                  // may or may not show up in this loop
    }
    println("ConcurrentHashMap:          no exception, now ${open.size} keys")

    // 3. CopyOnWriteArrayList: the loop walks a snapshot taken when it started
    val hooks = CopyOnWriteArrayList(listOf("a", "b", "c"))
    var seen = 0
    for (h in hooks) {
        hooks.add("$h+")                                     // goes into a NEW array
        seen++
    }
    println("CopyOnWriteArrayList:       loop saw $seen items, list now has ${hooks.size}")

    // 4. the single-thread fix for case 1: remove through the iterator, or removeIf
    pending = mutableListOf("pay-1", "pay-2", "pay-3", "pay-4")
    pending.removeIf { it == "pay-2" }
    println("ArrayList.removeIf:         $pending")
}
