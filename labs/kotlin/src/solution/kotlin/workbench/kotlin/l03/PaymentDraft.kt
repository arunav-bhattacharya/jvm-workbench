package workbench.kotlin.l03

import kotlin.properties.Delegates

/** A payment being prepared. Every recorded property is audited in [log]. */
class PaymentDraft(val log: ChangeLog) {
    var status: String by log.recorded("NEW")
    var amountMinor: Long by log.recorded(0L)
    var note: String? by log.recorded(null)

    /** vetoable: the handler runs before the assignment, and false keeps the old value. */
    var currency: String by Delegates.vetoable("EUR") { _, _, new -> new.matches(Regex("[A-Z]{3}")) }
}

/** Settings for one merchant, read from a parsed config map. `by map` looks up the property name as the key. */
class MerchantConfig(settings: Map<String, Any?>) {
    val name: String by settings
    val dailyLimitMinor: Long by settings
}
