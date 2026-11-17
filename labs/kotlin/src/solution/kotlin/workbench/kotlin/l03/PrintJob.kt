package workbench.kotlin.l03

import kotlin.properties.Delegates

/** A print job being prepared. Every recorded property is audited in [log]. */
class PrintJob(val log: ChangeLog) {
    var status: String by log.recorded("NEW")
    var copies: Int by log.recorded(1)
    var note: String? by log.recorded(null)

    /** vetoable: the handler runs before the assignment, and false keeps the old value. */
    var paperSize: String by Delegates.vetoable("A4") { _, _, new -> new.matches(Regex("A[0-6]")) }
}

/** Settings for one printer, read from a parsed config map. `by map` looks up the property name as the key. */
class PrinterProfile(settings: Map<String, Any?>) {
    val name: String by settings
    val dailyPageLimit: Long by settings
}
