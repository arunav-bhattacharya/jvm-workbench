package workbench.kotlin.l06

/**
 * A service a framework wraps in a proxy (to time it, or to log every call). The proxy is a generated subclass.
 *
 * TODO 5: as written, the class and sheetsFor are final, so no subclass can exist. Don't add `open`:
 * mark the class with the all-open marker, workbench.kotlin.OpenForProxies.
 */
class SheetPlanner {
    /** Sheets of paper needed for [pages] pages printed on both sides. */
    fun sheetsFor(pages: Int): Int = (pages + sidesPerSheet() - 1) / sidesPerSheet()

    private fun sidesPerSheet(): Int = 2
}

/**
 * A row a database library loads: it creates an empty object through a no-argument constructor,
 * then sets the fields.
 *
 * TODO 6: give it a no-argument constructor for frameworks with the no-arg marker,
 * workbench.kotlin.NoArgEntity, and make it open with OpenForProxies too.
 */
class JobRecord(val id: String, var pages: Int) {
    var status: String = "NEW"
}
