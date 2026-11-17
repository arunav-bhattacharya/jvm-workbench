package workbench.kotlin.l03

/** A print job being prepared. Every recorded property is audited in [log]. Finished: it uses your delegates. */
class PrintJob(val log: ChangeLog) {
    var status: String by log.recorded("NEW")
    var copies: Int by log.recorded(1)
    var note: String? by log.recorded(null)

    /**
     * TODO 4: the paper size. Start at "A4", and ignore any assignment that isn't a capital A
     * followed by one digit from 0 to 6: `job.paperSize = "a3"` leaves it unchanged.
     * Use a delegate from kotlin.properties.Delegates.
     */
    var paperSize: String = "A4"
}

/**
 * Settings for one printer, read from a parsed config map such as
 * mapOf("name" to "Laser 7", "dailyPageLimit" to 5_000L).
 *
 * TODO 5: delegate both properties to the map, so each reads the key with its own name.
 * A missing key should fail when the property is read, not when the object is built.
 */
class PrinterProfile(settings: Map<String, Any?>) {
    val name: String get() = TODO("delegate to the map")
    val dailyPageLimit: Long get() = TODO("delegate to the map")
}
