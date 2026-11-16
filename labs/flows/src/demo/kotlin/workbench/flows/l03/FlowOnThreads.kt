package workbench.flows.l03

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking
import java.util.concurrent.Executors

fun log(stage: String, v: Any?) = println("  %-8s %-3s thread=%s".format(stage, v, Thread.currentThread().name))

fun main() {
    // debug mode adds " @coroutine#N" to thread names, so you can count the coroutines
    System.setProperty("kotlinx.coroutines.debug", "on")
    val io = Executors.newSingleThreadExecutor { r -> Thread(r, "io-thread") }.asCoroutineDispatcher()
    val cpu = Executors.newSingleThreadExecutor { r -> Thread(r, "cpu-thread") }.asCoroutineDispatcher()

    runBlocking {
        println("=== two flowOn calls: two walls, three rooms")
        flow { for (i in 1..2) { log("emit", i); emit(i) } }
            .map { log("map1", it); it }
            .flowOn(io)
            .map { log("map2", it); it }
            .flowOn(cpu)
            .collect { log("collect", it) }

        println("=== flowOn(CoroutineName): same dispatcher, so no wall")
        flow { for (i in 1..2) { log("emit", i); emit(i) } }
            .flowOn(CoroutineName("renamed"))
            .collect { log("collect", it) }
    }

    println("=== adjacent flowOn calls fuse; toString() is a peek under the hood, not an API")
    val fused = flowOf(1, 2, 3).flowOn(Dispatchers.IO).flowOn(Dispatchers.Default)
    println("  " + fused.toString().substringAfter(" -> "))

    println("=== a Job in flowOn is refused when the operator is built")
    try {
        flowOf(1).flowOn(Job())
    } catch (e: IllegalArgumentException) {
        println("  " + e.message!!.substringBefore("Had"))
    }
    io.close(); cpu.close()
}
