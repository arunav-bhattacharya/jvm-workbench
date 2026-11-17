package workbench.kotlin.l06

import workbench.kotlin.NoArgEntity
import workbench.kotlin.OpenForProxies

/**
 * A service a framework wraps in a proxy (to time it, or to log every call). The proxy is a generated
 * subclass, so the class and its public methods must not be final. all-open removes the final for us.
 */
@OpenForProxies
class SheetPlanner {
    /** Sheets of paper needed for [pages] pages printed on both sides. */
    fun sheetsFor(pages: Int): Int = (pages + sidesPerSheet() - 1) / sidesPerSheet()

    private fun sidesPerSheet(): Int = 2            // private members stay private and final
}

/**
 * A row a database library loads: it creates an empty object through a no-argument constructor,
 * then sets the fields. no-arg generates that constructor; all-open lets the library subclass it.
 */
@NoArgEntity
@OpenForProxies
class JobRecord(val id: String, var pages: Int) {
    var status: String = "NEW"                     // NOT run by the generated constructor
}
