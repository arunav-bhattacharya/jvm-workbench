package workbench.kotlin.l06.demo

import kotlinx.serialization.SerialName
import kotlinx.serialization.SerializationException
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
sealed interface LedgerEvent {
    val paymentId: String
}

@Serializable
@SerialName("posted")
data class Posted(override val paymentId: String, val amountMinor: Long, val currency: String = "EUR") : LedgerEvent

@Serializable
@SerialName("reversed")
data class Reversed(override val paymentId: String, val reason: String? = null) : LedgerEvent

private val lenient = Json { ignoreUnknownKeys = true; explicitNulls = false }

fun main() {
    val events: List<LedgerEvent> = listOf(Posted("pay_1", 1_999), Reversed("pay_1"))
    val text = lenient.encodeToString(events)
    println(text)
    println("round trip equal: ${lenient.decodeFromString<List<LedgerEvent>>(text) == events}")

    val p = Posted("pay_2", 1)
    println("static type Posted:      ${Json.encodeToString(p)}")
    println("static type LedgerEvent: ${Json.encodeToString<LedgerEvent>(p)}")

    val newer = """{"type":"posted","paymentId":"pay_3","amountMinor":5,"acquirer":"acq-a"}"""
    println("lenient: ${lenient.decodeFromString<LedgerEvent>(newer)}")
    try {
        Json.decodeFromString<LedgerEvent>(newer)
    } catch (e: SerializationException) {
        println("default Json: ${e.message?.lineSequence()?.first()}")
    }
    println("generated serializer: ${Posted.serializer().javaClass.name}")
}
