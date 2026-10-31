package workbench.generics.l05

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.generics.JavaSignatures

class ContravarianceTest {
    private val a1 = CardAuthorized("pay_3", 1_200)
    private val a2 = CardAuthorized("pay_1", 350)
    private val r1 = RefundIssued("pay_2", 500)

    @Test
    fun `CollectingSink remembers every item in order`() {
        val sink = CollectingSink<PaymentEvent>()
        sink.accept(a1)
        sink.accept(r1)
        assertThat(sink.items).containsExactly(a1, r1)
    }

    @Test
    fun `CollectingSink items cannot be used to change its history`() {
        val sink = CollectingSink<String>()
        sink.accept("EUR")
        val seen = sink.items
        sink.accept("USD")
        assertThat(seen).containsExactly("EUR")              // a snapshot, not a live view
        assertThat(sink.items).containsExactly("EUR", "USD")
    }

    @Test
    fun `feedAll sends every event and counts them`() {
        val sink = CollectingSink<PaymentEvent>()
        assertThat(feedAll(listOf(a1, r1, a2), sink)).isEqualTo(3)
        assertThat(sink.items).containsExactly(a1, r1, a2)
    }

    @Test
    fun `Sink is declared in, so Java sees feedAll taking Sink of super PaymentEvent`() {
        // Kotlin writes a ? super wildcard into a parameter only when the class is declared `in`
        assertThat(JavaSignatures.paramText("workbench.generics.l05.SinkKt", "feedAll", 1))
            .`as`("feedAll's sink parameter as Java sees it (add `in` to Sink's type parameter)")
            .isEqualTo("Sink<? super PaymentEvent>")
    }

    @Test
    fun `highest ranks a list of CardAuthorized with a Comparator of PaymentEvent`() {
        val top: CardAuthorized = highest(listOf(a2, a1), byPaymentId)
        assertThat(top).isEqualTo(a1)                        // pay_3 sorts last
        assertThat(highest(listOf(1, 9, 4), naturalOrder<Int>())).isEqualTo(9)
    }

    @Test
    fun `highest of an empty list throws IllegalArgumentException`() {
        assertThatThrownBy { highest(emptyList<CardAuthorized>(), byPaymentId) }
            .isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `a handler for any PaymentEvent can subscribe to a Dispatcher of CardAuthorized`() {
        val audit = mutableListOf<String>()
        val auditAll: (PaymentEvent) -> Unit = { audit += "audit ${it.paymentId}" }
        val cardsOnly: (CardAuthorized) -> Unit = { audit += "fraud check ${it.cents}" }

        val dispatcher = Dispatcher<CardAuthorized>()
        dispatcher.subscribe(auditAll)                      // compiles: Function1 is in in its parameter
        dispatcher.subscribe(cardsOnly)

        assertThat(dispatcher.publish(a1)).isEqualTo(2)
        assertThat(audit).containsExactly("audit pay_3", "fraud check 1200")
    }

    @Test
    fun `publish with no handlers calls nobody`() {
        assertThat(Dispatcher<RefundIssued>().publish(r1)).isZero()
    }
}
