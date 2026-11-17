package workbench.kotlin.l02

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.lang.reflect.InvocationTargetException

class WeightTest {

    @Test
    fun `Weight rejects a negative weight`() {
        assertThatThrownBy { Weight(-1) }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessageContaining("-1")
        assertThat(Weight(0).grams).isEqualTo(0)
    }

    @Test
    fun `parse reads kilograms with up to three decimals`() {
        assertThat(Weight.parse("1.25")).isEqualTo(Weight(1250))
        assertThat(Weight.parse("10").toString()).isEqualTo("10.000")
        assertThat((Weight.parse("10") + Weight(500)).toString()).isEqualTo("10.500")
        assertThat(Weight(7).toString()).isEqualTo("0.007")
    }

    @Test
    fun `parse refuses fractions of a gram and negative weights`() {
        assertThatThrownBy { Weight.parse("1.2345") }.isInstanceOf(ArithmeticException::class.java)
        assertThatThrownBy { Weight.parse("-0.001") }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `plus and times fail loudly on overflow`() {
        assertThat(Weight(250) * 3).isEqualTo(Weight(750))
        assertThat(Weight(250) + Weight(1)).isEqualTo(Weight(251))
        assertThatThrownBy { Weight(Long.MAX_VALUE) + Weight(1) }.isInstanceOf(ArithmeticException::class.java)
        assertThatThrownBy { Weight(Long.MAX_VALUE / 2 + 1) * 2 }.isInstanceOf(ArithmeticException::class.java)
    }

    @Test
    fun `Weight sorts by grams, even when boxed in a list`() {
        val sorted = listOf(Weight(300), Weight(100), Weight(200)).sorted()
        assertThat(sorted).containsExactly(Weight(100), Weight(200), Weight(300))
        // inside a List the value class is boxed: the element is a real Weight object
        val first: Any = sorted[0]
        assertThat(first.javaClass).isEqualTo(Weight::class.java)
    }

    @Test
    fun `JobId accepts well-formed ids and rejects the rest`() {
        assertThat(JobId("job-2026_0042").value).isEqualTo("job-2026_0042")
        for (bad in listOf("short", "x".repeat(65), "job 2026 0042", "job-2026/42", "jöb-20260042")) {
            assertThatThrownBy { JobId(bad) }
                .`as`("id '%s'", bad)
                .isInstanceOf(IllegalArgumentException::class.java)
        }
    }

    @Test
    fun `parcelLabel formats a weight for Kotlin callers`() {
        assertThat(parcelLabel(Weight(1250))).isEqualTo("Parcel 1.250 kg")
    }

    @Test
    fun `the Java entry point has a plain JVM name and still validates`() {
        // this is the lookup javac does when Java writes LabelsKt.parcelLabelForJava(1250L)
        val labels = Class.forName("workbench.kotlin.l02.LabelsKt")
        val names = labels.declaredMethods.map { it.name }
        assertThat(names).anyMatch { it.startsWith("parcelLabel-") }   // the Kotlin one stays mangled
        val forJava = labels.getMethod("parcelLabelForJava", Long::class.javaPrimitiveType)
        assertThat(forJava.invoke(null, 1250L)).isEqualTo("Parcel 1.250 kg")
        assertThatThrownBy { forJava.invoke(null, -500L) }
            .isInstanceOf(InvocationTargetException::class.java)
            .hasCauseInstanceOf(IllegalArgumentException::class.java)
    }
}
