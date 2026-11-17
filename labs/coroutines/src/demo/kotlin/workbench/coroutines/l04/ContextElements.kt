package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asContextElement
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlin.coroutines.ContinuationInterceptor

private val guest = ThreadLocal<String?>()   // a note on the cook's apron, not on the dish

fun main() = runBlocking {
    // 1. a context is a set of elements; + combines them, and the right side wins for the same key
    val ctx = Dispatchers.IO + CoroutineName("soup")
    val renamed = ctx + CoroutineName("salad")
    println("ctx[CoroutineName]     = ${ctx[CoroutineName]}")
    println("renamed[CoroutineName] = ${renamed[CoroutineName]}")
    println("dispatcher by its key  = ${renamed[ContinuationInterceptor]}")

    // 2. a ThreadLocal does not follow a coroutine to another thread
    guest.set("ana")
    println("main thread sees              ${guest.get()}")
    withContext(Dispatchers.Default) { println("on Default, plain ThreadLocal  ${guest.get()}") }

    // 3. asContextElement copies the value in and out whenever the coroutine runs on a thread
    withContext(Dispatchers.Default + guest.asContextElement()) {
        println("on Default, asContextElement  ${guest.get()}")
    }
}
