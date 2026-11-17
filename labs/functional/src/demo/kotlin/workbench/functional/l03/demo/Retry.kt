package workbench.functional.l03.demo

// A fake recipe website that times out a few times, then answers.
class FlakySite(private var failuresLeft: Int) {
    var calls = 0
    fun fetch(recipe: String): String {
        calls++
        if (failuresLeft-- > 0) throw IllegalStateException("site timeout on call $calls")
        return "page:$recipe"
    }
}

// A higher-order function: the loop is written once, and the work comes in as a function.
fun <T> retry(times: Int, block: () -> T): T {
    var last: Exception? = null
    repeat(times) { attempt ->
        try {
            return block()                          // returns from retry: repeat is inline
        } catch (e: Exception) {
            last = e
            println("  attempt ${attempt + 1} failed: ${e.message}")
        }
    }
    throw IllegalStateException("gave up after $times attempts", last)
}

// Another one: run any block, report how long it took, hand back its result unchanged.
fun <T> timed(label: String, block: () -> T): T {
    val start = System.nanoTime()
    try {
        return block()
    } finally {
        println("  $label took %.2f ms".format((System.nanoTime() - start) / 1e6))
    }
}

fun main() {
    val site = FlakySite(failuresLeft = 2)
    val page = timed("fetch with retry") { retry(3) { site.fetch("pancakes") } }
    println("result: $page after ${site.calls} calls")

    val down = FlakySite(failuresLeft = 5)
    try {
        retry(3) { down.fetch("waffles") }
    } catch (e: IllegalStateException) {
        println("result: ${e.message} (last cause: ${e.cause?.message})")
    }
}
