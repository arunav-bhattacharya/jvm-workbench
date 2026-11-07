package workbench.kotlin.l02

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.lang.reflect.InvocationTargetException

class MoneyTest {

    @Test
    fun `Money rejects a negative amount`() {
        assertThatThrownBy { Money(-1) }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessageContaining("-1")
        assertThat(Money(0).cents).isEqualTo(0)
    }

    @Test
    fun `parse reads an amount with up to two decimals`() {
        assertThat(Money.parse("12.34")).isEqualTo(Money(1234))
        assertThat(Money.parse("10").toString()).isEqualTo("10.00")
        assertThat((Money.parse("10") + Money(500)).toString()).isEqualTo("15.00")
        assertThat(Money(7).toString()).isEqualTo("0.07")
    }

    @Test
    fun `parse refuses sub-cent and negative amounts`() {
        assertThatThrownBy { Money.parse("1.234") }.isInstanceOf(ArithmeticException::class.java)
        assertThatThrownBy { Money.parse("-0.01") }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `plus and times fail loudly on overflow`() {
        assertThat(Money(250) * 3).isEqualTo(Money(750))
        assertThat(Money(250) + Money(1)).isEqualTo(Money(251))
        assertThatThrownBy { Money(Long.MAX_VALUE) + Money(1) }.isInstanceOf(ArithmeticException::class.java)
        assertThatThrownBy { Money(Long.MAX_VALUE / 2 + 1) * 2 }.isInstanceOf(ArithmeticException::class.java)
    }

    @Test
    fun `Money sorts by amount, even when boxed in a list`() {
        val sorted = listOf(Money(300), Money(100), Money(200)).sorted()
        assertThat(sorted).containsExactly(Money(100), Money(200), Money(300))
        // inside a List the value class is boxed: the element is a real Money object
        val first: Any = sorted[0]
        assertThat(first.javaClass).isEqualTo(Money::class.java)
    }

    @Test
    fun `IdempotencyKey accepts well-formed keys and rejects the rest`() {
        assertThat(IdempotencyKey("order-981_attempt-1").value).isEqualTo("order-981_attempt-1")
        for (bad in listOf("short", "x".repeat(65), "order 981 attempt", "order-981/1", "ordér-9811")) {
            assertThatThrownBy { IdempotencyKey(bad) }
                .`as`("key '%s'", bad)
                .isInstanceOf(IllegalArgumentException::class.java)
        }
    }

    @Test
    fun `receiptLine formats an amount for Kotlin callers`() {
        assertThat(receiptLine(Money(1999))).isEqualTo("EUR 19.99")
    }

    @Test
    fun `the Java entry point has a plain JVM name and still validates`() {
        // this is the lookup javac does when Java writes ReceiptsKt.receiptLineForJava(1999L)
        val receipts = Class.forName("workbench.kotlin.l02.ReceiptsKt")
        val names = receipts.declaredMethods.map { it.name }
        assertThat(names).anyMatch { it.startsWith("receiptLine-") }   // the Kotlin one stays mangled
        val forJava = receipts.getMethod("receiptLineForJava", Long::class.javaPrimitiveType)
        assertThat(forJava.invoke(null, 1999L)).isEqualTo("EUR 19.99")
        assertThatThrownBy { forJava.invoke(null, -500L) }
            .isInstanceOf(InvocationTargetException::class.java)
            .hasCauseInstanceOf(IllegalArgumentException::class.java)
    }
}
