package workbench.flows.l08

import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.asFlow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.conflate
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.reactive.asFlow
import kotlinx.coroutines.reactor.ReactorContext
import kotlinx.coroutines.reactor.asFlux
import kotlinx.coroutines.runBlocking
import org.reactivestreams.Subscription
import reactor.core.publisher.BaseSubscriber
import reactor.core.publisher.Flux
import reactor.util.context.Context

// Faces for Java callers (the Java twin uses them): Java can't collect a Flow, so it gets a Flux.
object LedgerFaces {
    @JvmStatic fun entries(): Flux<Int> = (1..600).asFlow().asFlux()

    @JvmStatic fun entriesTracked(returned: MutableList<Int>): Flux<Int> =
        flow { for (i in 1..10) { emit(i); returned += i } }.asFlux()
}

// Flux -> Flow: log every request(n) that the Flow side sends up to a 300-item Flux.
private fun demand(label: String, collect: suspend (Flux<Int>) -> Unit) = runBlocking {
    val requests = mutableListOf<String>()
    var delivered = 0
    val flux = Flux.range(1, 300)
        .doOnRequest { n -> requests += (if (n == Long.MAX_VALUE) "MAX" else "$n") + " after $delivered" }
        .doOnNext { delivered++ }
        .doOnCancel { requests += "cancel after $delivered" }
    collect(flux)
    val shown = if (requests.size > 6) requests.take(3) + "..." + requests.takeLast(1) + "(${requests.size} in all)" else requests
    println("  %-28s %s".format(label, shown))
}

fun main() {
    println("== 1. Flux -> Flow: the collector's demand becomes request(n)")
    demand("asFlow()") { it.asFlow().collect { } }
    demand("asFlow().buffer(10)") { it.asFlow().buffer(10).collect { } }
    demand("asFlow().buffer(0)") { it.asFlow().buffer(0).take(3).collect { } }
    demand("asFlow().conflate()") { it.asFlow().conflate().collect { } }
    demand("asFlow().buffer(UNLIMITED)") { it.asFlow().buffer(Channel.UNLIMITED).collect { } }
    demand("asFlow().take(3)") { it.asFlow().take(3).collect { } }

    println("== 2. Flow -> Flux: the flow suspends inside emit when the demand runs out")
    val returned = mutableListOf<Int>()
    val received = mutableListOf<Int>()
    lateinit var subscription: Subscription
    LedgerFaces.entriesTracked(returned).subscribe(object : BaseSubscriber<Int>() {
        override fun hookOnSubscribe(s: Subscription) { subscription = s; s.request(2) }
        override fun hookOnNext(v: Int) { received += v }
    })
    println("  after request(2): received=$received, emit() returned for $returned")
    subscription.request(3)
    println("  after request(3): received=$received, emit() returned for $returned")
    subscription.cancel()

    println("== 3. threads: asFlux() runs the flow on Dispatchers.Unconfined")
    val threads: Flow<String> = flow {
        emit("before delay: " + Thread.currentThread().name)
        delay(10)
        emit("after delay: " + Thread.currentThread().name)
    }
    threads.asFlux().map { "$it | onNext on " + Thread.currentThread().name }.collectList().block()!!.forEach { println("  $it") }

    println("== 4. context: a Reactor Context reaches the flow as ReactorContext")
    val traceId = flow { emit(currentCoroutineContext()[ReactorContext]?.context?.getOrDefault("traceId", "none") ?: "no ReactorContext") }
    println("  with contextWrite: " + traceId.asFlux().contextWrite(Context.of("traceId", "t-123")).blockFirst())
    println("  without:           " + traceId.asFlux().blockFirst())
}
