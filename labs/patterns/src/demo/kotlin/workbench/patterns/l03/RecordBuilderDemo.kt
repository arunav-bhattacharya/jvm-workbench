package workbench.patterns.l03

import java.time.Duration

// The Kotlin twin of RecordBuilderDemo.java: no builder and no withers, because named arguments,
// defaults and copy() do both jobs. The rules still live in one place: init.

data class DeliveryRequest(
    val address: String,
    val speed: String = "STANDARD",
    val notes: Map<String, String> = emptyMap(),
    val window: Duration = Duration.ofHours(2),
    val retries: Int = 0,
) {
    init {                                                    // runs for every construction, copy() included
        require(retries >= 0) { "retries must be >= 0, was $retries" }
    }
}

fun main() {
    val req = DeliveryRequest(
        address = "12 Mill Lane",
        speed = "EXPRESS",
        notes = mapOf("door" to "blue gate"),
        retries = 2,
    )
    println("built:        $req")
    println("narrower:     ${req.copy(window = Duration.ofMinutes(30)).window}")

    // Map is a read-only type, so there is no put(). Force a cast and the map behind it refuses too:
    val write = runCatching { (req.notes as MutableMap<String, String>)["dog"] = "friendly" }
    println("notes:        ${if (write.isFailure) "unmodifiable" else "writable!"}")

    try {
        req.copy(retries = -1)                                // copy() can't skip the check either
    } catch (e: IllegalArgumentException) {
        println("copy():       ${e.message}")
    }
}
