package workbench.kotlin.l06

import workbench.kotlin.NoArgEntity
import workbench.kotlin.OpenForProxies

/**
 * A service a framework wraps in a proxy (transactions, metrics). The proxy is a generated subclass,
 * so the class and its public methods must not be final. all-open removes the final for us.
 */
@OpenForProxies
class FeeService {
    fun feeMinor(amountMinor: Long): Long = amountMinor * rateBps() / 10_000

    private fun rateBps(): Long = 125            // private members stay private and final
}

/**
 * A row an ORM loads: it creates an empty object through a no-argument constructor, then sets the
 * fields. no-arg generates that constructor; all-open lets the ORM subclass it for lazy loading.
 */
@NoArgEntity
@OpenForProxies
class PaymentEntity(val id: String, var amountMinor: Long) {
    var note: String = "default-note"            // NOT run by the generated constructor
}
