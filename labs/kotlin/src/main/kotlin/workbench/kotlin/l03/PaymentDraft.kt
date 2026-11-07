package workbench.kotlin.l03

/** A payment being prepared. Every recorded property is audited in [log]. Finished: it uses your delegates. */
class PaymentDraft(val log: ChangeLog) {
    var status: String by log.recorded("NEW")
    var amountMinor: Long by log.recorded(0L)
    var note: String? by log.recorded(null)

    /**
     * TODO 4: an ISO currency code. Start at "EUR", and ignore any assignment that isn't three capital
     * letters: `draft.currency = "usd"` leaves it unchanged. Use a delegate from kotlin.properties.Delegates.
     */
    var currency: String = "EUR"
}

/**
 * Settings for one merchant, read from a parsed config map such as mapOf("name" to "Kiosk 7", "dailyLimitMinor" to 500_000L).
 *
 * TODO 5: delegate both properties to the map, so each reads the key with its own name.
 * A missing key should fail when the property is read, not when the object is built.
 */
class MerchantConfig(settings: Map<String, Any?>) {
    val name: String get() = TODO("delegate to the map")
    val dailyLimitMinor: Long get() = TODO("delegate to the map")
}
