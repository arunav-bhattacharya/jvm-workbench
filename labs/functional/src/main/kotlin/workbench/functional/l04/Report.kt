package workbench.functional.l04

// Write each function as one chain of collection operations: no `for`, no `var`.
// Each TODO names the operation that fits. All of them must work on an empty list.

/** TODO 1: every cookie of every tray, in order. (flatMap) */
fun allCookies(trays: List<Tray>): List<Cookie> = TODO("flatMap")

/** TODO 2: the sum of grams of GOLDEN cookies. 0 for none. (filter, sumOf) */
fun goldenGrams(cookies: List<Cookie>): Int = TODO("filter, sumOf")

/** TODO 3: the sum of every bite that was taken. Most cookies have none. (mapNotNull, sum) */
fun nibbledGrams(cookies: List<Cookie>): Int = TODO("mapNotNull, sum")

/**
 * TODO 4: for GOLDEN cookies only, grams minus the bite, added up per flavor.
 * Flavors appear in the order they are first seen. (filter, groupBy, mapValues, sumOf)
 */
fun netByFlavor(cookies: List<Cookie>): Map<String, Int> = TODO("filter, groupBy, mapValues")

/** TODO 5: the ids of BURNT cookies, in input order. (filter, map) */
fun burntIds(cookies: List<Cookie>): List<String> = TODO("filter, map")

/** TODO 6: the GOLDEN cookie with the most grams, or null when none came out golden. (filter, maxByOrNull) */
fun largestGolden(cookies: List<Cookie>): Cookie? = TODO("filter, maxByOrNull")

/**
 * TODO 7: what the cookie jar holds after the day. Start from [startGrams], what is already in the jar;
 * each GOLDEN cookie adds its grams minus its bite; RAW and BURNT cookies stay out of the jar. (fold)
 */
fun jarGrams(startGrams: Int, cookies: List<Cookie>): Int = TODO("fold with a when inside")

/**
 * TODO 8: map each id to its cookie. associateBy alone would keep the last cookie for a repeated id
 * and say nothing. Instead, throw IllegalArgumentException("duplicate cookie ids: c2, c7"):
 * each repeated id once, in the order first seen, joined with ", ". (groupingBy, eachCount, associateBy)
 */
fun indexById(cookies: List<Cookie>): Map<String, Cookie> = TODO("find duplicates first, then associateBy")

/**
 * TODO 9: the whole report for one baking day, built from the functions above.
 * A day with repeated cookie ids must be refused (call indexById). A day with no cookies is a normal day.
 */
fun bakeReport(trays: List<Tray>): BakeReport = TODO("allCookies, indexById, then the rest")
