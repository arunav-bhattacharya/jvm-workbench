package workbench.functional.l04.demo

// Cookie, Status and sampleDay are in SampleDay.kt, next to this file.

// The loop: four results built at once, and every line changes one of them.
fun reportLoop(cookies: List<Cookie>): String {
    var golden = 0
    val net = LinkedHashMap<String, Int>()
    val burnt = ArrayList<String>()
    var largest = cookies.first()
    for (c in cookies) {
        when (c.status) {
            Status.GOLDEN -> {
                golden += c.grams
                net[c.flavor] = (net[c.flavor] ?: 0) + c.grams - (c.nibbledGrams ?: 0)
                if (c.grams > largest.grams) largest = c
            }
            Status.BURNT -> burnt.add(c.id)
            Status.RAW -> {}
        }
    }
    return "golden=$golden net=$net burnt=$burnt largest=${largest.id}"
}

// The same report: one val per result, each computed from the list.
fun reportChain(cookies: List<Cookie>): String {
    val goldenCookies = cookies.filter { it.status == Status.GOLDEN }
    val golden = goldenCookies.sumOf { it.grams }
    val net = goldenCookies.groupBy { it.flavor }
        .mapValues { (_, cs) -> cs.sumOf { it.grams - (it.nibbledGrams ?: 0) } }
    val burnt = cookies.filter { it.status == Status.BURNT }.map { it.id }
    val largest = goldenCookies.maxByOrNull { it.grams }
    return "golden=$golden net=$net burnt=$burnt largest=${largest?.id}"
}

fun main(args: Array<String>) {
    val cookies = if (args.firstOrNull() == "empty") emptyList() else sampleDay
    println("chain: ${reportChain(cookies)}")
    try {
        println("loop:  ${reportLoop(cookies)}")
    } catch (e: NoSuchElementException) {
        println("loop:  threw $e")
    }
}
