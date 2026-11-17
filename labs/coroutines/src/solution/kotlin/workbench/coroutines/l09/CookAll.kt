package workbench.coroutines.l09

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.produce
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch

@OptIn(ExperimentalCoroutinesApi::class) // produce is still marked experimental
suspend fun cookAll(
    dishes: List<String>,
    helpers: Int,
    cook: suspend (dish: String) -> String,
): Map<String, String> = coroutineScope {
    // 1. fan-out source: a rendezvous channel, closed automatically when the block ends
    val hatch = produce { for (dish in dishes) send(dish) }
    // 2. fan-in: every helper sends what it cooked here
    val done = Channel<Pair<String, String>>()
    val team = List(helpers) {
        launch {
            for (dish in hatch) done.send(dish to cook(dish)) // each dish is received by exactly one helper
        }
    }
    // 3. close the fan-in channel once every helper is done, so the loop below can end
    launch { team.joinAll(); done.close() }
    val result = LinkedHashMap<String, String>()
    for ((dish, plate) in done) result[dish] = plate
    result
}
