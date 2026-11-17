package workbench.functional.l04

// Each function is one chain. Every operation here is inline on Iterable, so no lambda objects
// are created; each step does build a new list or map.

fun allCookies(trays: List<Tray>): List<Cookie> = trays.flatMap { it.cookies }

fun goldenGrams(cookies: List<Cookie>): Int =
    cookies.filter { it.status == Status.GOLDEN }.sumOf { it.grams }      // sumOf of nothing is 0

fun nibbledGrams(cookies: List<Cookie>): Int =
    cookies.mapNotNull { it.nibbledGrams }.sum()        // the nulls disappear, so sum sees only bites

// groupBy returns a LinkedHashMap in first-seen key order, and mapValues keeps that order.
fun netByFlavor(cookies: List<Cookie>): Map<String, Int> =
    cookies.filter { it.status == Status.GOLDEN }
        .groupBy { it.flavor }
        .mapValues { (_, cs) -> cs.sumOf { it.grams - (it.nibbledGrams ?: 0) } }

fun burntIds(cookies: List<Cookie>): List<String> =
    cookies.filter { it.status == Status.BURNT }.map { it.id }

// maxByOrNull returns null on an empty list instead of throwing, and keeps the first of equal maxima.
fun largestGolden(cookies: List<Cookie>): Cookie? =
    cookies.filter { it.status == Status.GOLDEN }.maxByOrNull { it.grams }

// fold is the general loop: the accumulator is the jar, and the lambda is one turn of the loop.
fun jarGrams(startGrams: Int, cookies: List<Cookie>): Int =
    cookies.fold(startGrams) { jar, c ->
        when (c.status) {
            Status.GOLDEN -> jar + c.grams - (c.nibbledGrams ?: 0)
            Status.RAW, Status.BURNT -> jar
        }
    }

// associateBy silently keeps the last value for a repeated key, so look for repeats first.
fun indexById(cookies: List<Cookie>): Map<String, Cookie> {
    val duplicates = cookies.groupingBy { it.id }.eachCount().filterValues { it > 1 }.keys
    require(duplicates.isEmpty()) { "duplicate cookie ids: ${duplicates.joinToString()}" }
    return cookies.associateBy { it.id }
}

fun bakeReport(trays: List<Tray>): BakeReport {
    val cookies = allCookies(trays)
    indexById(cookies)                                  // refuse the day before adding anything up
    return BakeReport(
        cookieCount = cookies.size,
        goldenGrams = goldenGrams(cookies),
        nibbledGrams = nibbledGrams(cookies),
        netByFlavor = netByFlavor(cookies),
        burntIds = burntIds(cookies),
        largestGolden = largestGolden(cookies),
    )
}
