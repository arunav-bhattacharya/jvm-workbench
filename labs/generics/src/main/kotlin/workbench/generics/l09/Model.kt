package workbench.generics.l09

/** Services the payment app looks up by type. */
interface PaymentGateway { fun authorize(paymentId: String, cents: Long): String }
interface FraudCheck { fun score(paymentId: String): Int }

class FakeGateway(private val name: String) : PaymentGateway {
    override fun authorize(paymentId: String, cents: Long) = "$name approved $paymentId for $cents"
}
class AlwaysLowRisk : FraudCheck {
    override fun score(paymentId: String) = 1
}

data class Payment(val id: String, val cents: Long)
data class Refund(val id: String, val cents: Long)

/** A generic service: Repository<Payment> and Repository<Refund> are different types with ONE class. */
interface Repository<T> { fun all(): List<T> }
class InMemoryRepository<T>(private val items: List<T>) : Repository<T> {
    override fun all(): List<T> = items
}
