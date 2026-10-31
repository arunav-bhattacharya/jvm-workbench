package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asContextElement
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlin.coroutines.ContinuationInterceptor

private val requestId = ThreadLocal<String?>()

fun main() = runBlocking {
    // 1. a context is a set of elements; + combines them, and the right side wins for the same key
    val ctx = Dispatchers.IO + CoroutineName("capture")
    val renamed = ctx + CoroutineName("refund")
    println("ctx[CoroutineName]     = ${ctx[CoroutineName]}")
    println("renamed[CoroutineName] = ${renamed[CoroutineName]}")
    println("dispatcher by its key  = ${renamed[ContinuationInterceptor]}")

    // 2. a ThreadLocal does not follow a coroutine to another thread
    requestId.set("req-42")
    println("main thread sees              ${requestId.get()}")
    withContext(Dispatchers.Default) { println("on Default, plain ThreadLocal  ${requestId.get()}") }

    // 3. asContextElement copies the value in and out whenever the coroutine runs on a thread
    withContext(Dispatchers.Default + requestId.asContextElement()) {
        println("on Default, asContextElement  ${requestId.get()}")
    }
}
