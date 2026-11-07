package workbench.executors.l08

import java.util.TreeSet
import java.util.concurrent.ConcurrentHashMap

/** Collecting from a parallel stream into shared state, and the stream's own way. */
fun main() {
    val ids: List<Int> = (0 until 100_000).toList()
    val threads = ConcurrentHashMap.newKeySet<String>()

    val shared = ArrayList<Int>()
    try {
        ids.parallelStream().forEach { id ->
            threads.add(Thread.currentThread().name)
            shared.add(id)                                        // many threads, one ArrayList
        }
        println("shared ArrayList:   %,d of %,d ids, in order: %b".format(shared.size, ids.size, shared == ids))
    } catch (e: ArrayIndexOutOfBoundsException) {
        println("shared ArrayList:   threw $e")
    }
    val collected = ids.parallelStream().map { it }.toList()
    println("toList():           %,d of %,d ids, in order: %b".format(collected.size, ids.size, collected == ids))

    val total = LongArray(1)
    ids.parallelStream().forEach { id -> total[0] += id }     // read, add, write from many threads
    val sum = ids.parallelStream().mapToLong { it.toLong() }.sum()
    println("shared long[] sum:  %,d".format(total[0]))
    println("mapToLong().sum():  %,d".format(sum))

    println("threads that ran the first stream: ${TreeSet(threads)}")
}
