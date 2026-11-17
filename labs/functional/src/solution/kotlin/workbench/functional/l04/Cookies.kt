package workbench.functional.l04

/** How a cookie came out of the oven. */
enum class Status { GOLDEN, RAW, BURNT }

data class Cookie(
    val id: String,
    val flavor: String,
    val grams: Int,
    val status: Status,
    val nibbledGrams: Int? = null,      // set when someone took a bite of a golden cookie
)

/** One tray out of the oven. A baking day is a list of trays. */
data class Tray(val id: String, val cookies: List<Cookie>)

data class BakeReport(
    val cookieCount: Int,               // cookies on all trays
    val goldenGrams: Int,               // sum of grams of GOLDEN cookies
    val nibbledGrams: Int,              // sum of every bite that was taken
    val netByFlavor: Map<String, Int>,  // GOLDEN only: grams minus bites, flavors in first-seen order
    val burntIds: List<String>,         // ids of BURNT cookies, in input order
    val largestGolden: Cookie?,         // the heaviest GOLDEN cookie, null when there is none
)

/**
 * The report as it was first written: one loop and five mutable accumulators. It is finished and
 * gives the right answer on a normal day. Read it; don't edit it. One test compares your version with it.
 * It also has two bugs that a normal day never shows. The tests for your version find both.
 */
fun bakeReportLoop(trays: List<Tray>): BakeReport {
    val all = ArrayList<Cookie>()
    for (t in trays) for (c in t.cookies) all.add(c)
    var golden = 0
    var nibbled = 0
    val net = LinkedHashMap<String, Int>()
    val burnt = ArrayList<String>()
    var largest = all.first()
    for (c in all) {
        if (c.nibbledGrams != null) nibbled += c.nibbledGrams
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
    return BakeReport(all.size, golden, nibbled, net, burnt, largest)
}
