package workbench.coroutines.tmpcheck

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

class Tracker {
    val status: StateFlow<String>
        field = MutableStateFlow("PENDING")

    fun move(to: String) { status.value = to }
}

fun main() = runBlocking {
    val t = Tracker()
    t.move("AUTHORIZED")
    println("explicit backing field works: ${t.status.value}; runtime class ${t.status::class.simpleName}; getter returns ${Tracker::class.java.getMethod("getStatus").returnType.simpleName}")
    val shared = MutableSharedFlow<Int>()
    println("tryEmit with no subscribers: ${shared.tryEmit(1)}")
    val job = launch(start = CoroutineStart.UNDISPATCHED) { shared.collect { delay(100); println("got $it") } }
    println("tryEmit with an idle subscriber: ${shared.tryEmit(2)}")
    val buffered = MutableSharedFlow<Int>(extraBufferCapacity = 2)
    val job2 = launch(start = CoroutineStart.UNDISPATCHED) { buffered.collect { delay(100); println("buffered got $it") } }
    println("buffered tryEmit: ${(1..4).map { buffered.tryEmit(it) }}")
    delay(600); job.cancel(); job2.cancel()
    val dropping = MutableSharedFlow<Int>(extraBufferCapacity = 2, onBufferOverflow = kotlinx.coroutines.channels.BufferOverflow.DROP_OLDEST)
    val job3 = launch(start = CoroutineStart.UNDISPATCHED) { dropping.collect { delay(100); println("dropping got $it") } }
    println("drop-oldest tryEmit: ${(1..5).map { dropping.tryEmit(it) }}")
    delay(600); job3.cancel()
    val sf = MutableStateFlow(0)
    val job4 = launch(start = CoroutineStart.UNDISPATCHED) { sf.collect { println("state got $it"); delay(100) } }
    sf.value = 1; sf.value = 2; sf.value = 3; delay(150); sf.value = 3; delay(150); job4.cancel()
}
