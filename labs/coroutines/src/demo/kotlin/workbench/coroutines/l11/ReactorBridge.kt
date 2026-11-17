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

/** A Kotlin suspend call, handed to Reactor code as a cold Mono. */
fun recipeFor(dish: String): Mono<String> = mono {
    println("  [kotlin] looking up $dish")
    delay(50)
    if (dish == "dragon stew") null else "$dish: 40 minutes"
}

/** A Kotlin Flow of oven temperatures, handed to Reactor code as a Flux. */
fun temperatures(): Flow<Int> = flow { for (i in 0 until 5) { delay(20); emit(180 + i * 5) } }
fun temperatureFlux(): Flux<Int> = temperatures().asFlux()

fun main() = runBlocking {
    println("1. mono { } is cold:")
    val m = recipeFor("soup")
    println("  built the Mono; nothing looked up yet")
    println("  awaitSingle() -> ${m.awaitSingle()}")
    println("  awaitSingle() again -> ${m.awaitSingle()}")

    println("2. an empty Mono:")
    try { recipeFor("dragon stew").awaitSingle() } catch (e: NoSuchElementException) { println("  awaitSingle() threw NoSuchElementException") }

    println("3. a Flux consumed as a Flow (cancelling the flow cancels the subscription):")
    val plates = Flux.interval(Duration.ofMillis(10)).map { "plate-$it" }.doOnCancel { println("  [reactor] subscription cancelled") }
    println("  ${plates.asFlow().take(3).toList()}")

    println("4. a Flow handed to Reactor as a Flux:")
    println("  ${temperatureFlux().map { "$it C" }.collectList().block()}")
}
