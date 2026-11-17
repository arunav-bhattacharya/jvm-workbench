package workbench.events.l01

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatCode
import org.assertj.core.api.Assertions.assertThatIllegalArgumentException
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import kotlin.reflect.KClass

class ModelTest {
    private val id = ParcelId("PP-7781")

    private fun rejected(fields: Map<String, String>): String {
        val result = parseEvent(fields)
        assertThat(result).`as`("parseEvent($fields)").isInstanceOf(Parsed.Rejected::class.java)
        return (result as Parsed.Rejected).reason
    }

    // ---- value classes ----

    @Test
    fun `a parcel id is PP- followed by 4 to 12 digits`() {
        assertThat(ParcelId("PP-7781").value).isEqualTo("PP-7781")
        assertThat(ParcelId("PP-000123456789").value).isEqualTo("PP-000123456789")
        for (bad in listOf("7781", "PP-", "PP-77", "pp-7781", "PP-77A1", "PP-7781!", " PP-7781", "PP-" + "1".repeat(13))) {
            assertThatIllegalArgumentException().`as`("ParcelId(\"$bad\")")
                .isThrownBy { ParcelId(bad) }
                .withMessageContaining(bad)
        }
    }

    @Test
    fun `a weight is never negative`() {
        assertThat(Weight(0).grams).isZero()
        assertThatIllegalArgumentException().isThrownBy { Weight(-1) }.withMessageContaining("-1")
    }

    @Test
    fun `weights add and subtract exactly`() {
        assertThat(Weight(2_499) + Weight(1)).isEqualTo(Weight(2_500))
        assertThat(Weight(2_500) - Weight(500)).isEqualTo(Weight(2_000))
        assertThatIllegalArgumentException().`as`("5 kg - 5.001 kg").isThrownBy { Weight(5_000) - Weight(5_001) }
        assertThatThrownBy { Weight(Long.MAX_VALUE) + Weight(1) }.isInstanceOf(ArithmeticException::class.java)
    }

    @Test
    fun `a weight prints in kilograms`() {
        assertThat(Weight(2_500).toString()).isEqualTo("2.5 kg")
        assertThat(Weight(2_000).toString()).isEqualTo("2 kg")
        assertThat(Weight(5).toString()).isEqualTo("0.005 kg")
    }

    @Test
    fun `booked, collected and delivered weights must be positive`() {
        assertThatIllegalArgumentException().isThrownBy { ParcelBooked(id, Weight.ZERO) }
        assertThatIllegalArgumentException().isThrownBy { ParcelCollected(id, Weight.ZERO) }
        assertThatIllegalArgumentException().isThrownBy { ParcelDelivered(id, Weight.ZERO) }
        assertThat(ParcelCollected(id, Weight(1)).weight).isEqualTo(Weight(1))
    }

    // ---- the edge ----

    @Test
    fun `parse builds each event type from valid fields`() {
        assertThat(parseEvent(mapOf("type" to "booked", "parcelId" to "PP-7781", "grams" to "2500")))
            .isEqualTo(Parsed.Ok(ParcelBooked(id, Weight(2_500))))
        assertThat(parseEvent(mapOf("type" to "collected", "parcelId" to "PP-7781", "grams" to "2500")))
            .isEqualTo(Parsed.Ok(ParcelCollected(id, Weight(2_500))))
        assertThat(parseEvent(mapOf("type" to "delivered", "parcelId" to "PP-7781", "grams" to "2500")))
            .isEqualTo(Parsed.Ok(ParcelDelivered(id, Weight(2_500))))
        assertThat(parseEvent(mapOf("type" to "failed", "parcelId" to "PP-7781", "reason" to "NOBODY_HOME")))
            .isEqualTo(Parsed.Ok(DeliveryFailed(id, FailReason.NOBODY_HOME)))
    }

    @Test
    fun `parse names the field that is missing`() {
        assertThat(rejected(mapOf("parcelId" to "PP-7781", "grams" to "2500"))).contains("type")
        assertThat(rejected(mapOf("type" to "collected", "grams" to "2500"))).contains("parcelId")
        assertThat(rejected(mapOf("type" to "collected", "parcelId" to "PP-7781"))).contains("grams")
        assertThat(rejected(mapOf("type" to "failed", "parcelId" to "PP-7781"))).contains("reason")
    }

    @Test
    fun `parse rejects weights that are not whole numbers of grams`() {
        for (raw in listOf("2.5", "1e3", "", " 2500", "2,5", "99999999999999999999")) {
            assertThat(rejected(mapOf("type" to "collected", "parcelId" to "PP-7781", "grams" to raw)))
                .`as`("grams '$raw'").contains("grams")
        }
    }

    @Test
    fun `parse turns a constructor's refusal into Rejected`() {
        assertThat(rejected(mapOf("type" to "collected", "parcelId" to "7781", "grams" to "2500"))).contains("7781")
        assertThat(rejected(mapOf("type" to "delivered", "parcelId" to "PP-7781", "grams" to "-500"))).contains("-500")
        assertThat(rejected(mapOf("type" to "collected", "parcelId" to "PP-7781", "grams" to "0"))).contains("positive")
    }

    @Test
    fun `parse rejects unknown event types and fail reasons by name`() {
        assertThat(rejected(mapOf("type" to "lost", "parcelId" to "PP-7781", "grams" to "2500"))).contains("lost")
        assertThat(rejected(mapOf("type" to "failed", "parcelId" to "PP-7781", "reason" to "dog_in_garden"))).contains("dog_in_garden")
    }

    @Test
    fun `parse never throws, whatever arrives`() {
        val hostile = listOf(
            emptyMap(),
            mapOf("type" to ""),
            mapOf("type" to "COLLECTED", "parcelId" to "PP-7781", "grams" to "1"),
            mapOf("type" to "collected", "parcelId" to "", "grams" to ""),
            mapOf("type" to "failed", "parcelId" to "PP-7781", "reason" to "nobody_home"),
            mapOf("type" to "delivered", "parcelId" to "PP-7781", "grams" to "-9223372036854775808"),
            mapOf("type" to "booked", "parcelId" to "PP-\u0000\u0000\u0000\u0000", "grams" to "1"),
        )
        for (fields in hostile) {
            assertThatCode { assertThat(parseEvent(fields)).isInstanceOf(Parsed.Rejected::class.java) }
                .`as`("parseEvent($fields)").doesNotThrowAnyException()
        }
    }

    // ---- exhaustive operations ----

    private val samples: List<ParcelEvent> = listOf(
        ParcelBooked(id, Weight(2_500)),
        DeliveryFailed(id, FailReason.NOBODY_HOME),
        ParcelCollected(id, Weight(2_500)),
        ParcelDelivered(id, Weight(2_500)),
    )

    private fun leaves(type: KClass<*>): Set<KClass<*>> =
        if (type.isSealed) type.sealedSubclasses.flatMap(::leaves).toSet() else setOf(type)

    @Test
    fun `every event type has a summary line`() {
        // if this first check fails, someone added an event type: add a sample for it above
        assertThat(samples.map { it::class }.toSet()).isEqualTo(leaves(ParcelEvent::class))
        assertThat(samples.map(::summary)).containsExactly(
            "PP-7781 booked, 2.5 kg",
            "PP-7781 not delivered: NOBODY_HOME",
            "PP-7781 collected, 2.5 kg",
            "PP-7781 delivered, 2.5 kg",
        )
    }
}
