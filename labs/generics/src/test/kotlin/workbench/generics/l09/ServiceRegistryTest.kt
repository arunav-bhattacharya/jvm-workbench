package workbench.generics.l09

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import kotlin.reflect.typeOf

class ServiceRegistryTest {

    @Test
    fun `get by KClass returns the registered service`() {
        val registry = ServiceRegistry()
        val gateway = FakeGateway("acquirer-a")
        registry.register(PaymentGateway::class, gateway)
        registry.register(FraudCheck::class, AlwaysLowRisk())
        assertThat(registry.get(PaymentGateway::class)).isSameAs(gateway)
        assertThat(registry.get(FraudCheck::class).score("pay_1")).isEqualTo(1)
    }

    @Test
    fun `reified get finds the service from the type argument alone`() {
        val registry = ServiceRegistry()
        val gateway = FakeGateway("acquirer-a")
        registry.register(PaymentGateway::class, gateway)
        registry.register(FraudCheck::class, AlwaysLowRisk())
        assertThat(Callers.gateway(registry)).isSameAs(gateway)
        assertThat(Callers.fraudCheck(registry)).isInstanceOf(AlwaysLowRisk::class.java)
    }

    @Test
    fun `a later registration replaces the earlier one`() {
        val registry = ServiceRegistry()
        registry.register(PaymentGateway::class, FakeGateway("acquirer-a"))
        registry.register(PaymentGateway::class, FakeGateway("acquirer-b"))
        assertThat(Callers.gateway(registry).authorize("pay_9", 1_200)).isEqualTo("acquirer-b approved pay_9 for 1200")
    }

    @Test
    fun `a missing service throws NoSuchElementException naming the class`() {
        val registry = ServiceRegistry()
        assertThatThrownBy { registry.get(FraudCheck::class) }
            .isInstanceOf(NoSuchElementException::class.java)
            .hasMessage("no service for FraudCheck")
        assertThatThrownBy { Callers.gateway(registry) }
            .isInstanceOf(NoSuchElementException::class.java)
            .hasMessage("no service for PaymentGateway")
    }

    @Test
    fun `a KClass key cannot tell Repository of Payment from Repository of Refund`() {
        // both have the class Repository, so the second registration overwrites the first
        val registry = ServiceRegistry()
        registry.register(Repository::class, InMemoryRepository(listOf(Payment("pay_1", 1_200))))
        registry.register(Repository::class, InMemoryRepository(listOf(Refund("ref_1", 500))))
        assertThat(registry.get(Repository::class).all()).containsExactly(Refund("ref_1", 500))
    }

    @Test
    fun `KType keys keep Repository of Payment and Repository of Refund apart`() {
        val registry = ServiceRegistry()
        val payments = InMemoryRepository(listOf(Payment("pay_1", 1_200), Payment("pay_2", 350)))
        val refunds = InMemoryRepository(listOf(Refund("ref_1", 500)))
        Callers.registerRepositories(registry, payments, refunds)

        assertThat(Callers.payments(registry).all()).containsExactly(Payment("pay_1", 1_200), Payment("pay_2", 350))
        assertThat(Callers.refunds(registry).all()).containsExactly(Refund("ref_1", 500))
    }

    @Test
    fun `getTyped by KType uses the full type, arguments included`() {
        val registry = ServiceRegistry()
        val refunds = InMemoryRepository(listOf(Refund("ref_1", 500)))
        registry.registerTyped(typeOf<Repository<Refund>>(), refunds)
        assertThat(registry.getTyped(typeOf<Repository<Refund>>())).isSameAs(refunds)
        assertThatThrownBy { registry.getTyped(typeOf<Repository<Payment>>()) }
            .isInstanceOf(NoSuchElementException::class.java)
            .hasMessageStartingWith("no service for ")
    }
}
