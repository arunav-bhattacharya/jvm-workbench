package workbench.coroutines.l11

import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.reactive.asFlow
import kotlinx.coroutines.reactive.awaitSingle
import kotlinx.coroutines.reactor.asFlux
import kotlinx.coroutines.reactor.mono
import kotlinx.coroutines.runBlocking
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

/** A Kotlin suspend call, exposed to Reactor code as a cold Mono. */
fun quoteFor(acquirer: String): Mono<String> = mono {
    println("  [kotlin] asking $acquirer for a quote")
    delay(50)
    if (acquirer == "nobody") null else "$acquirer: 1.80%"
}

/** A Kotlin Flow of FX ticks, exposed to Reactor code as a Flux. */
fun ticks(): Flow<Double> = flow { for (i in 0 until 5) { delay(20); emit(1.0800 + i / 10_000.0) } }
fun tickFlux(): Flux<Double> = ticks().asFlux()

fun main() = runBlocking {
    println("1. mono { } is cold:")
    val m = quoteFor("north")
    println("  built the Mono; nothing asked yet")
    println("  awaitSingle() -> ${m.awaitSingle()}")
    println("  awaitSingle() again -> ${m.awaitSingle()}")

    println("2. an empty Mono:")
    try { quoteFor("nobody").awaitSingle() } catch (e: NoSuchElementException) { println("  awaitSingle() threw NoSuchElementException") }

    println("3. a Flux consumed as a Flow (cancelling the flow cancels the subscription):")
    val settlements = Flux.interval(Duration.ofMillis(10)).map { "batch-$it" }.doOnCancel { println("  [reactor] subscription cancelled") }
    println("  ${settlements.asFlow().take(3).toList()}")

    println("4. a Flow handed to Reactor as a Flux:")
    println("  ${tickFlux().map { "%.4f".format(it) }.collectList().block()}")
}
