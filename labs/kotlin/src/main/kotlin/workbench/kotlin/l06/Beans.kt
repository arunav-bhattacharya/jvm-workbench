package workbench.kotlin.l06

/**
 * A service a framework wraps in a proxy (transactions, metrics). The proxy is a generated subclass.
 *
 * TODO 5: as written, the class and feeMinor are final, so no subclass can exist. Don't add `open`:
 * mark the class with the all-open marker, workbench.kotlin.OpenForProxies.
 */
class FeeService {
    fun feeMinor(amountMinor: Long): Long = amountMinor * rateBps() / 10_000

    private fun rateBps(): Long = 125
}

/**
 * A row an ORM loads: it creates an empty object through a no-argument constructor, then sets the fields.
 *
 * TODO 6: give it a no-argument constructor for frameworks with the no-arg marker,
 * workbench.kotlin.NoArgEntity, and make it open with OpenForProxies too.
 */
class PaymentEntity(val id: String, var amountMinor: Long) {
    var note: String = "default-note"
}
