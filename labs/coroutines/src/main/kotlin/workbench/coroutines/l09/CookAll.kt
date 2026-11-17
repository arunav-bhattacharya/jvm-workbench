package workbench.coroutines.l09

/**
 * Cooks every dish and returns dish -> what came out of the kitchen.
 *
 * Use [helpers] coroutines that take dishes from one channel (fan-out), so at most [helpers]
 * cook calls run at once and each dish is cooked exactly once. Collect what the helpers cook
 * through a second channel (fan-in). If any cook call throws, cookAll throws it, and the other
 * helpers are cancelled.
 *
 * Bug: correct, but one dish at a time. Twelve dishes of 100 ms take 1.2 s instead of 0.3 s
 * with four helpers.
 */
suspend fun cookAll(
    dishes: List<String>,
    helpers: Int,
    cook: suspend (dish: String) -> String,
): Map<String, String> =
    dishes.associateWith { cook(it) }
