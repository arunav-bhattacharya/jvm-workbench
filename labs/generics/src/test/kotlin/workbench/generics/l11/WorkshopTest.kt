package workbench.generics.l11

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.generics.JavaSignatures

class WorkshopTest {

    // ---- Either ----

    private fun parseCents(text: String): Either<String, Long> =
        text.toLongOrNull()?.let { Either.Right(it) } ?: Either.Left("not a number: $text")

    @Test
    fun `map transforms a Right and passes a Left through`() {
        assertThat(parseCents("1200").map { it / 100 }).isEqualTo(Either.Right(12L))
        val failed: Either<String, String> = parseCents("x").map { "cents $it" }
        assertThat(failed).isEqualTo(Either.Left("not a number: x"))
    }

    @Test
    fun `getOrElse returns the Right value or the fallback for a Left`() {
        assertThat(parseCents("350").getOrElse { -1 }).isEqualTo(350L)
        assertThat(parseCents("oops").getOrElse { it.length.toLong() }).isEqualTo(18L)   // "not a number: oops"
    }

    // ---- Repository ----

    @Test
    fun `InMemoryRepository saves, finds by id and lists in id order`() {
        val merchants = InMemoryRepository<Merchant, Long>()
        merchants.save(Merchant(7, "Kiosk"))
        merchants.save(Merchant(2, "Bakery"))
        assertThat(merchants.findById(7)).isEqualTo(Merchant(7, "Kiosk"))
        assertThat(merchants.findById(99)).isNull()
        assertThat(merchants.findAll().map { it.id }).containsExactly(2L, 7L)
    }

    @Test
    fun `saveAll saves every item and returns them in the order given`() {
        val settlements = InMemoryRepository<Settlement, String>()
        val saved = settlements.saveAll(listOf(Settlement("s-2", 500), Settlement("s-1", 1_200)))
        assertThat(saved.map { it.id }).containsExactly("s-2", "s-1")
        assertThat(settlements.findAll().map { it.id }).containsExactly("s-1", "s-2")
    }

    @Test
    fun `describeAll prints one line per entity`() {
        val view = object : ReadRepository<Entity<*>> {
            override fun findAll(): List<Entity<*>> = listOf(Merchant(1, "Kiosk"), Settlement("s-9", 99))
        }
        assertThat(describeAll(view)).containsExactly("entity 1", "entity s-9")
    }

    @Test
    fun `ReadRepository is covariant, so describeAll accepts a repository of any entity`() {
        // with `out T`, Kotlin writes a ? extends wildcard into describeAll's Java signature
        assertThat(JavaSignatures.paramText("workbench.generics.l11.RepositoryKt", "describeAll", 0))
            .`as`("describeAll's parameter as Java sees it (add `out` to ReadRepository)")
            .isEqualTo("ReadRepository<? extends Entity<?>>")
    }

    // ---- EventBus ----

    @Test
    fun `publish calls the handlers for the event's class, in order, and counts them`() {
        val bus = EventBus()
        val log = mutableListOf<String>()
        bus.subscribe(CardAuthorized::class) { log += "fraud ${it.cents}" }
        bus.subscribe(CardAuthorized::class) { log += "ledger ${it.paymentId}" }
        bus.subscribe(RefundIssued::class) { log += "refund ${it.paymentId}" }

        assertThat(bus.publish(CardAuthorized("pay_1", 1_200))).isEqualTo(2)
        assertThat(log).containsExactly("fraud 1200", "ledger pay_1")
    }

    @Test
    fun `a handler for every PaymentEvent can subscribe to one event class`() {
        val bus = EventBus()
        val log = mutableListOf<String>()
        val auditAll: (PaymentEvent) -> Unit = { log += "audit ${it.paymentId}" }
        bus.subscribe(CardAuthorized::class, auditAll)    // (PaymentEvent) -> Unit is a (CardAuthorized) -> Unit
        bus.subscribe(RefundIssued::class, auditAll)
        bus.publish(CardAuthorized("pay_1", 1_200))
        bus.publish(RefundIssued("pay_2", 500))
        assertThat(log).containsExactly("audit pay_1", "audit pay_2")
    }

    @Test
    fun `reified subscribe takes the event class from the type argument`() {
        val bus = EventBus()
        val log = mutableListOf<String>()
        Callers.onCard(bus) { log += "card ${it.cents}" }
        Callers.onRefund(bus) { log += "refund ${it.cents}" }
        bus.publish(RefundIssued("pay_3", 75))
        assertThat(log).containsExactly("refund 75")
    }

    @Test
    fun `publish with no handlers for that class calls nobody`() {
        val bus = EventBus()
        val log = mutableListOf<String>()
        bus.subscribe(CardAuthorized::class) { log += "card" }
        assertThat(bus.publish(RefundIssued("pay_4", 10))).isZero()
        assertThat(log).isEmpty()
    }

    // ---- Attributes ----

    @Test
    fun `attributes return the value with the key's type, or null`() {
        val attrs = Attributes()
        attrs[Callers.currencies()] = listOf("EUR", "USD")
        val currencies: List<String>? = attrs[Callers.currencies()]   // no cast at the call site
        assertThat(currencies).containsExactly("EUR", "USD")
        assertThat(attrs[Callers.retryCount()]).isNull()
        assertThat(attrs.getOrDefault(Callers.retryCount(), 3)).isEqualTo(3)
    }

    @Test
    fun `keys with the same name but different types do not collide`() {
        val attrs = Attributes()
        attrs[Callers.retryDelays()] = listOf(100L, 400L)
        attrs[Callers.retryCount()] = 2
        assertThat(Callers.retryDelays()).isNotEqualTo(Callers.retryCount())   // same name, different KType
        assertThat(attrs[Callers.retryDelays()]).containsExactly(100L, 400L)
        assertThat(attrs[Callers.retryCount()]).isEqualTo(2)
    }

    @Test
    fun `remove returns the old value and clears it`() {
        val attrs = Attributes()
        attrs[Callers.retryCount()] = 5
        assertThat(attrs.remove(Callers.retryCount())).isEqualTo(5)
        assertThat(attrs[Callers.retryCount()]).isNull()
        assertThat(attrs.remove(Callers.retryCount())).isNull()
    }
}
